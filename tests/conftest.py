import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Fallback values so config.py loads even without a real .env
os.environ.setdefault("TOGETHER_API_KEY", "test-key-together")
os.environ.setdefault("OPENAI_API_KEY", "test-key-openai")
os.environ.setdefault("GOOGLE_API_KEY", "test-key-google")
os.environ.setdefault("BOT_KEY", "0:test-bot-key")