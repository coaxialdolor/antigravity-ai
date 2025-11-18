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
/* General Dark Theme Overrides */
body, .gradio-container {
    background-color: #0d0d0d !important;
    color: #e0e0e0 !important;
}

/* Sidebar */
.sidebar {
    background-color: #171717 !important;
    border-right: 1px solid #333 !important;
    height: 100vh !important;
    padding: 20px !important;
}
.sidebar button {
    text-align: left !important;
    justify-content: flex-start !important;
    padding-left: 10px !important;
}
.header-text h2 {
    color: #fff !important;
    font-weight: 600 !important;
    margin-bottom: 20px !important;
}

/* Chatbot Area */
#chatbot {
    background-color: transparent !important;
    border: none !important;
    height: calc(100vh - 120px) !important;
    overflow-y: auto !important;
}
.message-row {
    margin-bottom: 20px !important;
}
/* User Message Bubble */
.message-row.user-row .message {
    background-color: #2f2f2f !important;
    border-radius: 18px !important;
    padding: 10px 20px !important;
    color: #fff !important;
    border: 1px solid #444 !important;
}
/* Bot Message - Minimal */
.message-row.bot-row .message {
    background-color: transparent !important;
    padding: 0 !important;
    color: #d0d0d0 !important;
    border: none !important;
}

/* Floating Input Bar */
.input-container-wrapper {
    position: absolute !important;
    bottom: 30px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 60% !important;
    max-width: 800px !important;
    z-index: 100 !important;
}

.input-pill {
    background-color: #1e1e1e !important;
    border-radius: 28px !important;
    border: 1px solid #333 !important;
    padding: 6px 12px !important;
    display: flex !important;
    align-items: center !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    gap: 8px !important;
}
.input-pill:focus-within {
    border-color: #555 !important;
}

/* Transparent Textarea */
.transparent-input textarea {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #fff !important;
    padding: 8px 0 !important;
    font-size: 1rem !important;
    resize: none !important;
}
.transparent-input .wrap {
    background: transparent !important;
    border: none !important;
}

/* Circular Buttons */
.circle-btn {
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    border-radius: 50% !important;
    background: transparent !important;
    border: none !important;
    color: #888 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
    font-size: 1.2em !important;
    box-shadow: none !important;
}
.circle-btn:hover {
    background-color: #333 !important;
    color: #fff !important;
}

.send-btn-circle {
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    border-radius: 50% !important;
    background: #fff !important;
    color: #000 !important;
    border: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
    box-shadow: none !important;
}
.send-btn-circle:hover {
    background: #e0e0e0 !important;
}

