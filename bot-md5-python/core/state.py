import json
from pathlib import Path
from typing import Dict, Any

STORAGE = Path("data.json")


def load_state() -> Dict[str, Any]:
    if not STORAGE.exists():
        return {"history": [], "stats": {"total": 0, "correct": 0, "wrong": 0}, "last_session": None}
    try:
        return json.loads(STORAGE.read_text(encoding="utf-8"))
    except Exception:
        return {"history": [], "stats": {"total": 0, "correct": 0, "wrong": 0}, "last_session": None}


def save_state(state: Dict[str, Any]):
    STORAGE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
