import json
import os
from pathlib import Path

class ConfigManager:
    DEFAULT_CONFIG = {
        "default_grid_mode": "zoom",  # Options: zoom, minimap, roving
    }
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "visscreen"
        self.config_path = self.config_dir / "config.json"
        self.config = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
            except Exception:
                pass

    def save(self):
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception:
            pass

    def get(self, key):
        return self.config.get(key, self.DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()
