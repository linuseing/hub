from pathlib import Path


def ensure_path(path):
    Path(path).mkdir(parents=True, exist_ok=True)
