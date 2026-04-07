# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

opentasks is a cross-platform Things 3 alternative built with PySide6 (Qt). It includes a Things Cloud sync protocol parser that fetches and reconstructs task state from cloud history deltas.

## Common Commands

| Action | Command |
|---|---|
| Run GUI | `uv run python -m opentasks.app` |
| Run tests with coverage | `uv run pytest tests/ --cov=opentasks --cov-report=term-missing` |
| Run single test | `uv run pytest tests/test_parser.py::test_name -v` |
| Lint | `uv run ruff check opentasks/ tests/` |
| Format check | `uv run ruff format --check opentasks/ tests/` |
| Format fix | `uv run ruff format opentasks/ tests/` |
| Install deps | `uv sync --extra dev` |

Taskfile shortcuts: `task tests`, `task run`

## Architecture

**GUI layer** (`opentasks/`): PySide6 desktop app with sidebar navigation (Inbox, Today, Upcoming, Anytime, Someday, Logbook) and a content area for task management. `app.py` is the entry point (`MainWindow`). Widgets are split across `task_widgets.py` (TaskItem, TaskEditor, InlineTaskEditor), `task_list.py` (TaskListWidget with drag-drop), `checklist.py`, and `buttons.py`. Styles live in `styles.py`.

**Data models** (`opentasks/models.py`): `TaskData` and `ChecklistItemData` — GUI-facing data containers.

**Things Cloud layer** (`opentasks/things/`):
- `cloud.py` — HTTP client (`CloudAPI`) for Things Cloud sync protocol using custom auth handlers
- `models.py` — Typed dataclasses for 6 entity types (Task6, ChecklistItem3, Area3, Tag4, Settings5, Tombstone2) with enums for Status, StartType, TaskType
- `parser.py` — `StateBuilder` applies history deltas (full snapshots + incremental updates, including byte-level note patches) to reconstruct a `State` object with query methods (`projects`, `todos`, `open_tasks`, `tasks_for_project()`, etc.)

**Utility** (`compare.py`): CLI tool comparing Things Cloud state vs local Things.app database.

## Code Style

- Python >= 3.11; use `from __future__ import annotations`
- Built-in generics: `dict[str, Any]`, `list[str]` (not `typing.Dict`)
- Pipe unions: `str | None` (not `Optional[str]`)
- Ruff with default settings, line length 88
- Minimal comments — code should be self-explanatory

## CI

GitHub Actions runs on push/PR: tests across Python 3.11–3.14, ruff lint + format check. Coverage uploaded to Codecov on 3.14.
