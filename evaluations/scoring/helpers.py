import json
from pathlib import Path


def normalize_text(text):
    text = str(text).lower().strip()
    return text


def load_json(file_path):
    return json.loads(Path(file_path).read_text(encoding="utf-8"))

