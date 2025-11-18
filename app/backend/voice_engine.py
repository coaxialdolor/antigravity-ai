import edge_tts
import asyncio
import tempfile
import os
import soundfile as sf
import numpy as np
from pathlib import Path

# Try importing local engines
try:
    from kokoro_onnx import Kokoro
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False

class VoiceEngine:
    def __init__(self, models_dir="models/voice"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.kokoro = None
        self.kokoro_model_path = self.models_dir / "kokoro-v0_19.onnx"
        self.kokoro_voices_path = self.models_dir / "voices.json"
        
        # Edge TTS Voices
        self.edge_voices = [
            "en-US-AriaNeural", 
            "en-US-GuyNeural", 
            "en-US-ChristopherNeural", 
            "en-US-JennyNeural",
            "en-GB-SoniaNeural",
            "en-GB-RyanNeural",
            "en-AU-NatashaNeural",
            "en-AU-WilliamNeural"
        ]

    async def text_to_speech(self, text, voice_id, output_file=None):
        if not output_file:
            fd, output_file = tempfile.mkstemp(suffix=".wav")
            os.close(fd)

        # 1. Local Kokoro
        if voice_id.startswith("lokal-"):
            if not KOKORO_AVAILABLE:
                print("Kokoro not installed.")
                return None
            
            if not self.kokoro:
                if not self.kokoro_model_path.exists():
                    print("Kokoro model not found. Please download it.")
                    return None
                self.kokoro = Kokoro(str(self.kokoro_model_path), str(self.kokoro_voices_path))
            
            # Map ID to kokoro voice
            k_voice = voice_id.replace("lokal-", "")
            # Kokoro generate returns audio samples and sample rate
            samples, sample_rate = self.kokoro.create(text, voice=k_voice, speed=1.0, lang="en-us")
            
            sf.write(output_file, samples, sample_rate)
            return output_file

        # 2. Edge TTS (Online)
        communicate = edge_tts.Communicate(text, voice_id)
        await communicate.save(output_file)
        return output_file

    def get_available_voices(self):
        voices = self.edge_voices.copy()
        if KOKORO_AVAILABLE and self.kokoro_model_path.exists():
            # Add Kokoro voices (hardcoded common ones for now as loading json is heavy just for list)
            voices.extend(["lokal-af_bella", "lokal-af_sarah", "lokal-am_adam", "lokal-am_michael"])
        return voices

# Synchronous wrapper
def tts_sync(text, voice_id):
    engine = VoiceEngine() # Re-init to ensure paths (lightweight)
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    output_path = loop.run_until_complete(engine.text_to_speech(text, voice_id))
    return output_path
