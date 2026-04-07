from __future__ import annotations

from datetime import date


class ChecklistItemData:
    def __init__(self, title: str, completed: bool = False, cancelled: bool = False):
        self.title = title
        self.completed = completed
        self.cancelled = cancelled


class TaskData:
    def __init__(
        self,
        title: str,
        notes: str = "",
        checklist: list[ChecklistItemData] | None = None,
        tags: list[str] | None = None,
        due_date: date | None = None,
        project: str | None = None,
        flagged: bool = False,
    ):
        self.title = title
        self.notes = notes
        self.checklist: list[ChecklistItemData] = checklist if checklist else []
        self.tags: list[str] = tags if tags else []
        self.due_date = due_date
        self.project = project
        self.flagged = flagged

    def due_date_display(self) -> str:
        """Return a human-readable string for the due date."""
        if self.due_date is None:
            return ""
        today = date.today()
        if self.due_date == today:
            return "Today"
        delta = (self.due_date - today).days
        if delta == 1:
            return "Tomorrow"
        return self.due_date.strftime("%b %-d")

    def has_metadata(self) -> bool:
        """Return True if any metadata field is set (tags, due_date, project, flagged)."""
        return bool(self.tags or self.due_date or self.project or self.flagged)
