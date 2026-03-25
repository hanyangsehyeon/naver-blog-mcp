"""
File I/O tools: convert_hwpx, read_file, save_output, get_formatting_rules.
"""
import os, json, zipfile, xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_DIR  = os.path.join(ROOT, "input")   # hwpx 원본
DRAFTS_DIR = os.path.join(ROOT, "drafts")  # 변환된 txt
OUTPUT_DIR = os.path.join(ROOT, "output")
FORMATTING_RULES_PATH = os.path.join(ROOT, "formatting_rules.json")


def convert_hwpx(filename: str) -> str:
    """Convert a .hwpx file from input/ to .txt in drafts/. Returns saved txt path."""
    hwpx_path = os.path.join(INPUT_DIR, filename)
    if not os.path.exists(hwpx_path):
        raise FileNotFoundError(f"input/{filename} not found")

    extracted = []
    with zipfile.ZipFile(hwpx_path, "r") as z:
        section_files = sorted(
            f for f in z.namelist()
            if f.startswith("Contents/section") and f.endswith(".xml")
        )
        if not section_files:
            raise ValueError(f"section XML not found in {filename}")
        for section_file in section_files:
            with z.open(section_file) as f:
                root = ET.fromstring(f.read())
                for tag in root.iter():
                    if tag.tag.endswith("}t") or tag.tag == "t":
                        if tag.text:
                            extracted.append(tag.text)
                    elif tag.tag.endswith("}p") or tag.tag == "p":
                        extracted.append("\n")

    text = "".join(extracted).strip()
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    txt_filename = os.path.splitext(filename)[0] + ".txt"
    txt_path = os.path.join(DRAFTS_DIR, txt_filename)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    return txt_path


def read_file(filename: str) -> str:
    """Read a .txt file from the drafts/ directory."""
    path = os.path.join(DRAFTS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"drafts/{filename} not found")
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


def load_output(filename: str) -> dict:
    """Load a saved output JSON from output/ directory."""
    if not filename.endswith(".json"):
        filename += ".json"
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"output/{filename} not found")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_formatting_rules() -> dict:
    """Return formatting_rules.json contents."""
    if not os.path.exists(FORMATTING_RULES_PATH):
        return {}
    with open(FORMATTING_RULES_PATH, encoding="utf-8") as f:
        return json.load(f)
