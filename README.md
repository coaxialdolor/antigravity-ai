# Multimodal AI Assistant

A one-click installer and local AI assistant featuring Text, Voice, and Image generation.

## Features
- **One-Click Install**: Automatically sets up Python virtual environment and installs dependencies (CUDA-aware).
- **Text Chat**: Local LLM support via `llama-cpp-python` (GGUF models).
- **Voice**: Expressive TTS using Edge-TTS.
- **Image**: Local image generation using Stable Diffusion.
- **Settings**: Configurable preferences and hardware detection.

## Installation
1. Double-click `setup.bat`.
2. Wait for the installation to complete (this may take a while as it downloads dependencies).
3. Once finished, run `run.bat` to start the app.

## Usage
- **Chat**: Load a `.gguf` model into `models/llm` (or let the app guide you) and start chatting.
- **Voice**: Type text and click Speak.
- **Image**: Enter a prompt and generate images.

## Uninstallation
Run `python installer/uninstall.py` (or create a bat for it) to remove the environment and configs.

## Requirements
- Windows 10/11
- Python 3.10+
- NVIDIA GPU recommended (for fast inference), but CPU is supported.
