import gradio as gr
import os
import sys
import threading
from pathlib import Path

# Add parent dir
sys.path.append(str(Path(__file__).parent.parent))

from app.backend.config_manager import ConfigManager
from app.backend.hardware import get_device_info
from app.backend.text_engine import TextEngine
from app.backend.voice_engine import VoiceEngine, tts_sync
from app.backend.image_engine import ImageEngine
from app.backend.stt_engine import STTEngine
from app.backend.session_manager import SessionManager
import asyncio
from download_models import MODELS as DOWNLOADABLE_MODELS, download_file

# --- Initialization ---
config = ConfigManager()
models_root = config.get_nested(["paths", "models_root"], "models")
custom_paths = config.get("custom_model_paths", [])

text_engine = TextEngine(os.path.join(models_root, "llm"), custom_paths)
image_engine = ImageEngine(os.path.join(models_root, "image"))
stt_engine = STTEngine(os.path.join(models_root, "stt"))
session_manager = SessionManager()

# --- Constants & Theme ---
css = """
.history-container {
    max-height: 200px;
    overflow-y: auto;
}
.history-container .wrap {
    display: block !important;
}
.history-container label {
    font-size: 0.8em !important;
    padding: 4px 8px !important;
    margin-bottom: 2px !important;
    border-radius: 4px !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.icon-btn {
    min-width: 40px !important;
    width: 40px !important;
    height: 40px !important;
    padding: 0 !important;
    background: transparent !important;
    border: 1px solid #444 !important;
    color: #ccc !important;
}
.icon-btn:hover {
    background: #333 !important;
}
.input-row {
    align-items: flex-end;
}
"""

theme = gr.themes.Base(
    primary_hue="zinc",
    secondary_hue="stone",
    neutral_hue="neutral",
    radius_size=gr.themes.sizes.radius_sm,
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
).set(
    body_background_fill="*neutral_950",
    body_text_color="*neutral_50",
    block_background_fill="*neutral_900",
    block_border_width="1px",
    block_border_color="*neutral_800",
    input_background_fill="*neutral_800",
    button_primary_background_fill="*neutral_200",
    button_primary_text_color="*neutral_950"
)

PERSONALITIES = {
    "Helpful Assistant": "You are a helpful, polite, and accurate AI assistant.",
    "Code Wizard": "You are an expert software engineer. You provide concise, high-quality code snippets.",
    "Storyteller": "You are a creative storyteller.",
    "Sarcastic": "You are a sarcastic robot."
}

# --- Logic ---

def get_available_models():
    installed = text_engine.list_models()
    hw = get_device_info()
    vram = hw.get("vram", 0)
    
    recommendations = []
    for m in DOWNLOADABLE_MODELS:
        name = m["name"]
        if name not in installed:
            is_small = "1B" in name or "3B" in name or "Phi-3" in name
            if vram < 6 and not is_small:
                continue
            recommendations.append(f"⬇️ Download: {name}")
            
    return installed + recommendations

def get_voice_list():
    # Instantiate temp engine to get list
    ve = VoiceEngine() # This is fast
    return ve.get_available_voices()

def handle_model_change(model_selection):
    if not model_selection or not isinstance(model_selection, str):
        return gr.update(), "Invalid selection"

    if model_selection.startswith("⬇️ Download:"):
        model_name = model_selection.replace("⬇️ Download: ", "").strip()
        url = next((m["url"] for m in DOWNLOADABLE_MODELS if m["name"] == model_name), None)
        if url:
            gr.Info(f"Downloading {model_name}...")
            dest = Path(models_root) / "llm" / model_name
            try:
                download_file(url, dest)
                gr.Info(f"Downloaded {model_name}!")
                return gr.update(choices=get_available_models(), value=model_name), f"Loaded {model_name}"
            except Exception as e:
                gr.Warning(f"Download failed: {e}")
                return gr.update(), f"Error: {e}"
    
    msg = text_engine.load_model(model_selection)
    return gr.update(), msg

def transcribe_audio(audio_path):
    if not audio_path: return ""
    text = stt_engine.transcribe(audio_path)
    return text

def chat_turn(message, history, session_id, personality, voice_enabled, voice_id, image_mode_trigger=False):
    if not message.strip() and not image_mode_trigger:
        return history, None, gr.update()

    # 1. Check for Image Generation Request
    # Simple heuristic: if "generate image" or "draw" is in the message
    lower_msg = message.lower()
    if "generate image" in lower_msg or "draw " in lower_msg or "create an image" in lower_msg:
        # Image Mode
        history = history + [[message, "🎨 Generating image..."]]
        yield history, None, gr.update()
        
        # Extract prompt (naive)
        prompt = message
        img, status = image_engine.generate(prompt)
        
        if img:
            img_path = os.path.join(models_root, "image", f"gen_{len(history)}.png")
            img.save(img_path)
            # Replace the "Generating..." message with the image
            history[-1][1] = (img_path, "Generated Image")
        else:
            history[-1][1] = f"❌ Image generation failed: {status}"
            
        yield history, None, gr.update()
        
        # Save session
        if session_id:
             session_manager.update_session(session_id, history)
        return

    # 2. Text Chat
    new_history = history + [[message, None]]
    
    # 2. Generate
    system_prompt = PERSONALITIES.get(personality, "")
    response = text_engine.generate(message, history, system_prompt)
    
    new_history[-1][1] = response
    
    # 3. Save session
    if session_id:
        # Auto-title if new or untitled
        current_session = session_manager.get_session(session_id)
        title = current_session.get("title", "New Chat")
        
        if len(history) == 0: # First turn
            # Generate title
            try:
                title_prompt = f"Summarize this conversation in 3-5 words for a title. User: {message}\nAI: {response}"
                title = text_engine.generate(title_prompt, [], "You are a title generator. Output ONLY the title.")
                title = title.strip().replace('"', '')
            except:
                title = message[:30] + "..."
        
        session_manager.update_session(session_id, new_history, title)
            
    # 4. Voice
    audio = None
    if voice_enabled:
        # Use the new VoiceEngine
        ve = VoiceEngine()
        # Run async in sync
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        audio = loop.run_until_complete(ve.text_to_speech(response, voice_id))
        
    yield new_history, audio, gr.update(choices=refresh_session_list())

