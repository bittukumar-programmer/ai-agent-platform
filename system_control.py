import os
import subprocess

# Base folder where the assistant will create files/folders, to keep things safe and organized
WORKSPACE = os.path.join(os.path.expanduser("~"), "Desktop", "AI_Workspace")
os.makedirs(WORKSPACE, exist_ok=True)


def open_notepad(filename: str = None) -> str:
    """Opens Notepad, optionally with a specific file."""
    try:
        if filename:
            path = os.path.join(WORKSPACE, filename)
            if not os.path.exists(path):
                open(path, "w").close()
            subprocess.Popen(["notepad.exe", path])
            return f"Opened Notepad with {filename}"
        else:
            subprocess.Popen(["notepad.exe"])
            return "Opened Notepad"
    except Exception as e:
        return f"Error opening Notepad: {e}"


def create_folder(folder_name: str) -> str:
    """Creates a new folder inside the AI Workspace."""
    try:
        path = os.path.join(WORKSPACE, folder_name)
        os.makedirs(path, exist_ok=True)
        return f"Created folder '{folder_name}' at {path}"
    except Exception as e:
        return f"Error creating folder: {e}"


def create_file(filename: str, folder_name: str = None, content: str = "") -> str:
    """Creates a new file, optionally inside a specific folder within the workspace."""
    try:
        base = os.path.join(WORKSPACE, folder_name) if folder_name else WORKSPACE
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Created file '{filename}' at {path}"
    except Exception as e:
        return f"Error creating file: {e}"


def open_vscode(path: str = None) -> str:
    """Opens VS Code, optionally at a specific folder/file path."""
    try:
        target = path if path else WORKSPACE
        subprocess.Popen(["code", target], shell=True)
        return f"Opened VS Code at {target}"
    except Exception as e:
        return f"Error opening VS Code: {e}"


def close_app(app_name: str) -> str:
    """Force-closes an application by its process name (e.g. 'Code.exe', 'notepad.exe')."""
    try:
        subprocess.run(["taskkill", "/IM", app_name, "/F"], capture_output=True)
        return f"Closed {app_name}"
    except Exception as e:
        return f"Error closing {app_name}: {e}"