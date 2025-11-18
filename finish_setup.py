import os
import json
from pathlib import Path

ROOT_DIR = Path(".").absolute()
MODELS_DIR = ROOT_DIR / "models"
CONFIG_FILE = ROOT_DIR / "app" / "config.json"

def finish_setup():
    print("Finishing setup...")
    MODELS_DIR.mkdir(exist_ok=True)
    (MODELS_DIR / "llm").mkdir(exist_ok=True)
    (MODELS_DIR / "voice").mkdir(exist_ok=True)
    (MODELS_DIR / "image").mkdir(exist_ok=True)

    config = {
        "hardware": {"has_nvidia_gpu": True}, # We know this from the test
        "paths": {
            "models_root": str(MODELS_DIR),
            "llm_dir": str(MODELS_DIR / "llm"),
            "voice_dir": str(MODELS_DIR / "voice"),
            "image_dir": str(MODELS_DIR / "image")
        },
        "preferences": {
            "voice_id": "en-US-AriaNeural",
            "personality": "Helpful Assistant",
            "theme": "dark"
        }
    }
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    print("Setup finished.")

if __name__ == "__main__":
    finish_setup()
