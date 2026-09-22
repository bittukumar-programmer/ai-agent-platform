import json
import os

MEMORY_FILE = "agent_memory.json"


def load_memory() -> list:
    """Loads saved conversation history from a local file, if it exists."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_memory(history: list):
    """Saves conversation history to a local file."""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Could not save memory: {e}")