/* Audio Button Hack */
.audio-btn {
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    border-radius: 50% !important;
    background: transparent !important;
    border: none !important;
    overflow: hidden !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.audio-btn .wrap {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    width: 100% !important;
    height: 100% !important;
}
.audio-btn audio { display: none !important; }

/* History List */
.history-item {
    padding: 8px 12px !important;
    border-radius: 8px !important;
    color: #aaa !important;
    cursor: pointer !important;
    margin-bottom: 4px !important;
    font-size: 0.9em !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.history-item:hover {
    background-color: #222 !important;
    color: #fff !important;
}
"""

theme = gr.themes.Base(
    primary_hue="zinc",
    secondary_hue="stone",
    neutral_hue="neutral",
    radius_size=gr.themes.sizes.radius_sm,
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
).set(
    body_background_fill="#0d0d0d",
    body_text_color="#e0e0e0",
    block_background_fill="#171717",
    block_border_width="0px",
    input_background_fill="#1e1e1e",
    button_primary_background_fill="#ffffff",
    button_primary_text_color="#000000"
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
        yield history, None, gr.update()
        return

    # 1. Check for Image Generation Request
    lower_msg = message.lower()
    if "generate image" in lower_msg or "draw " in lower_msg or "create an image" in lower_msg:
        # Image Mode
        history = history + [[message, "🎨 Generating image..."]]
        yield history, None, gr.update()
        
        prompt = message
        img, status = image_engine.generate(prompt)
        
        if img:
            img_path = os.path.join(models_root, "image", f"gen_{len(history)}.png")
            img.save(img_path)
            history[-1][1] = (img_path, "Generated Image")
        else:
            history[-1][1] = f"❌ Image generation failed: {status}"
            
        yield history, None, gr.update()
        
        if session_id:
             session_manager.update_session(session_id, history)
        return

    # 2. Text Chat with Streaming
    history = history + [[message, ""]]
    yield history, None, gr.update()
    
    system_prompt = PERSONALITIES.get(personality, "")
    
    # Generator for streaming
    response_generator = text_engine.generate(message, history[:-1], system_prompt, stream=True)
    
    full_response = ""
    for chunk in response_generator:
        full_response += chunk
        history[-1][1] = full_response
        yield history, None, gr.update()
    
    # 3. Save session
    if session_id:
        current_session = session_manager.get_session(session_id)
        title = current_session.get("title", "New Chat")
        
        if len(history) == 1: # First turn
            try:
                title_prompt = f"Summarize this conversation in 3-5 words for a title. User: {message}\nAI: {full_response}"
                # Non-streaming for title
                title = text_engine.generate(title_prompt, [], "You are a title generator. Output ONLY the title.", stream=False)
                title = title.strip().replace('"', '')
            except:
                title = message[:30] + "..."
        
        session_manager.update_session(session_id, history, title)
            
    # 4. Voice (Post-generation)
    audio = None
    if voice_enabled:
        ve = VoiceEngine()
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        audio = loop.run_until_complete(ve.text_to_speech(full_response, voice_id))
        
    yield history, audio, gr.update(choices=refresh_session_list())

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
    
    new_list = refresh_session_list()
    return gr.update(choices=new_list, value=None), None, []

def add_path(p):
    text_engine.custom_dirs.append(Path(p))
    return gr.update(choices=get_available_models())

# --- UI ---

with gr.Blocks(theme=theme, css=css, title="Antigravity AI") as demo:
    session_id = gr.State(None)
    
    with gr.Row(equal_height=True, variant="default"):
        # --- Sidebar ---
        with gr.Column(scale=1, min_width=280, elem_classes=["sidebar"]):
            gr.Markdown("## ⚡ Antigravity", elem_classes=["header-text"])
            new_chat_btn = gr.Button("+ New Chat", variant="primary", size="sm")
            
            gr.Markdown("#### Chats", elem_id="history-label")
            history_list = gr.Radio(choices=refresh_session_list(), label="", interactive=True, container=False, elem_classes=["history-list"])
            
            with gr.Accordion("⚙️ Settings", open=False):
                model_selector = gr.Dropdown(choices=get_available_models(), label="Model", interactive=True)
                personality_selector = gr.Dropdown(choices=list(PERSONALITIES.keys()), value="Helpful Assistant", label="Personality")
                voice_chk = gr.Checkbox(label="Voice Response")
                voice_sel = gr.Dropdown(choices=get_voice_list(), value="en-US-AriaNeural", label="Voice")
                delete_chat_btn = gr.Button("🗑️ Delete Chat", size="sm", variant="secondary")
            
            with gr.Accordion("Custom Paths", open=False):
                path_input = gr.Textbox(label="Add Path")
                add_path_btn = gr.Button("Add")

        # --- Main Chat ---
        with gr.Column(scale=5, elem_id="main-area"):
            # Header
            with gr.Row():
                 status_display = gr.Markdown("", elem_id="status")

            # Chatbot
            chatbot = gr.Chatbot(
                height=700,
                bubble_full_width=False,
                show_copy_button=True,
                avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=KD"),
                elem_id="chatbot",
                type="messages" # Use new messages format if available, else default
            )
            
            # Floating Input Pill
            with gr.Group(elem_classes=["input-container-wrapper"]):
                with gr.Row(elem_classes=["input-pill"]):
                    # Left Tools
                    upload_btn = gr.UploadButton("＋", file_types=["image", "text", "audio"], elem_classes=["circle-btn"])
                    live_btn = gr.Button("❖", elem_classes=["circle-btn"]) # Grid icon approx
                    
                    # Input
                    msg_input = gr.Textbox(
                        placeholder="Send a Message", 
                        show_label=False,
                        container=False,
                        autofocus=True,
                        lines=1,
                        max_lines=5,
                        scale=1,
                        elem_classes=["transparent-input"]
                    )
                    
                    # Right Tools
                    mic_btn = gr.Audio(sources=["microphone"], type="filepath", show_label=False, container=False, elem_classes=["audio-btn", "circle-btn"])
                    send_btn = gr.Button("➤", elem_classes=["send-btn-circle"])
            
            audio_out = gr.Audio(visible=False, autoplay=True)

    # --- Wiring ---
    
    # Init
    def on_load():
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
    mic_btn.stop_recording(transcribe_audio, inputs=[mic_btn], outputs=[msg_input])

if __name__ == "__main__":
    demo.queue().launch(inbrowser=True)
