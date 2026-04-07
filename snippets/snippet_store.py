"""
snippet_store.py - Storage layer for the FRH snippet system.

Snippets are stored in ~/.frh/snippets.json as:
  { "SNIPPET_NAME": "full text content...", ... }

No length limit. Content can be multi-line.
Referenced in files as {{SNIPPET_NAME}}.
"""

import json
import os
from pathlib import Path

STORE_DIR  = Path.home() / ".frh"
STORE_FILE = STORE_DIR / "snippets.json"


def _load() -> dict:
    if not STORE_FILE.exists():
        return {}
    with open(STORE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict):
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add(name: str, content: str):
    """Add or overwrite a snippet."""
    data = _load()
    data[name] = content
    _save(data)


def get(name: str) -> str | None:
    """Return snippet content, or None if not found."""
    return _load().get(name)


def delete(name: str) -> bool:
    """Delete a snippet. Returns True if it existed."""
    data = _load()
    if name not in data:
        return False
    del data[name]
    _save(data)
    return True


def list_all() -> dict:
    """Return all snippets as {name: content}."""
    return _load()


def store_path() -> Path:
    return STORE_FILE
