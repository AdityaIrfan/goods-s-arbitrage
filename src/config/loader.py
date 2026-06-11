import json
from pathlib import Path

_SUBJECTS_DIR = Path(__file__).resolve().parent / "subjects"


def load_subject_config(subject: str) -> dict:
    file_path = _SUBJECTS_DIR / _filename(subject)

    if not file_path.exists():
        raise FileNotFoundError(f"no config found for subject '{subject}' (expected {file_path})")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _filename(subject: str) -> str:
    if not subject:
        raise Exception("subject can not be empty")

    return subject.strip().lower().replace(" ", "_") + ".json"
