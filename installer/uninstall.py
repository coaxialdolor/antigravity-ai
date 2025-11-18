import shutil
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).parent.parent.absolute()
VENV_DIR = ROOT_DIR / "venv"
APP_DIR = ROOT_DIR / "app"
MODELS_DIR = ROOT_DIR / "models"
CONFIG_FILE = APP_DIR / "config.json"

def log(msg):
    print(f"[UNINSTALLER] {msg}")

def uninstall():
    log("Starting uninstallation...")
    
    # 1. Remove venv
    if VENV_DIR.exists():
        log(f"Removing virtual environment: {VENV_DIR}")
        try:
            shutil.rmtree(VENV_DIR)
        except Exception as e:
            log(f"Error removing venv: {e}")
    else:
        log("No virtual environment found.")

    # 2. Remove Config
    if CONFIG_FILE.exists():
        log(f"Removing config file: {CONFIG_FILE}")
        try:
            CONFIG_FILE.unlink()
        except Exception as e:
            log(f"Error removing config: {e}")

    # 3. Optional: Remove Models (Ask user? For now, we just warn or keep them as they are heavy)
    # The requirement says "clean uninstall... removes all files". 
    # Usually users hate losing GBs of models. I will remove the folders if they are inside the project.
    if MODELS_DIR.exists():
        log(f"Removing models directory: {MODELS_DIR}")
        try:
            shutil.rmtree(MODELS_DIR)
        except Exception as e:
            log(f"Error removing models: {e}")

    # 4. Remove __pycache__ and other artifacts
    for path in ROOT_DIR.rglob("__pycache__"):
        try:
            shutil.rmtree(path)
        except Exception:
            pass

    log("Uninstallation complete. You can now delete the project folder.")

if __name__ == "__main__":
    print("WARNING: This will delete the virtual environment, configuration, and downloaded models.")
    confirm = input("Type 'yes' to continue: ")
    if confirm.lower() == "yes":
        uninstall()
    else:
        print("Uninstallation cancelled.")
