# Filesystem Reference Helper

Keeps path references in sync across your files when folders are renamed or moved. Set a path as an environment variable once — when the folder moves, every reference updates automatically.

Also supports text snippet expansion: define reusable snippets and insert them into any file with `{{SNIPPET_NAME}}`.

## What it does

Without this tool: rename a folder and every hardcoded path in your code, notes, and docs silently breaks.

With this tool: rename the folder, every `%MY_VAR%` reference in your files updates immediately.

## Installation modes

Choose what you want covered during setup:

| Mode | What it watches | Default |
|------|----------------|---------|
| **Code files** | `.py`, `.js`, `.ts`, `.go`, `.java`, `.cs`, `.cpp`, `.rs`, and more | Yes |
| **Text files** | `.txt`, `.md`, `.log`, `.csv`, `.json`, `.yaml`, `.toml`, `.ini` | No — opt-in |

Text file coverage is off by default. This is a beta release and we want code-file coverage solid before expanding scope. You can enable it during setup or at any time by re-running the installer.

You can also install text-file coverage only if that is all you need.

## Features

### Path sync (env vars)

Register a path as an environment variable using **EnvVar Creator**:

```
MY_PROJECT: C:/Projects/MyApp
DATA_DIR: C:/Data/processed
```

Reference it in code:
```python
path = os.environ["MY_PROJECT"]
```

Reference it in text files:
```
See %MY_PROJECT% for the source files.
```

When you rename `C:/Projects/MyApp` to `C:/Projects/MyApp-v2`, the env var updates and every reference stays valid.

### Text snippets (long-form content)

For content too long for an env var (paragraphs, boilerplate, templates), use the snippets store:

```
{{PROJECT_OVERVIEW}}
{{STANDARD_DISCLAIMER}}
{{PIPELINE_DESCRIPTION}}
```

Snippets are stored in a local file, no length limit. The file watcher expands them when you save.

## Components

- **EnvVar Creator** — bulk-create env vars from a plain text file
- **Sync Daemon** — background process that watches for renames and updates references
- **Snippet Store** — manages longer text content with `{{NAME}}` notation

## Status

Beta. Code file coverage is stable. Text file and snippet expansion are in development.
