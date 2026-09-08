# AGENTS.md

## Overview

Python CLI that cleans profanity from EPUB files. Derived from [calibre-plugin-language-cleaner](https://github.com/jdanders/calibre-plugin-language-cleaner).

## Run

```sh
uv run src/main.py <path-to-epub>
uv run src/main.py <path-to-epub> -o <output.epub>
```

Defaults to `<stem>_edit.epub` alongside the input file.

## Structure

- `src/main.py` — CLI entrypoint.
- `src/epub_mod.py` — Core EPUB handling. Extracts EPUB (ZIP), applies replacements to all HTML files, re-packages.
- `src/cleaner.py` — Regex-based replacement engine. `language_check()` returns the rule list; rules are context-adaptive based on book content.

## Conventions

- Managed with **uv** (`pyproject.toml` + `uv.lock`). Python 3.12+.
- Tests use **pytest** (`uv run pytest`, config in `pyproject.toml`). Fixtures: EPUBs in `tests/data/` via Git LFS.
- No linter, no typecheck, no CI.
- `cleaner.py` is adapted from an external source. Regex rules are intentionally quirky (e.g. the `zxsa` intermediate for f-words). Edit carefully.
