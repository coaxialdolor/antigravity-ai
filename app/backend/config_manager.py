import json
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path="app/config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            # Default config with user's requested paths
            default_config = {
                "custom_model_paths": [
                    "B:\\AI\\LLM-Models",
                    "B:\\AI\\models"
                ],
                "preferences": {
                    "theme": "dark"
                }
            }
            return default_config
            
        with open(self.config_path, "r") as f:
            config = json.load(f)
            
        # Ensure custom paths exist in loaded config
        if "custom_model_paths" not in config:
            config["custom_model_paths"] = [
                "B:\\AI\\LLM-Models",
                "B:\\AI\\models"
            ]
        return config

    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def get_nested(self, keys, default=None):
        """Get a value from nested dictionaries."""
        val = self.config
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default

    def update(self, key, value):
        self.config[key] = value
        self._save()

    def _save(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)
