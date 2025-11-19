
import os
from pathlib import Path
from app.backend.text_engine import TextEngine
from app.backend.config_manager import ConfigManager

# Setup test environment
test_dir = Path("test_custom_models")
test_dir.mkdir(exist_ok=True)
(test_dir / "test_model.gguf").touch()

print(f"Created test model at {test_dir.absolute()}")

# Initialize ConfigManager
config = ConfigManager("test_config.json")
print(f"Initial config: {config.config}")

# Initialize TextEngine
# We'll use a dummy default dir
default_dir = Path("models/llm")
text_engine = TextEngine(default_dir, config.get("custom_model_paths", []))

print("Initial models:", text_engine.list_models())

# Add custom path
custom_path = str(test_dir.absolute())
print(f"Adding custom path: {custom_path}")

if Path(custom_path) not in text_engine.custom_dirs:
    text_engine.custom_dirs.append(Path(custom_path))

# Update config
current_paths = config.get("custom_model_paths", [])
if custom_path not in current_paths:
    current_paths.append(custom_path)
    config.update("custom_model_paths", current_paths)

print("Updated config:", config.config)

# List models again
models = text_engine.list_models()
print("Models after adding custom path:", models)

if "test_model.gguf" in models:
    print("SUCCESS: Test model found.")
else:
    print("FAILURE: Test model NOT found.")

# Cleanup
import shutil
if test_dir.exists():
    shutil.rmtree(test_dir)
if Path("test_config.json").exists():
    os.remove("test_config.json")
