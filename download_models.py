import requests
import sys
from pathlib import Path

MODELS_DIR = Path("models")
LLM_DIR = MODELS_DIR / "llm"

# Models to download
MODELS = [
    {
        "url": "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "name": "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
    },
    {
        "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "name": "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    },
    {
        "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "name": "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    },
    {
        "url": "https://huggingface.co/TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/resolve/main/openhermes-2.5-mistral-7b.Q4_K_M.gguf",
        "name": "openhermes-2.5-mistral-7b.Q4_K_M.gguf"
    },
    {
        "url": "https://huggingface.co/TheBloke/Gemma-7b-it-GGUF/resolve/main/gemma-7b-it.Q4_K_M.gguf",
        "name": "gemma-7b-it.Q4_K_M.gguf"
    },
    {
        "url": "https://huggingface.co/TheBloke/Phi-3-mini-4k-instruct-GGUF/resolve/main/Phi-3-mini-4k-instruct.Q4_K_M.gguf",
        "name": "Phi-3-mini-4k-instruct.Q4_K_M.gguf"
    },
    {
        "url": "https://huggingface.co/MaziyarPanahi/Llama-3-8B-Instruct-GGUF/resolve/main/Llama-3-8B-Instruct.Q4_K_M.gguf",
        "name": "Llama-3-8B-Instruct.Q4_K_M.gguf"
    }
]

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    print(f"Saving to {dest_path}")
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    # Simple progress indicator
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end="")
        print("\nDownload complete.")
    except Exception as e:
        print(f"\nError downloading: {e}")

def main():
    LLM_DIR.mkdir(parents=True, exist_ok=True)
    
    for model in MODELS:
        dest = LLM_DIR / model["name"]
        if dest.exists():
            print(f"{model['name']} already exists.")
        else:
            download_file(model["url"], dest)

if __name__ == "__main__":
    main()
