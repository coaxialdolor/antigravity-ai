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
from app.backend.session_manager import SessionManager
import asyncio
from download_models import MODELS as DOWNLOADABLE_MODELS, download_file

# --- Initialization ---
config = ConfigManager()
models_root = config.get_nested(["paths", "models_root"], "models")
custom_paths = config.get("custom_model_paths", [])

text_engine = TextEngine(os.path.join(models_root, "llm"), custom_paths)
image_engine = ImageEngine(os.path.join(models_root, "image"))
session_manager = SessionManager()

# --- Constants & Theme ---
# Modern, sharp theme
theme = gr.themes.Base(
    primary_hue="zinc",
    secondary_hue="stone",
    neutral_hue="neutral",
    radius_size=gr.themes.sizes.radius_sm, # Sharper corners
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

def chat_turn(message, history, session_id, personality, voice_enabled, voice_id):
    if not message.strip():
        return history, None, gr.update()

    # 1. Save user message
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
        
    return new_history, audio, gr.update(choices=refresh_session_list())

def create_new_session():
    sid, _ = session_manager.create_session()
    return sid, [], gr.update(choices=refresh_session_list())

def load_session(evt: gr.SelectData):
    # evt.value is the display string "Title (Date)" usually, but we need ID.
    # Gradio DataFrame or Listbox is better. Let's use a Dataset or Radio? 
    # Radio is easiest for list.
    # We need to parse ID from the selection string or maintain a map.
    # Let's assume the value passed is the label.
    # We will store "Title | ID" in the list.
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
                height=700, 
                bubble_full_width=False,
                show_copy_button=True,
                avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=KD")
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    scale=4, 
                    placeholder="Type a message...", 
                    show_label=False,
                    container=False,
                    autofocus=True,
                    lines=3
                )
                send_btn = gr.Button("➤", scale=1, variant="primary")
            
            audio_out = gr.Audio(visible=False, autoplay=True)

    # --- Wiring ---
    
    # Init
    def on_load():
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

    # Chat
    chat_inputs = [msg_input, chatbot, session_id, personality_selector, voice_chk, voice_sel]
    chat_outputs = [chatbot, audio_out, history_list]
    
    msg_input.submit(chat_turn, chat_inputs, chat_outputs).then(lambda: "", None, msg_input)
    send_btn.click(chat_turn, chat_inputs, chat_outputs).then(lambda: "", None, msg_input)

    # Custom Path
    def add_path(p):
        text_engine.custom_dirs.append(Path(p))
        return gr.update(choices=get_available_models())
        
    add_path_btn.click(add_path, path_input, model_selector)

if __name__ == "__main__":
    demo.queue().launch(inbrowser=True)
