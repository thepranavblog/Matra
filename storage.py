"""
storage.py — Simple JSON file storage for Mātra prototype.

Each user gets their own JSON file in the /data directory.
Good enough for 50–100 beta users. Swap for Supabase/Firebase when scaling.
"""

import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def _user_path(user_id: str) -> Path:
    return DATA_DIR / f"{user_id}.json"


def load_user(user_id: str) -> dict:
    path = _user_path(user_id)
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {}


def save_user(user_id: str, data: dict):
    with open(_user_path(user_id), "w") as f:
        json.dump(data, f, indent=2)


def append_history(user_id: str, entry: dict):
    """Append a meal or workout log entry to the user's history."""
    user = load_user(user_id)
    if "history" not in user:
        user["history"] = []
    user["history"].append(entry)
    # Keep last 90 entries to avoid unbounded growth
    user["history"] = user["history"][-90:]
    save_user(user_id, user)


def get_today_logs(user_id: str) -> list:
    """Return all logs from today."""
    from datetime import datetime, date
    user = load_user(user_id)
    today = date.today().isoformat()
    return [
        entry for entry in user.get("history", [])
        if entry.get("timestamp", "").startswith(today)
    ]