def create_new_session():
    sid, _ = session_manager.create_session()
    return sid, [], gr.update(choices=refresh_session_list())

def load_session(evt: gr.SelectData):
    selected = evt.value
    if not selected: return None, []
    sid = selected.split(" | ")[-1]
    data = session_manager.get_session(sid)
    if data:
        return sid, data["history"]
    return None, []

def refresh_session_list():
    sessions = session_manager.list_sessions()
    return [f"{s['title']} | {s['id']}" for s in sessions]

def delete_current_session(selected_str):
    if not selected_str: return gr.update()
    
    sid = selected_str.split(" | ")[-1]
    session_manager.delete_session(sid)
    
    # Refresh list and clear selection
    new_list = refresh_session_list()
    return gr.update(choices=new_list, value=None), None, [] # Reset chat

def add_path(p):
    text_engine.custom_dirs.append(Path(p))
    return gr.update(choices=get_available_models())

# --- UI ---

with gr.Blocks(theme=theme, title="Antigravity AI") as demo:
    # State
    session_id = gr.State(None)
    
    with gr.Row(equal_height=True):
        gr.Markdown("## ⚡ Antigravity AI", elem_classes=["header-text"])
        status_display = gr.Markdown("", elem_id="status")

    with gr.Row():
        # --- Sidebar (History & Settings) ---
        with gr.Column(scale=1, min_width=250, variant="panel"):
            new_chat_btn = gr.Button("+ New Chat", variant="primary")
            
            gr.Markdown("### 🕒 History")
            # Using Radio as a vertical list of chats
            history_list = gr.Radio(choices=refresh_session_list(), label="Recent Chats", interactive=True, container=False)
            delete_chat_btn = gr.Button("🗑️ Delete Selected", size="sm", variant="secondary")
            
            gr.Markdown("### ⚙️ Controls")
            model_selector = gr.Dropdown(choices=get_available_models(), label="Model", interactive=True)
            personality_selector = gr.Dropdown(choices=list(PERSONALITIES.keys()), value="Helpful Assistant", label="Personality")
            
            with gr.Accordion("Voice & Audio", open=False):
                voice_chk = gr.Checkbox(label="Voice Response")
                voice_sel = gr.Dropdown(choices=get_voice_list(), value="en-US-AriaNeural", label="Voice")
            
            with gr.Accordion("Custom Paths", open=False):
                path_input = gr.Textbox(label="Add Path")
                add_path_btn = gr.Button("Add")

        # --- Main Chat ---
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(
                height=650, 
                bubble_full_width=False,
                show_copy_button=True,
                avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=KD")
            )
            
            with gr.Row():
                with gr.Column(scale=4):
                    msg_input = gr.Textbox(
                        placeholder="Type a message or 'generate image of...'...", 
                        show_label=False,
                        container=False,
                        autofocus=True,
                        lines=3
                    )
                with gr.Column(scale=1, min_width=100):
                    send_btn = gr.Button("➤ Send", variant="primary", size="lg")
            
            with gr.Row():
                mic_btn = gr.Audio(sources=["microphone"], type="filepath", label="Voice Input", show_label=False, scale=1)
                upload_btn = gr.UploadButton("📁 Upload File", file_types=["image", "text", "audio"], scale=1)
                live_voice_btn = gr.Button("🎙️ Live Voice (Toggle)", variant="secondary", scale=1) # Placeholder for now
            
            audio_out = gr.Audio(visible=False, autoplay=True)

    # --- Wiring ---
    
    # Init
    def on_load():
        # Cleanup empty
        session_manager.cleanup_empty_sessions()
        sid, _ = session_manager.create_session()
        return sid, refresh_session_list(), get_available_models()
        
    demo.load(on_load, None, [session_id, history_list, model_selector])

    # New Chat
    new_chat_btn.click(create_new_session, None, [session_id, chatbot, history_list])

    # Load Chat
    history_list.select(load_session, None, [session_id, chatbot])
    
    # Delete Chat
    delete_chat_btn.click(delete_current_session, history_list, [history_list, session_id, chatbot])

    # Model Change
    model_selector.change(handle_model_change, model_selector, [model_selector, status_display])

    # Custom Path
    add_path_btn.click(add_path, path_input, model_selector)

    # Chat Flow
    chat_inputs = [msg_input, chatbot, session_id, personality_selector, voice_chk, voice_sel]
    chat_outputs = [chatbot, audio_out, history_list]
    
    msg_input.submit(chat_turn, chat_inputs, chat_outputs).then(lambda: "", None, msg_input)
    send_btn.click(chat_turn, chat_inputs, chat_outputs).then(lambda: "", None, msg_input)

    # Voice Input Flow
    # When audio is recorded/stopped, transcribe it and put it in msg_input
    mic_btn.stop_recording(transcribe_audio, inputs=[mic_btn], outputs=[msg_input])
    # Optional: Auto-submit after transcription?
    # mic_btn.stop_recording(transcribe_audio, inputs=[mic_btn], outputs=[msg_input]).then(chat_turn, chat_inputs, chat_outputs)

if __name__ == "__main__":
    demo.queue().launch(inbrowser=True)
