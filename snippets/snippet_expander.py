"""
snippet_expander.py - File watcher daemon that expands {{SNIPPET_NAME}} in files.

When a watched file is saved and contains {{SNIPPET_NAME}}, the placeholder is
replaced in-place with the stored snippet content. The replacement is permanent —
the placeholder is consumed on save.

Watches configured directories for the configured file extensions.
Config lives at ~/.frh/expander_config.json:
{
  "watch_dirs": ["C:/Projects", "C:/Notes"],
  "extensions": [".py", ".js", ".txt", ".md"]
}

Requires: pip install watchdog
"""

import json
import logging
import re
import sys
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import snippet_store as store

CONFIG_FILE = Path.home() / ".frh" / "expander_config.json"
LOG_FILE    = Path.home() / ".frh" / "snippet_expander.log"

SNIPPET_RE  = re.compile(r'\{\{([A-Z][A-Z0-9_]*)\}\}')

DEFAULT_CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
    ".cs", ".cpp", ".c", ".h", ".rs", ".rb", ".php", ".swift",
    ".kt", ".scala", ".r", ".lua", ".sh", ".bat", ".ps1",
}
DEFAULT_TEXT_EXTENSIONS = {
    ".txt", ".md", ".log", ".csv", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".conf",
}


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {"watch_dirs": [], "extensions": list(DEFAULT_CODE_EXTENSIONS)}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


class SnippetExpanderHandler(FileSystemEventHandler):
    def __init__(self, extensions: set):
        self.extensions = extensions
        self._expanding: set = set()   # files we are currently writing (avoid re-trigger)
        self._lock = threading.Lock()

    def on_modified(self, event):
        if event.is_directory:
            return
        path = str(event.src_path)
        ext  = Path(path).suffix.lower()
        if ext not in self.extensions:
            return
        with self._lock:
            if path in self._expanding:
                return
        self._expand_file(path)

    def _expand_file(self, path: str):
        try:
            content = Path(path).read_text(encoding="utf-8")
        except Exception as e:
            logging.debug(f"Read error {path}: {e}")
            return

        matches = SNIPPET_RE.findall(content)
        if not matches:
            return

        new_content = content
        expanded    = []
        missing     = []

        for name in dict.fromkeys(matches):   # preserve order, deduplicate
            snippet = store.get(name)
            if snippet is not None:
                new_content = new_content.replace(f"{{{{{name}}}}}", snippet)
                expanded.append(name)
            else:
                missing.append(name)

        if missing:
            logging.warning(f"{Path(path).name}: unknown snippet(s): {missing}")

        if new_content == content:
            return

        with self._lock:
            self._expanding.add(path)

        try:
            Path(path).write_text(new_content, encoding="utf-8")
            logging.info(f"Expanded {expanded} in {Path(path).name}")
        except Exception as e:
            logging.error(f"Write error {path}: {e}")
        finally:
            # Small delay so the write event fires and is ignored before we unregister
            threading.Timer(0.5, lambda: self._expanding.discard(path)).start()


def main():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )

    logging.info("[DEBUG] snippet_expander starting")

    cfg        = load_config()
    watch_dirs = cfg.get("watch_dirs", [])
    extensions = set(cfg.get("extensions", list(DEFAULT_CODE_EXTENSIONS)))

    if not watch_dirs:
        logging.warning("No watch_dirs configured. Add directories to ~/.frh/expander_config.json")
        logging.warning("  Example: {\"watch_dirs\": [\"C:/Projects\"], \"extensions\": [\".py\", \".md\"]}")

    snippets = store.list_all()
    logging.info(f"Loaded {len(snippets)} snippet(s) from store")
    logging.info(f"Watching extensions: {sorted(extensions)}")

    handler  = SnippetExpanderHandler(extensions)
    observer = Observer()

    for d in watch_dirs:
        p = Path(d)
        if not p.exists():
            logging.warning(f"Watch dir does not exist, skipping: {d}")
            continue
        observer.schedule(handler, str(p), recursive=True)
        logging.info(f"Watching: {d}")

    observer.start()
    logging.info("snippet_expander running\n")

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        logging.info("snippet_expander stopping")

    observer.stop()
    observer.join()
    logging.info("snippet_expander stopped")


if __name__ == "__main__":
    main()
