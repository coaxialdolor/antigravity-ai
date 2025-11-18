import requests
from pathlib import Path

MODELS_DIR = Path("models/voice")

FILES = [
    {
        "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx",
        "name": "kokoro-v0_19.onnx"
    },
    {
        "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.json",
        "name": "voices.json"
    }
]

def download_voice_models():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print("Checking voice models...")
    
    for item in FILES:
        dest = MODELS_DIR / item["name"]
        if not dest.exists():
            print(f"Downloading {item['name']}...")
            try:
                r = requests.get(item["url"], stream=True)
                r.raise_for_status()
                with open(dest, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print("Done.")
            except Exception as e:
                print(f"Failed to download {item['name']}: {e}")
        else:
            print(f"{item['name']} exists.")

if __name__ == "__main__":
    download_voice_models()
