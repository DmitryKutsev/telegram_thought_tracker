import os
import shutil
import sys
from pathlib import Path

_root = Path(__file__).parent.parent
if not (_root / "config.yaml").exists() and (_root / "config_example.yaml").exists():
    shutil.copy(_root / "config_example.yaml", _root / "config.yaml")

sys.path.insert(0, str(_root / "src"))

# Fallback values so config.py loads even without a real .env
os.environ.setdefault("TOGETHER_API_KEY", "test-key-together")
os.environ.setdefault("OPENAI_API_KEY", "test-key-openai")
os.environ.setdefault("GOOGLE_API_KEY", "test-key-google")
os.environ.setdefault("BOT_KEY", "0:test-bot-key")