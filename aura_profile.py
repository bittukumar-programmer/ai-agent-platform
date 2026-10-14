import json
import os

PROFILE_FILE = "aura_profile.json"


def load_profile() -> dict:
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def profile_as_text() -> str:
    """Formats the profile as readable text for AURA's system instructions."""
    p = load_profile()
    lines = []
    if p.get("name"):
        lines.append(f"- His name is {p['name']}.")
    if p.get("address"):
        lines.append(f"- His address: {p['address']}.")
    if p.get("college"):
        lines.append(f"- College: {p['college']}.")
    if p.get("branch"):
        lines.append(f"- Branch/course: {p['branch']}.")
    if p.get("projects"):
        lines.append(f"- His projects: {', '.join(p['projects'])}.")
    return "\n".join(lines) if lines else "No profile information saved yet."