from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"


def data_path(layer: str, filename: str) -> Path:
    layer_dir = _DATA_DIR / layer
    layer_dir.mkdir(parents=True, exist_ok=True)
    return layer_dir / filename
