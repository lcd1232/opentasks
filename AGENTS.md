# AGENTS.md — opentasks

Things3 Cloud sync protocol parser. Fetches history from Things Cloud API,
reconstructs final object state by applying full snapshots (`t=0`) and
delta patches (`t=1`), including UTF-8 byte-offset note patching.

## Quick Reference

| Action | Command |
|---|---|
| Run script | `uv run python3 <file>` |
| Lint | `ruff check src/ compare.py` |
| Format check | `ruff format --check src/ compare.py` |
| Format fix | `ruff format src/ compare.py` |
| Compare (cached files) | `uv run python3 compare.py` |
| Compare (live API) | `uv run python3 compare.py --live` |

No test framework is configured. No CI pipeline exists.

## Project Layout

```
src/
  cloud.py      # Things Cloud API client (auth, history fetch)
  models.py     # Typed dataclasses for all 6 entity types
  parser.py     # StateBuilder: applies history deltas → final State
  app.py        # PySide6 GUI (placeholder, not part of core logic)
compare.py      # CLI tool comparing cloud state vs local Things DB
history_*.json  # Cached API responses (do NOT commit, too large)
src/.env        # Credentials (THINGS_EMAIL, THINGS_PASSWORD) — never read or commit
```

## Architecture

```
CloudAPI.full_history()          →  list[HistoryResponse]
    ↓
StateBuilder.apply_all(responses) →  merges t=0 (full) + t=1 (delta)
    ↓
StateBuilder.build()             →  State (tasks, areas, tags, checklist_items, ...)
```

### Entity Types

| Protocol Name | Model Class | Notes |
|---|---|---|
| `Task6` | `Task` | `tp`: 0=task, 1=project, 2=heading |
| `ChecklistItem3` | `ChecklistItem` | `ts` = parent task UUIDs |
| `Area3` | `Area` | |
| `Tag4` | `Tag` | |
| `Settings5` | `Settings` | |
| `Tombstone2` | `Tombstone` | Marks deleted objects |

### Key Enums

| Enum | Field | Values |
|---|---|---|
| `StartType` | `st` | 0=Inbox, 1=Anytime, 2=Someday |
| `Status` | `ss` | 0=Open, 2=Cancelled, 3=Completed |
| `TaskType` | `tp` | 0=Task, 1=Project, 2=Heading |

### Delta Patching (Critical)

- `t=0`: Full object — replace all properties
- `t=1`: Delta — merge only provided properties into existing object
- `nt` field (notes) with `nt.t=2`: Incremental text patch, NOT replacement
  - `ps` array: each patch has `p` (UTF-8 byte offset), `l` (delete length), `r` (replacement)
  - Positions are **UTF-8 byte offsets**, not character indices

## Code Style

### Python Version
- Requires Python >= 3.11
- Use `from __future__ import annotations` in every file

### Typing
- Use built-in generics: `dict[str, Any]`, `list[str]` (not `typing.Dict`)
- Use pipe unions: `str | None` (not `Optional[str]`)
- Annotate all function parameters and return types
- Use `TYPE_CHECKING` guard for imports only needed by type checkers

### Naming
- Classes: `PascalCase` (`StateBuilder`, `HistoryResponse`)
- Functions/methods: `snake_case` (`apply_delta`, `from_raw`)
- Constants: `UPPER_SNAKE_CASE` (`ENTITY_TYPE_TO_MODEL`, `TASK_FIELDS`)
- Private: single underscore prefix (`_apply_delta`, `_objects`)

### Imports
Three groups separated by blank lines:
1. Standard library (`import json`, `from dataclasses import dataclass`)
2. Third-party (`import httpx`, `from dataclasses_json import config`)
3. Local (`from src.cloud import HistoryResponse`)

### Formatting
- Ruff with default settings (no custom config)
- Line length: 88 (ruff default)
- f-strings for all interpolation
- `!r` in debug/comparison output

### Classes
- Data models: `@dataclass` (plain, not attrs/pydantic)
- Cloud API models: `@dataclass_json` + `@dataclass` with `field(metadata=config(field_name=...))`
- Each model has a `from_raw(uuid, props)` classmethod for construction from raw dicts
- Logic classes: plain classes (`CloudAPI`, `StateBuilder`)

### Comments
- Minimal. Code should be self-explanatory.
- Comments allowed for: reverse-engineered protocol field mappings, enum value meanings
- No docstrings on private methods or obvious functions
- Module-level docstrings only when file purpose is non-obvious

### Error Handling
- API errors: `response.raise_for_status()` — let httpx exceptions propagate
- Missing data: return `None` (e.g., `NoteContent.from_raw(None) → None`)
- No bare `except:` or empty `catch` blocks

## Things You Must Know

- The `.env` file lives at `src/.env`, not project root
- `HistoryObject.t` is an `int` (0 or 1), not a string
- `dataclasses_json` adds `from_json`/`to_json` at runtime — type checkers
  will report false errors on these methods. This is expected.
- `environ` type inference is imprecise — `env.str()` returns `Unknown | NoValue | None`
  per the type checker. These are pre-existing false positives.
- `src/app.py` is an unrelated PySide6 placeholder — ignore its lint errors
- History JSON files are large (600KB–1.7MB each). Never read them fully in context.
