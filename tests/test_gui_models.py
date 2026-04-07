from __future__ import annotations

from datetime import date

from opentasks.models import ChecklistItemData, TaskData


class TestTaskData:
    def test_default_fields(self):
        task = TaskData("Buy milk")
        assert task.title == "Buy milk"
        assert task.notes == ""
        assert task.checklist == []
        assert task.tags == []
        assert task.due_date is None
        assert task.project is None
        assert task.flagged is False

    def test_all_fields(self):
        checklist = [ChecklistItemData("Sub-item")]
        task = TaskData(
            title="Review PRs",
            notes="Check conflicts",
            checklist=checklist,
            tags=["work", "urgent"],
            due_date=date(2026, 4, 7),
            project="Dev Project",
            flagged=True,
        )
        assert task.title == "Review PRs"
        assert task.notes == "Check conflicts"
        assert task.checklist == checklist
        assert task.tags == ["work", "urgent"]
        assert task.due_date == date(2026, 4, 7)
        assert task.project == "Dev Project"
        assert task.flagged is True

    def test_tags_default_is_empty_list(self):
        task1 = TaskData("A")
        task2 = TaskData("B")
        task1.tags.append("x")
        assert task2.tags == []

    def test_due_date_display_today(self):
        task = TaskData("X", due_date=date.today())
        assert task.due_date_display() == "Today"

    def test_due_date_display_tomorrow(self):
        tomorrow = date.today().replace(day=date.today().day + 1)
        task = TaskData("X", due_date=tomorrow)
        assert task.due_date_display() == "Tomorrow"

    def test_due_date_display_other(self):
        task = TaskData("X", due_date=date(2026, 12, 25))
        assert task.due_date_display() == "Dec 25"

    def test_due_date_display_none(self):
        task = TaskData("X")
        assert task.due_date_display() == ""

    def test_has_metadata_false(self):
        task = TaskData("X")
        assert task.has_metadata() is False

    def test_has_metadata_tags(self):
        task = TaskData("X", tags=["work"])
        assert task.has_metadata() is True

    def test_has_metadata_due_date(self):
        task = TaskData("X", due_date=date.today())
        assert task.has_metadata() is True

    def test_has_metadata_project(self):
        task = TaskData("X", project="Dev")
        assert task.has_metadata() is True

    def test_has_metadata_flagged(self):
        task = TaskData("X", flagged=True)
        assert task.has_metadata() is True
