"""
FastAPI server for the multimodal chat frontend
"""
import os
import sys
import uuid
import base64
import tempfile
from pathlib import Path
from typing import Optional, List
import asyncio

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent dir
sys.path.append(str(Path(__file__).parent.parent))

from app.backend.config_manager import ConfigManager
from app.backend.text_engine import TextEngine
from app.backend.image_engine import ImageEngine
from app.backend.stt_engine import STTEngine
from app.backend.voice_engine import VoiceEngine
from app.backend.session_manager import SessionManager

# Initialize engines
config = ConfigManager()
models_root = config.get_nested(["paths", "models_root"], "models")
custom_paths = config.get("custom_model_paths", [])

text_engine = TextEngine(os.path.join(models_root, "llm"), custom_paths)
image_engine = ImageEngine(os.path.join(models_root, "image"))
stt_engine = STTEngine(os.path.join(models_root, "stt"))
voice_engine = VoiceEngine(os.path.join(models_root, "voice"))
session_manager = SessionManager()

PERSONALITIES = {
    "helpful": "You are a helpful, polite, and accurate AI assistant.",
    "friendly": "You are a friendly and warm AI assistant.",
    "technical": "You are an expert software engineer.",
    "humorous": "You are a humorous and entertaining AI assistant.",
    "socratic": "You are a Socratic teacher who asks thoughtful questions."
}

app = FastAPI(title="Antigravity API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend path
frontend_path = Path(__file__).parent.parent / "frontend"

# Request/Response models
class ChatRequest(BaseModel):
    text: str
    files: Optional[List[dict]] = []
    model: Optional[str] = None
    voice: Optional[str] = None
    personality: Optional[str] = "helpful"
    session_id: Optional[str] = None

class ImageGenRequest(BaseModel):
    prompt: str
    size: Optional[str] = "768x768"
    style: Optional[str] = "photorealistic"
    model: Optional[str] = None

class TranscribeRequest(BaseModel):
    model: Optional[str] = None

# API Routes


@app.get("/api/models")
async def get_models():
    """Get list of available models"""
    return {"models": text_engine.list_models()}

@app.get("/api/voices")
async def get_voices():
    """Get list of available voices"""
    return {"voices": voice_engine.get_available_voices()}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Handle chat messages"""
    try:
        # Get or create session
        session_id = request.session_id
        if not session_id:
            session_id, _ = session_manager.create_session()
        
        session = session_manager.get_session(session_id)
        if not session:
            session_id, session = session_manager.create_session()
        
        history = session.get("history", [])
        
        # Convert history format if needed
        if history and isinstance(history[0], list):
            # Old format: [[user_msg, bot_msg], ...]
            history = []
        
        # Handle image generation request
        if any(x in request.text.lower() for x in ["generate image", "draw ", "create an image"]):
            img, status = image_engine.generate(request.text)
            if img:
                # Save image temporarily
                temp_path = tempfile.mktemp(suffix=".png")
                img.save(temp_path)
                
                # Read and encode
                with open(temp_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode()
                
                os.unlink(temp_path)
                
                return {
                    "markdown": f"![Generated Image](data:image/png;base64,{img_data})",
                    "session_id": session_id
                }
            else:
                return {
                    "markdown": f"❌ Image generation failed: {status}",
                    "session_id": session_id
                }
        
        # Get personality prompt
        system_prompt = PERSONALITIES.get(request.personality, PERSONALITIES["helpful"])
        
        # Generate response
        gen = text_engine.generate(
            request.text,
            history,
            system_prompt,
            stream=False
        )
        
        response_text = gen if isinstance(gen, str) else "".join(gen)
        
        # Update session
        new_history = history + [[request.text, response_text]]
        session_manager.update_session(session_id, new_history)
        
        return {
            "markdown": response_text,
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/image")
async def generate_image(request: ImageGenRequest):
    """Generate an image from a prompt"""
    try:
        img, status = image_engine.generate(request.prompt)
        if img:
            # Save to temp file
            temp_path = tempfile.mktemp(suffix=".png")
            img.save(temp_path)
            
            return FileResponse(
                temp_path,
                media_type="image/png",
                filename=f"generated-{uuid.uuid4().hex[:8]}.png"
            )
        else:
            raise HTTPException(status_code=500, detail=f"Image generation failed: {status}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio file"""
    try:
        # Save uploaded file temporarily
        temp_path = tempfile.mktemp(suffix=".webm")
        with open(temp_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Transcribe
        text = stt_engine.transcribe(temp_path)
        
        # Cleanup
        os.unlink(temp_path)
        
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session")
async def create_session():
    """Create a new session"""
    session_id, session = session_manager.create_session()
    return {"session_id": session_id}

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session data"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    session_manager.delete_session(session_id)
    return {"status": "deleted"}

@app.get("/api/sessions")
async def list_sessions():
    """List all sessions"""
    return {"sessions": session_manager.list_sessions()}

# Serve frontend files (must be last)
if frontend_path.exists():
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        """Serve frontend files"""
        # Skip API routes
        if path.startswith("api/"):
            raise HTTPException(status_code=404)
        
        file_path = frontend_path / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        
        # Default to index.html for SPA routing
        index_path = frontend_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        
        raise HTTPException(status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

