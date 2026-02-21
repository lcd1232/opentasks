# AGENTS.md — opentasks

Things 3 alternative — cross-platform task management app built with PySide6.
Includes Things Cloud sync protocol parser for fetching and reconstructing task state.

## Quick Reference

| Action | Command |
|---|---|
| Run GUI | `uv run python -m opentasks.app` |
| Run script | `uv run python3 <file>` |
| Lint | `ruff check opentasks/ compare.py` |
| Format check | `ruff format --check opentasks/ compare.py` |
| Format fix | `ruff format opentasks/ compare.py` |

## Project Layout

```
opentasks/
  app.py              # MainWindow + entry point
  models.py           # Data classes (ChecklistItemData, TaskData)
  buttons.py          # EditorActionButton, ToolbarButton
  styles.py           # STYLES constant (Qt stylesheet)
  checklist.py        # ChecklistItemWidget, ChecklistWidget
  task_widgets.py     # TaskItem, TaskEditor, InlineTaskEditor
  task_list.py        # TaskListWidget
  things/
    cloud.py          # Things Cloud API client (auth, history fetch)
    models.py         # Typed dataclasses for all 6 entity types
    parser.py         # StateBuilder: applies history deltas → final State
compare.py            # CLI tool comparing cloud state vs local Things DB
```

## GUI Application (app.py)

### Components

- `MainWindow` — Main window with sidebar + content area
- `TaskListWidget` — Draggable task list with keyboard navigation
- `TaskEditor` — Floating editor for new tasks
- `InlineTaskEditor` — Inline editor for editing existing tasks
- `TaskItem` — Individual task display widget
- `TaskData` — Task data container (title, notes)

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Space` | Create new task below current (or at top if none selected) |
| `Cmd+N` / `Ctrl+N` | Create new task below current |
| `Enter` | Open selected task for editing |
| `Escape` | Cancel edit / Deselect all tasks |
| `Delete` | Delete selected task |
| `↑` / `↓` | Navigate between tasks |

### Task Operations

- **Create**: Click `+` button or use `Space`/`Cmd+N`
- **Edit**: Double-click task or press `Enter`
- **Delete**: Press `Delete` key
- **Reorder**: Drag and drop tasks

## Code Style

- Python >= 3.11, use `from __future__ import annotations`
- Use built-in generics: `dict[str, Any]`, `list[str]`
- Use pipe unions: `str | None`
- Ruff with default settings, line length 88
- Minimal comments, code should be self-explanatory
