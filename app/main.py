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

# --- CSS (Claude Style) ---
css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
    box-sizing: border-box;
}

body, .gradio-container {
    background-color: #0f0f0f !important;
    color: #e0e0e0 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}

/* Main Layout */
.main-layout {
    display: flex !important;
    height: 100vh !important;
    width: 100vw !important;
    overflow: hidden !important;
}

/* Sidebar */
.sidebar {
    background-color: #171717 !important;
    width: 260px !important;
    min-width: 260px !important;
    max-width: 260px !important;
    display: flex !important;
    flex-direction: column !important;
    border-right: 1px solid #2a2a2a !important;
    height: 100vh !important;
    overflow: hidden !important;
}

.sidebar-header {
    padding: 16px 20px !important;
    border-bottom: 1px solid #2a2a2a !important;
}

.sidebar-brand {
    font-size: 18px !important;
    font-weight: 600 !important;
    color: #fff !important;
    margin: 0 !important;
    letter-spacing: -0.3px !important;
}

.new-chat-btn {
    margin: 12px 16px !important;
    background-color: #fff !important;
    color: #0f0f0f !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 16px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: background-color 0.2s !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    width: calc(100% - 32px) !important;
}

.new-chat-btn:hover {
    background-color: #e8e8e8 !important;
}

.new-chat-btn::before {
    content: "+" !important;
    font-size: 18px !important;
    font-weight: 300 !important;
}

.sidebar-nav {
    padding: 8px 0 !important;
    border-bottom: 1px solid #2a2a2a !important;
}

.nav-item {
    padding: 8px 20px !important;
    color: #a0a0a0 !important;
    font-size: 14px !important;
    cursor: pointer !important;
    transition: color 0.2s !important;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
}

.nav-item:hover {
    color: #fff !important;
    background-color: #1f1f1f !important;
}

.history-section {
    flex: 1 !important;
    overflow-y: auto !important;
    padding: 12px 0 !important;
}

.history-section-label {
    padding: 8px 20px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #707070 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

.history-list {
    margin-top: 8px !important;
}

.history-item {
    padding: 8px 20px !important;
    color: #a0a0a0 !important;
    font-size: 14px !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    border-left: 3px solid transparent !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
    margin: 0 !important;
}

.history-item:hover {
    background-color: #1f1f1f !important;
    color: #fff !important;
}

.history-item.selected {
    background-color: #1f1f1f !important;
    color: #fff !important;
    border-left-color: #d97757 !important;
}

.history-list label {
    padding: 8px 20px !important;
    color: #a0a0a0 !important;
    font-size: 14px !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    border-left: 3px solid transparent !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
    margin: 0 !important;
    background: transparent !important;
    border-top: none !important;
    border-right: none !important;
    border-bottom: none !important;
}

.history-list label:hover {
    background-color: #1f1f1f !important;
    color: #fff !important;
}

.history-list input[type="radio"]:checked + label {
    background-color: #1f1f1f !important;
    color: #fff !important;
    border-left-color: #d97757 !important;
}

.sidebar-footer {
    padding: 16px !important;
    border-top: 1px solid #2a2a2a !important;
}

.settings-accordion {
    margin-top: 8px !important;
}

.settings-content {
    padding: 12px 20px !important;
}

.setting-item {
    margin-bottom: 16px !important;
}

.setting-label {
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #a0a0a0 !important;
    margin-bottom: 6px !important;
    display: block !important;
}

.setting-control {
    width: 100% !important;
}

.setting-control select,
.setting-control input[type="text"] {
    background-color: #1f1f1f !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 6px !important;
    padding: 8px 12px !important;
    color: #fff !important;
    font-size: 14px !important;
    width: 100% !important;
}

.setting-control select:focus,
.setting-control input[type="text"]:focus {
    outline: none !important;
    border-color: #d97757 !important;
}

/* Chat Area */
.chat-area {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    background-color: #0f0f0f !important;
    position: relative !important;
    overflow: hidden !important;
}

.chat-header {
    padding: 16px 24px !important;
    border-bottom: 1px solid #2a2a2a !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
}

.chat-content {
    flex: 1 !important;
    overflow-y: auto !important;
    padding: 24px !important;
    padding-bottom: 120px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
}

#chatbot {
    width: 100% !important;
    max-width: 900px !important;
    background: transparent !important;
}

.message-row {
    margin-bottom: 24px !important;
    width: 100% !important;
}

.message-row.user-row .message {
    background-color: #1f1f1f !important;
    color: #fff !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    border: 1px solid #2a2a2a !important;
    max-width: 85% !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}

.message-row.bot-row .message {
    background: transparent !important;
    color: #e0e0e0 !important;
    padding: 0 !important;
    border: none !important;
    max-width: 100% !important;
}

/* Input Container */
.input-container {
    position: fixed !important;
    bottom: 0 !important;
    left: 260px !important;
    right: 0 !important;
    padding: 20px 24px !important;
    background-color: #0f0f0f !important;
    border-top: 1px solid #2a2a2a !important;
    z-index: 100 !important;
}

.input-wrapper {
    max-width: 900px !important;
    margin: 0 auto !important;
    position: relative !important;
}

.input-box {
    background-color: #1f1f1f !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    transition: border-color 0.2s !important;
}

.input-box:focus-within {
    border-color: #d97757 !important;
}

.input-icons {
    display: flex !important;
    gap: 8px !important;
    align-items: center !important;
}

.input-icon-btn {
    background: transparent !important;
    border: none !important;
    color: #707070 !important;
    cursor: pointer !important;
    padding: 6px !important;
    border-radius: 6px !important;
    transition: all 0.2s !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
}

.input-icon-btn:hover {
    background-color: #2a2a2a !important;
    color: #fff !important;
}

.input-icon-btn button {
    background: transparent !important;
    border: none !important;
    color: inherit !important;
    padding: 0 !important;
    width: 100% !important;
    height: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.input-icon-btn button:hover {
    background: transparent !important;
}

.input-textarea {
    flex: 1 !important;
    background: transparent !important;
    border: none !important;
    color: #fff !important;
    font-size: 15px !important;
    resize: none !important;
    outline: none !important;
    padding: 0 !important;
    min-height: 24px !important;
    max-height: 200px !important;
    overflow-y: auto !important;
}

.input-textarea::placeholder {
    color: #707070 !important;
}

.input-right {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}

.model-selector {
    background-color: #171717 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 6px !important;
    padding: 6px 10px !important;
    color: #a0a0a0 !important;
    font-size: 13px !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
}

.model-selector:hover {
    background-color: #1f1f1f !important;
    color: #fff !important;
}

.send-btn {
    background-color: #d97757 !important;
    border: none !important;
    border-radius: 8px !important;
    width: 32px !important;
    height: 32px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    transition: background-color 0.2s !important;
    color: #fff !important;
}

.send-btn:hover {
    background-color: #e08868 !important;
}

.send-btn::before {
    content: "↑" !important;
    font-size: 18px !important;
    font-weight: 600 !important;
}

.hidden {
    display: none !important;
}

/* Audio component styling */
.input-icon-btn audio {
    display: none !important;
}

.input-icon-btn .wrap {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    min-height: 32px !important;
    background: transparent !important;
    border: none !important;
}

.input-icon-btn .wrap button {
    background: transparent !important;
    border: none !important;
    color: #707070 !important;
    padding: 0 !important;
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    min-height: 32px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 16px !important;
    border-radius: 6px !important;
    transition: all 0.2s !important;
}

.input-icon-btn .wrap button:hover {
    background-color: #2a2a2a !important;
    color: #fff !important;
}

.input-icon-btn .wrap button::before {
    content: "🎤" !important;
    font-size: 16px !important;
}

/* Scrollbar */
.history-section::-webkit-scrollbar,
.chat-content::-webkit-scrollbar {
    width: 8px !important;
}

.history-section::-webkit-scrollbar-track,
.chat-content::-webkit-scrollbar-track {
    background: transparent !important;
}

.history-section::-webkit-scrollbar-thumb,
.chat-content::-webkit-scrollbar-thumb {
    background: #2a2a2a !important;
    border-radius: 4px !important;
}

.history-section::-webkit-scrollbar-thumb:hover,
.chat-content::-webkit-scrollbar-thumb:hover {
    background: #3a3a3a !important;
}
"""

theme = gr.themes.Base(
    primary_hue="orange",
    secondary_hue="zinc",
    neutral_hue="zinc",
    font=[gr.themes.GoogleFont("Inter"), "sans-serif"]
).set(
    body_background_fill="#0f0f0f",
    body_text_color="#e0e0e0",
    block_background_fill="#0f0f0f",
    block_border_width="0px",
    button_primary_background_fill="#d97757",
    button_primary_background_fill_hover="#e08868",
    button_primary_text_color="#fff"
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

def create_new_session(): 
    sid, _ = session_manager.create_session()
    return sid, [], gr.update(choices=refresh_session_list())
def load_session(evt: gr.SelectData): 
    if not evt.value: return None, []
    sessions = session_manager.list_sessions()
    session = next((s for s in sessions if s['title'] == evt.value), None)
    if session:
        return session['id'], session.get('history', [])
    return None, []
def refresh_session_list(): 
    sessions = session_manager.list_sessions()
    return [s['title'] for s in sessions]
def delete_current_session(sel): 
    if sel: 
        sessions = session_manager.list_sessions()
        session = next((s for s in sessions if s['title'] == sel), None)
        if session:
            session_manager.delete_session(session['id'])
    return gr.update(choices=refresh_session_list(), value=None), None, []
def add_path(p): text_engine.custom_dirs.append(Path(p)); return gr.update(choices=get_available_models())

# --- UI ---
with gr.Blocks(theme=theme, css=css, title="Antigravity") as demo:
    session_id = gr.State(None)
    selected_history_item = gr.State(None)
    
    with gr.Row(elem_classes=["main-layout"]):
        # Sidebar
        with gr.Column(elem_classes=["sidebar"], scale=0):
            # Header
            with gr.Column(elem_classes=["sidebar-header"]):
                gr.Markdown("### Antigravity", elem_classes=["sidebar-brand"])
            
            # New Chat Button
            new_chat_btn = gr.Button("New Chat", elem_classes=["new-chat-btn"])
            
            # Navigation (simplified)
            with gr.Column(elem_classes=["sidebar-nav"]):
                gr.Markdown("💬 Chats", elem_classes=["nav-item"])
            
            # History Section
            with gr.Column(elem_classes=["history-section"]):
                gr.Markdown("RECENTS", elem_classes=["history-section-label"])
                history_list = gr.Radio(
                    choices=[],
                    label="",
                    interactive=True,
                    container=False,
                    elem_classes=["history-list"],
                    show_label=False,
                    value=None
                )
            
            # Settings in Footer
            with gr.Column(elem_classes=["sidebar-footer"]):
                with gr.Accordion("⚙️ Settings", open=False, elem_classes=["settings-accordion"]):
                    with gr.Column(elem_classes=["settings-content"]):
                        # Model Selector
                        with gr.Column(elem_classes=["setting-item"]):
                            gr.Markdown("Model", elem_classes=["setting-label"])
                            model_selector = gr.Dropdown(
                                choices=get_available_models(),
                                label="",
                                interactive=True,
                                elem_classes=["setting-control"],
                                container=False,
                                show_label=False
                            )
                        
                        # Personality Selector
                        with gr.Column(elem_classes=["setting-item"]):
                            gr.Markdown("Personality", elem_classes=["setting-label"])
                            personality_selector = gr.Dropdown(
                                choices=list(PERSONALITIES.keys()),
                                value="Helpful Assistant",
                                label="",
                                interactive=True,
                                elem_classes=["setting-control"],
                                container=False,
                                show_label=False
                            )
                        
                        # Voice Settings
                        with gr.Column(elem_classes=["setting-item"]):
                            gr.Markdown("Voice", elem_classes=["setting-label"])
                            voice_chk = gr.Checkbox(label="Enable Voice", value=False, container=False)
                            voice_sel = gr.Dropdown(
                                choices=get_voice_list(),
                                value="en-US-AriaNeural",
                                label="",
                                interactive=True,
                                elem_classes=["setting-control"],
                                container=False,
                                show_label=False,
                                visible=False
                            )
                        
                        # Delete Chat Button
                        delete_chat_btn = gr.Button("🗑️ Delete Chat", variant="secondary", size="sm")
                        
                        # Custom Model Path
                        with gr.Column(elem_classes=["setting-item"]):
                            gr.Markdown("Custom Model Path", elem_classes=["setting-label"])
                            path_input = gr.Textbox(label="", container=False, show_label=False, elem_classes=["setting-control"])
                            add_path_btn = gr.Button("Add Path", variant="secondary", size="sm")
        
        # Chat Area
        with gr.Column(elem_classes=["chat-area"]):
            # Chat Content
            with gr.Column(elem_classes=["chat-content"]):
                chatbot = gr.Chatbot(
                    elem_id="chatbot",
                    bubble_full_width=False,
                    show_copy_button=True,
                    type="messages",
                    height="100%"
                )
            
            # Input Container (Fixed at bottom)
            with gr.Column(elem_classes=["input-container"]):
                with gr.Column(elem_classes=["input-wrapper"]):
                    with gr.Row(elem_classes=["input-box"]):
                        # Left Icons
                        with gr.Column(elem_classes=["input-icons"], scale=0):
                            upload_btn = gr.UploadButton(
                                "📎",
                                file_types=["image"],
                                elem_classes=["input-icon-btn"],
                                size="sm",
                                scale=0
                            )
                            mic_btn = gr.Audio(
                                sources=["microphone"],
                                type="filepath",
                                show_label=False,
                                container=False,
                                elem_classes=["input-icon-btn"],
                                scale=0
                            )
                        
                        # Text Input
                        msg_input = gr.Textbox(
                            placeholder="Message...",
                            show_label=False,
                            container=False,
                            lines=1,
                            max_lines=10,
                            elem_classes=["input-textarea"],
                            autofocus=True,
                            scale=1
                        )
                        
                        # Right Side (Model Selector + Send)
                        with gr.Column(elem_classes=["input-right"], scale=0):
                            personality_display = gr.Dropdown(
                                choices=list(PERSONALITIES.keys()),
                                value="Helpful Assistant",
                                label="",
                                interactive=True,
                                container=False,
                                show_label=False,
                                elem_classes=["model-selector"],
                                scale=0
                            )
                            send_btn = gr.Button("", elem_classes=["send-btn"], scale=0)
            
            status_display = gr.Markdown("", visible=False)
            audio_out = gr.Audio(visible=False, autoplay=True)
    
    # Event Handlers
    def on_load():
        session_manager.cleanup_empty_sessions()
        sid, _ = session_manager.create_session()
        models = get_available_models()
        def_model = next((m for m in models if "⬇️" not in m and any(x in m for x in ["1B", "3B", "Phi"])), None)
        if not def_model: def_model = next((m for m in models if "⬇️" not in m), None)
        status = text_engine.load_model(def_model) if def_model else "No model"
        # Show welcome message if no history
        welcome_msg = [{"role": "assistant", "content": "Hello! How can I help you today?"}]
        return sid, gr.update(choices=refresh_session_list()), models, def_model, status, welcome_msg
    
    def update_voice_visibility(voice_enabled):
        return gr.update(visible=voice_enabled)
    
    # Wire up events
    demo.load(
        on_load,
        None,
        [session_id, history_list, model_selector, model_selector, status_display, chatbot]
    )
    
    new_chat_btn.click(
        create_new_session,
        None,
        [session_id, chatbot, history_list]
    )
    
    def load_session_from_title(title):
        if not title: return None, []
        sessions = session_manager.list_sessions()
        session = next((s for s in sessions if s['title'] == title), None)
        if session:
            return session['id'], session.get('history', [])
        return None, []
    
    history_list.change(
        load_session_from_title,
        history_list,
        [session_id, chatbot]
    )
    
    delete_chat_btn.click(
        delete_current_session,
        history_list,
        [history_list, session_id, chatbot]
    )
    
    model_selector.change(
        handle_model_change,
        model_selector,
        [model_selector, status_display]
    )
    
    add_path_btn.click(
        add_path,
        path_input,
        model_selector
    )
    
    voice_chk.change(
        update_voice_visibility,
        voice_chk,
        voice_sel
    )
    
    # Sync personality selectors
    personality_selector.change(
        lambda x: x,
        personality_selector,
        personality_display
    )
    
    personality_display.change(
        lambda x: x,
        personality_display,
        personality_selector
    )
    
    # Chat input handlers
    chat_args = [msg_input, chatbot, session_id, personality_selector, voice_chk, voice_sel]
    
    def chat_wrapper(*args):
        for result in chat_turn(*args):
            history, audio, _ = result
            yield history, audio, gr.update(choices=refresh_session_list())
    
    msg_input.submit(
        chat_wrapper,
        chat_args,
        [chatbot, audio_out, history_list]
    ).then(lambda: "", None, msg_input)
    
    send_btn.click(
        chat_wrapper,
        chat_args,
        [chatbot, audio_out, history_list]
    ).then(lambda: "", None, msg_input)
    
    mic_btn.stop_recording(
        transcribe_audio,
        mic_btn,
        msg_input
    )

if __name__ == "__main__":
    demo.queue().launch(inbrowser=True)
