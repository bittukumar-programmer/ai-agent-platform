import os
import glob

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def list_own_files() -> list:
    """Lists all Python files in AURA's own project folder (read-only listing)."""
    return [os.path.basename(f) for f in glob.glob(os.path.join(PROJECT_DIR, "*.py"))]


def read_own_code(filename: str) -> str:
    """
    Reads one of AURA's own source files, READ-ONLY. Refuses anything outside
    the project folder or any file that isn't a .py file, for safety.
    """
    safe_name = os.path.basename(filename)  # strips any path traversal attempt like ../../
    if not safe_name.endswith(".py"):
        return "Error: can only read .py files."
    full_path = os.path.join(PROJECT_DIR, safe_name)
    if not os.path.exists(full_path):
        return f"Error: {safe_name} not found."
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()[:8000]  # cap length so it doesn't overwhelm the LLM
    except Exception as e:
        return f"Error reading file: {e}"


def check_system_health() -> dict:
    """Runs lightweight checks on each major subsystem AURA depends on."""
    results = {}

    # 1. Gemini API key present
    results["gemini_api_key"] = "OK" if os.getenv("GEMINI_API_KEY") else "MISSING"

    # 2. Memory database reachable
    try:
        from memory_store import collection
        count = collection.count()
        results["memory_db"] = f"OK ({count} memories stored)"
    except Exception as e:
        results["memory_db"] = f"ERROR: {e}"

    # 3. Webcam accessible
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        results["webcam"] = "OK" if cap.isOpened() else "NOT DETECTED"
        cap.release()
    except Exception as e:
        results["webcam"] = f"ERROR: {e}"

    # 4. WhatsApp session saved
    whatsapp_session = os.path.join(os.path.expanduser("~"), "aura_whatsapp_session")
    results["whatsapp_session"] = "OK (logged in)" if os.path.exists(whatsapp_session) else "NOT LOGGED IN"

    # 5. Voice profile enrolled
    results["voice_profile"] = "OK" if os.path.exists("voice_profile.npy") else "NOT ENROLLED"

    # 6. Profile data saved
    results["personal_profile"] = "OK" if os.path.exists("aura_profile.json") else "NOT SET UP"

    return results