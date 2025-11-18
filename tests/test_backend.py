import sys
import os
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent.parent))

def test_imports():
    print("Testing imports...")
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
    except ImportError as e:
        print(f"Failed to import PyTorch: {e}")

    try:
        from app.backend.text_engine import TextEngine
        print("TextEngine imported.")
    except ImportError as e:
        print(f"Failed to import TextEngine: {e}")

    try:
        from app.backend.voice_engine import VoiceEngine
        print("VoiceEngine imported.")
    except ImportError as e:
        print(f"Failed to import VoiceEngine: {e}")

    try:
        from app.backend.image_engine import ImageEngine
        print("ImageEngine imported.")
    except ImportError as e:
        print(f"Failed to import ImageEngine: {e}")

if __name__ == "__main__":
    test_imports()
