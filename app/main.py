import gradio as gr
import os
import sys
from pathlib import Path

# Add parent dir
sys.path.append(str(Path(__file__).parent.parent))

from app.backend.config_manager import ConfigManager
from app.backend.hardware import get_device_info
from app.backend.text_engine import TextEngine
from app.backend.voice_engine import VoiceEngine
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

# --- CSS (Claude Style - Aligned) ---
css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

/* RESET */
body, .gradio-container {
    background-color: #1e1e1e !important;
    color: #e0e0e0 !important;
    font-family: 'Inter', sans-serif !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* LAYOUT */
.main-layout {
    display: flex !important;
    height: 100vh !important;
    overflow: hidden !important;
}

/* SIDEBAR */
.sidebar {
    background-color: #171717 !important;
    border-right: 1px solid #333 !important;
    width: 260px !important;
    min-width: 260px !important;
    display: flex !important;
    flex-direction: column !important;
    padding: 16px !important;
    gap: 16px !important;
}

.sidebar-btn {
    background-color: #2a2a2a !important;
    color: #fff !important;
    border: 1px solid #444 !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    text-align: center !important;
    cursor: pointer !important;
    transition: background 0.2s !important;
}
.sidebar-btn:hover { background-color: #333 !important; }

.history-list {
    flex-grow: 1 !important;
    overflow-y: auto !important;
}
.history-list label {
    background: transparent !important;
    border: none !important;
    padding: 8px !important;
    color: #aaa !important;
    cursor: pointer !important;
    display: block !important;
    border-radius: 6px !important;
    margin-bottom: 4px !important;
}
.history-list label:hover { background-color: #2a2a2a !important; color: #fff !important; }
.history-list input { display: none !important; }

/* CHAT AREA */
.chat-area {
    flex-grow: 1 !important;
    position: relative !important;
    display: flex !important;
    flex-direction: column !important;
    background-color: #1e1e1e !important;
    align-items: center !important; /* Center content */
}

#chatbot {
    width: 100% !important;
    max-width: 900px !important; /* Fixed width for alignment */
    flex-grow: 1 !important;
    overflow-y: auto !important;
    padding-bottom: 150px !important;
    background: transparent !important;
}

/* Message Bubbles */
.message-row {
    padding: 12px 0 !important;
    width: 100% !important;
}

.message-row.user-row .message {
    background-color: #3a3a3a !important;
    color: #fff !important;
    border-radius: 12px !important;
    padding: 12px 18px !important;
    border: none !important;
    max-width: 80% !important;
}
.message-row.bot-row .message {
    background: transparent !important;
    color: #e0e0e0 !important;
    padding: 0 !important;
    border: none !important;
    max-width: 100% !important;
}

/* INPUT CONTAINER (Aligned) */
.input-container-wrapper {
    position: absolute !important;
    bottom: 30px !important;
    width: 100% !important;
    max-width: 900px !important; /* Matches Chatbot Width */
    z-index: 100 !important;
    padding: 0 20px !important; /* Safety padding on small screens */
}

.input-box {
    background-color: #2a2a2a !important;
    border: 1px solid #444 !important;
    border-radius: 16px !important;
    padding: 12px !important;
    display: flex !important;
    flex-direction: column !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
}
.input-box:focus-within { border-color: #666 !important; }

/* Textarea */
.input-textarea textarea {
    background: transparent !important;
    border: none !important;
    color: #fff !important;
    padding: 0 !important;
    font-size: 1rem !important;
    resize: none !important;
    box-shadow: none !important;
    min-height: 44px !important;
}
.input-textarea .wrap { background: transparent !important; border: none !important; }

/* Toolbar */
.input-toolbar {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-top: 8px !important;
    padding-top: 8px !important;
    border-top: 1px solid #3a3a3a !important;
}

.tool-group {
    display: flex !important;
    gap: 8px !important;
    align-items: center !important;
}

.tool-btn {
    background: transparent !important;
    border: none !important;
    color: #aaa !important;
    padding: 0 !important;
    border-radius: 4px !important;
    cursor: pointer !important;
    width: 36px !important;
    height: 36px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 1.2rem !important;
}
.tool-btn:hover { background-color: #3a3a3a !important; color: #fff !important; }

.send-btn {
    background-color: #d97757 !important;
    color: #fff !important;
    border-radius: 6px !important;
    font-size: 0.9rem !important;
    padding: 8px 16px !important;
    width: auto !important;
    font-weight: 600 !important;
    border: none !important;
}
.send-btn:hover { background-color: #e08868 !important; }

.hidden-audio { display: none !important; }
"""

theme = gr.themes.Base(
    primary_hue="zinc",
    secondary_hue="zinc",
    neutral_hue="zinc",
    font=[gr.themes.GoogleFont("Inter"), "sans-serif"]
).set(
    body_background_fill="#1e1e1e",
    body_text_color="#e0e0e0",
    block_background_fill="#1e1e1e",
    block_border_width="0px"
)

PERSONALITIES = {
    "Helpful Assistant": "You are a helpful, polite, and accurate AI assistant.",
    "Code Wizard": "You are an expert software engineer.",
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
            if vram < 6 and not is_small: continue
            recommendations.append(f"⬇️ {name}")
    return installed + recommendations

def get_voice_list(): return VoiceEngine().get_available_voices()

def handle_model_change(model_selection):
    if not model_selection or not isinstance(model_selection, str): return gr.update(), "Invalid"
    if model_selection.startswith("⬇️"):
        model_name = model_selection.replace("⬇️ ", "").strip()
        url = next((m["url"] for m in DOWNLOADABLE_MODELS if m["name"] == model_name), None)
        if url:
            gr.Info(f"Downloading {model_name}...")
            try:
                download_file(url, Path(models_root)/"llm"/model_name)
                return gr.update(choices=get_available_models(), value=model_name), f"Loaded {model_name}"
            except Exception as e: return gr.update(), f"Error: {e}"
    return gr.update(), text_engine.load_model(model_selection)

def transcribe_audio(audio_path): return stt_engine.transcribe(audio_path) if audio_path else ""

def chat_turn(message, history, session_id, personality, voice_enabled, voice_id):
    if not message.strip(): yield history, None, gr.update(); return
    
    # Image Gen
    if any(x in message.lower() for x in ["generate image", "draw ", "create an image"]):
        history = history + [[message, "🎨 Generating..."]]
        yield history, None, gr.update()
        img, status = image_engine.generate(message)
        if img:
            p = os.path.join(models_root, "image", f"gen_{len(history)}.png")
            img.save(p)
            history[-1][1] = (p, "Generated Image")
        else: history[-1][1] = f"❌ {status}"
        yield history, None, gr.update()
        if session_id: session_manager.update_session(session_id, history)
        return

    # Text Gen
    history = history + [[message, ""]]
    yield history, None, gr.update()
    
    gen = text_engine.generate(message, history[:-1], PERSONALITIES.get(personality, ""), stream=True)
    full_resp = ""
    for chunk in gen:
        full_resp += chunk
        history[-1][1] = full_resp
        yield history, None, gr.update()
        
    if session_id:
        sess = session_manager.get_session(session_id)
        title = sess.get("title", "New Chat")
        if len(history) == 1:
            try: title = text_engine.generate(f"Title for: {message}", [], "Title gen", stream=False).strip('"')[:30]
            except: title = message[:20]
        session_manager.update_session(session_id, history, title)
        
    audio = None
    if voice_enabled:
        try: loop = asyncio.get_event_loop()
        except: loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
        audio = loop.run_until_complete(VoiceEngine().text_to_speech(full_resp, voice_id))
        
    yield history, audio, gr.update(choices=refresh_session_list())

def create_new_session(): sid, _ = session_manager.create_session(); return sid, [], gr.update(choices=refresh_session_list())
def load_session(evt: gr.SelectData): 
    if not evt.value: return None, []
    sid = evt.value.split(" | ")[-1]
    data = session_manager.get_session(sid)
    return sid, data["history"] if data else []
def refresh_session_list(): return [f"{s['title']} | {s['id']}" for s in session_manager.list_sessions()]
def delete_current_session(sel): 
    if sel: session_manager.delete_session(sel.split(" | ")[-1])
    return gr.update(choices=refresh_session_list(), value=None), None, []
def add_path(p): text_engine.custom_dirs.append(Path(p)); return gr.update(choices=get_available_models())

# --- UI ---
with gr.Blocks(theme=theme, css=css, title="Antigravity") as demo:
    session_id = gr.State(None)
    
    with gr.Row(elem_classes=["main-layout"]):
        # Sidebar
        with gr.Column(elem_classes=["sidebar"], scale=0):
            gr.Markdown("### Antigravity")
            new_chat_btn = gr.Button("+ New Chat", elem_classes=["sidebar-btn"])
            
            gr.Markdown("#### History")
            history_list = gr.Radio(choices=[], label="", interactive=True, container=False, elem_classes=["history-list"])
            
            with gr.Accordion("Settings", open=False):
                model_selector = gr.Dropdown(choices=get_available_models(), label="Model")
                personality_selector = gr.Dropdown(choices=list(PERSONALITIES.keys()), value="Helpful Assistant", label="Personality")
                voice_chk = gr.Checkbox(label="Voice")
                voice_sel = gr.Dropdown(choices=get_voice_list(), value="en-US-AriaNeural", label="Voice")
                delete_chat_btn = gr.Button("Delete Chat")
                path_input = gr.Textbox(label="Path")
                add_path_btn = gr.Button("Add")

        # Chat Area
        with gr.Column(elem_classes=["chat-area"]):
            chatbot = gr.Chatbot(elem_id="chatbot", bubble_full_width=False, show_copy_button=True, type="messages")
            
            # Input Box (Claude Style)
            with gr.Group(elem_classes=["input-container-wrapper"]):
                with gr.Column(elem_classes=["input-box"]):
                    msg_input = gr.Textbox(
                        placeholder="Message...",
                        show_label=False,
                        container=False,
                        lines=1,
                        max_lines=10,
                        elem_classes=["input-textarea"],
                        autofocus=True
                    )
                    
                    with gr.Row(elem_classes=["input-toolbar"]):
                        with gr.Row(elem_classes=["tool-group"]):
                            upload_btn = gr.UploadButton("📎", file_types=["image"], elem_classes=["tool-btn"])
                            mic_btn = gr.Audio(sources=["microphone"], type="filepath", show_label=False, container=False, elem_classes=["tool-btn"])
                        
                        send_btn = gr.Button("Send", elem_classes=["send-btn"])

            status_display = gr.Markdown("", visible=False)
            audio_out = gr.Audio(visible=False, autoplay=True, elem_classes=["hidden-audio"])

    # Wiring
    def on_load():
        session_manager.cleanup_empty_sessions()
        sid, _ = session_manager.create_session()
        models = get_available_models()
        def_model = next((m for m in models if "⬇️" not in m and any(x in m for x in ["1B", "3B", "Phi"])), None)
        if not def_model: def_model = next((m for m in models if "⬇️" not in m), None)
        status = text_engine.load_model(def_model) if def_model else "No model"
        return sid, refresh_session_list(), models, def_model, status

    demo.load(on_load, None, [session_id, history_list, model_selector, model_selector, status_display])
    new_chat_btn.click(create_new_session, None, [session_id, chatbot, history_list])
    history_list.select(load_session, None, [session_id, chatbot])
    delete_chat_btn.click(delete_current_session, history_list, [history_list, session_id, chatbot])
    model_selector.change(handle_model_change, model_selector, [model_selector, status_display])
    add_path_btn.click(add_path, path_input, model_selector)
    
    chat_args = [msg_input, chatbot, session_id, personality_selector, voice_chk, voice_sel]
    msg_input.submit(chat_turn, chat_args, [chatbot, audio_out, history_list]).then(lambda: "", None, msg_input)
    send_btn.click(chat_turn, chat_args, [chatbot, audio_out, history_list]).then(lambda: "", None, msg_input)
    mic_btn.stop_recording(transcribe_audio, mic_btn, msg_input)

if __name__ == "__main__":
    demo.queue().launch(inbrowser=True)
