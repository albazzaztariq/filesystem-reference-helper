"""
snippet.py - CLI for managing FRH snippets.

Usage:
    python snippet.py add NAME --file content.txt
    python snippet.py add NAME "inline content here"
    python snippet.py list
    python snippet.py show NAME
    python snippet.py delete NAME
    python snippet.py edit NAME        (opens in Notepad)
    python snippet.py store            (show store file path)
"""

import sys
import os
import re
import subprocess
import tempfile
from pathlib import Path

import snippet_store as store

NAME_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')


def validate_name(name: str) -> str:
    """Uppercase and validate. Returns clean name or exits."""
    clean = name.strip().upper()
    if not NAME_RE.match(clean):
        print(f"[ERROR] Invalid snippet name '{name}'.")
        print("        Names must start with a letter and contain only A-Z, 0-9, _")
        sys.exit(1)
    return clean


def cmd_add(args):
    if len(args) < 1:
        print("Usage: snippet add NAME [\"inline content\" | --file path]")
        sys.exit(1)

    name    = validate_name(args[0])
    rest    = args[1:]

    if not rest:
        # No content supplied — open Notepad for input
        print(f"No content supplied. Opening Notepad to write snippet '{name}'...")
        cmd_edit_new(name)
        return

    if rest[0] == "--file":
        if len(rest) < 2:
            print("[ERROR] --file requires a path argument")
            sys.exit(1)
        fpath = Path(rest[1])
        if not fpath.exists():
            print(f"[ERROR] File not found: {fpath}")
            sys.exit(1)
        content = fpath.read_text(encoding="utf-8")
    else:
        content = " ".join(rest)

    existing = store.get(name)
    store.add(name, content)

    if existing is not None:
        print(f"Updated snippet '{name}' ({len(content)} chars)")
    else:
        print(f"Added snippet '{name}' ({len(content)} chars)")


def cmd_edit_new(name: str):
    """Create new snippet via Notepad."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(f"# Write content for snippet: {name}\n")
        f.write("# Delete this comment line before saving.\n\n")
        tmp = f.name

    subprocess.run(["notepad.exe", tmp])

    content = Path(tmp).read_text(encoding="utf-8")
    # Strip comment lines
    lines = [l for l in content.splitlines() if not l.startswith("#")]
    content = "\n".join(lines).strip()
    os.unlink(tmp)

    if not content:
        print("[CANCELLED] No content saved.")
        return

    store.add(name, content)
    print(f"Saved snippet '{name}' ({len(content)} chars)")


def cmd_edit(args):
    if not args:
        print("Usage: snippet edit NAME")
        sys.exit(1)

    name    = validate_name(args[0])
    content = store.get(name)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        if content:
            f.write(content)
        else:
            f.write(f"# New snippet: {name}\n\n")
        tmp = f.name

    subprocess.run(["notepad.exe", tmp])

    new_content = Path(tmp).read_text(encoding="utf-8").strip()
    os.unlink(tmp)

    if not new_content:
        print("[CANCELLED] Empty content — snippet not changed.")
        return

    store.add(name, new_content)
    print(f"Saved snippet '{name}' ({len(new_content)} chars)")


def cmd_list(_args):
    snippets = store.list_all()
    if not snippets:
        print("No snippets stored.")
        print(f"Store: {store.store_path()}")
        return

    print(f"\n{len(snippets)} snippet(s)  [{store.store_path()}]\n")
    name_w = max(len(n) for n in snippets)
    for name, content in sorted(snippets.items()):
        preview = content.replace("\n", " ").strip()
        if len(preview) > 60:
            preview = preview[:57] + "..."
        print(f"  {{{{ {name:<{name_w}} }}}}   {preview}")
    print()


def cmd_show(args):
    if not args:
        print("Usage: snippet show NAME")
        sys.exit(1)

    name    = validate_name(args[0])
    content = store.get(name)

    if content is None:
        print(f"[ERROR] No snippet named '{name}'")
        sys.exit(1)

    print(f"\n--- {name} ({len(content)} chars) ---\n")
    print(content)
    print(f"\n--- end ---\n")


def cmd_delete(args):
    if not args:
        print("Usage: snippet delete NAME")
        sys.exit(1)

    name = validate_name(args[0])

    if not store.delete(name):
        print(f"[ERROR] No snippet named '{name}'")
        sys.exit(1)

    print(f"Deleted snippet '{name}'")


def cmd_store(_args):
    print(store.store_path())


COMMANDS = {
    "add":    cmd_add,
    "edit":   cmd_edit,
    "list":   cmd_list,
    "show":   cmd_show,
    "delete": cmd_delete,
    "store":  cmd_store,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: snippet <command> [args]")
        print()
        print("Commands:")
        print("  add NAME [\"content\" | --file path]   add or overwrite a snippet")
        print("  edit NAME                             open snippet in Notepad")
        print("  list                                  list all snippets")
        print("  show NAME                             print full content")
        print("  delete NAME                           remove a snippet")
        print("  store                                 show store file location")
        sys.exit(1)

    cmd  = sys.argv[1]
    args = sys.argv[2:]
    COMMANDS[cmd](args)


if __name__ == "__main__":
    main()
