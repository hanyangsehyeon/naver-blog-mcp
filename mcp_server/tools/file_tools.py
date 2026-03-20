"""
File I/O tools: read_file, save_output, get_style_profile, get_formatting_rules.
"""
import os, json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_DIR = os.path.join(ROOT, "input")
OUTPUT_DIR = os.path.join(ROOT, "output")
STYLE_PROFILE_PATH = os.path.join(ROOT, "style_profile.json")
FORMATTING_RULES_PATH = os.path.join(ROOT, "formatting_rules.json")


def read_file(filename: str) -> str:
    """Read a file from the input/ directory."""
    path = os.path.join(INPUT_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"input/{filename} not found")
    with open(path, encoding="utf-8") as f:
        return f.read()


def save_output(filename: str, content: dict | str) -> str:
    """Save transformed content to output/ directory."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not filename.endswith(".json"):
        filename += ".json"
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        if isinstance(content, str):
            f.write(content)
        else:
            json.dump(content, f, ensure_ascii=False, indent=2)
    return path


def get_style_profile() -> dict | None:
    """Return style_profile.json contents, or None if not yet generated."""
    if not os.path.exists(STYLE_PROFILE_PATH):
        return None
    with open(STYLE_PROFILE_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_formatting_rules() -> dict:
    """Return formatting_rules.json contents."""
    if not os.path.exists(FORMATTING_RULES_PATH):
        return {}
    with open(FORMATTING_RULES_PATH, encoding="utf-8") as f:
        return json.load(f)
