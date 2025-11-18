import os
import sys
import subprocess
import venv
import platform
import shutil
import json
from pathlib import Path

# --- Constants ---
ROOT_DIR = Path(__file__).parent.parent.absolute()
VENV_DIR = ROOT_DIR / "venv"
APP_DIR = ROOT_DIR / "app"
MODELS_DIR = ROOT_DIR / "models"
CONFIG_FILE = APP_DIR / "config.json"

def log(msg):
    print(f"[INSTALLER] {msg}")

def check_hardware():
    """
    Detects hardware capabilities (CPU/GPU).
    Returns a dict with hardware info.
    """
    log("Detecting hardware...")
    hardware_info = {
        "platform": platform.system(),
        "processor": platform.processor(),
        "has_nvidia_gpu": False,
        "vram_gb": 0
    }

    # Simple check for NVIDIA GPU via nvidia-smi
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'], 
                                capture_output=True, text=True)
        if result.returncode == 0:
            hardware_info["has_nvidia_gpu"] = True
            # Sum up VRAM if multiple GPUs (naive approach, but works for detection)
            vram_total = sum(int(x) for x in result.stdout.strip().split('\n') if x.isdigit())
            hardware_info["vram_gb"] = round(vram_total / 1024, 2)
            log(f"NVIDIA GPU detected with {hardware_info['vram_gb']} GB VRAM.")
        else:
            log("No NVIDIA GPU detected (nvidia-smi not found or failed).")
    except FileNotFoundError:
        log("nvidia-smi not found. Assuming CPU only.")
    
    return hardware_info

def create_venv():
    """Creates a virtual environment."""
    if VENV_DIR.exists():
        log(f"Virtual environment already exists at {VENV_DIR}. Skipping creation.")
        return

    log(f"Creating virtual environment at {VENV_DIR}...")
    venv.create(VENV_DIR, with_pip=True)
    log("Virtual environment created.")

def get_pip_path():
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "pip.exe"
    else:
        return VENV_DIR / "bin" / "pip"

def install_dependencies(hardware_info):
    """Installs dependencies based on hardware."""
    pip_cmd = str(get_pip_path())
    
    log("Upgrading pip...")
    subprocess.check_call([pip_cmd, "install", "--upgrade", "pip"])

    # 1. Install PyTorch
    log("Installing PyTorch...")
    if hardware_info["has_nvidia_gpu"]:
        # Install CUDA 12.4 compatible PyTorch (stable as of late 2024/early 2025)
        # Using download.pytorch.org
        torch_cmd = [
            pip_cmd, "install", 
            "torch", "torchvision", "torchaudio", 
            "--index-url", "https://download.pytorch.org/whl/cu124"
        ]
        log("Targeting CUDA 12.4...")
    else:
        # CPU only
        torch_cmd = [
            pip_cmd, "install", 
            "torch", "torchvision", "torchaudio"
        ]
        log("Targeting CPU...")
    
    try:
        subprocess.check_call(torch_cmd)
    except subprocess.CalledProcessError:
        log("Failed to install PyTorch. Retrying with standard index...")
        subprocess.check_call([pip_cmd, "install", "torch", "torchvision", "torchaudio"])

    # 2. Install other requirements
    requirements = [
        "gradio",
        "llama-cpp-python", # For GGUF
        "diffusers",
        "transformers",
        "accelerate",
        "scipy",
        "ftfy",
        "soundfile",
        "edge-tts", # Good fallback for TTS
        "SpeechRecognition", # For microphone input logic if needed, or just use Gradio's built-in
        "numpy",
        "Pillow",
        "requests"
    ]

    # If GPU, we might want specific llama-cpp-python build args, 
    # but prebuilt wheels often work or it compiles. 
    # For simplicity in a python script, we just pip install. 
    # Advanced: set CMAKE_ARGS="-DGGML_CUDA=on" before install if compiling.
    
    log("Installing application dependencies...")
    
    # Special handling for llama-cpp-python with CUDA if possible
    env = os.environ.copy()
    llama_args = []
    
    if hardware_info["has_nvidia_gpu"]:
        env["CMAKE_ARGS"] = "-DGGML_CUDA=on"
        # Try to use pre-built wheels for CUDA 12.x to avoid compilation
        # Note: The version in the URL might need to match the CUDA version exactly or be close.
        # Using a generic approach or the official repo wheels.
        llama_args = ["--extra-index-url", "https://abetlen.github.io/llama-cpp-python/whl/cu124"]
        log("Using pre-built CUDA wheels for llama-cpp-python if available...")
    
    # Install llama-cpp-python separately to ensure args are applied or wheels are found
    try:
        subprocess.check_call([pip_cmd, "install", "llama-cpp-python"] + llama_args, env=env)
    except subprocess.CalledProcessError:
        log("Warning: Failed to install llama-cpp-python with CUDA wheels. Falling back to standard install (might require VS Build Tools)...")
        subprocess.check_call([pip_cmd, "install", "llama-cpp-python"])

    # Install remaining requirements
    remaining_reqs = [r for r in requirements if "llama-cpp-python" not in r]
    subprocess.check_call([pip_cmd, "install"] + remaining_reqs, env=env)
    
    log("Dependencies installed.")

def create_default_config(hardware_info):
    """Creates a default config file."""
    MODELS_DIR.mkdir(exist_ok=True)
    (MODELS_DIR / "llm").mkdir(exist_ok=True)
    (MODELS_DIR / "voice").mkdir(exist_ok=True)
    (MODELS_DIR / "image").mkdir(exist_ok=True)

    config = {
        "hardware": hardware_info,
        "paths": {
            "models_root": str(MODELS_DIR),
            "llm_dir": str(MODELS_DIR / "llm"),
            "voice_dir": str(MODELS_DIR / "voice"),
            "image_dir": str(MODELS_DIR / "image")
        },
        "preferences": {
            "voice_id": "en-US-AriaNeural", # Edge-TTS default
            "personality": "Helpful Assistant",
            "theme": "dark"
        }
    }
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    
    log(f"Config saved to {CONFIG_FILE}")

def main():
    log("Starting installation...")
    
    # 1. Hardware Detection
    hw_info = check_hardware()
    
    # 2. Venv Creation
    create_venv()
    
    # 3. Install Deps
    install_dependencies(hw_info)
    
    # 4. Config & Directories
    create_default_config(hw_info)
    
    log("Installation finished successfully.")

if __name__ == "__main__":
    main()
