from faster_whisper import WhisperModel
from pathlib import Path
import os

class STTEngine:
    def __init__(self, models_dir="models/stt", model_size="tiny"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.model_size = model_size
        self.model = None

    def load_model(self):
        if not self.model:
            # Run on GPU with FP16
            # If no GPU, it falls back or we can force cpu
            device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") != "-1" else "cpu" 
            # Actually faster-whisper handles auto detection usually, but let's be explicit if we know
            try:
                self.model = WhisperModel(self.model_size, device="auto", compute_type="float16", download_root=str(self.models_dir))
            except Exception:
                # Fallback to int8/cpu if float16 fails (common on some cards)
                self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8", download_root=str(self.models_dir))

    def transcribe(self, audio_path):
        if not self.model:
            self.load_model()
        
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        text = "".join([segment.text for segment in segments])
        return text.strip()
