from __future__ import annotations

import importlib.resources as pkg_resources
from pathlib import Path


def _res(filename: str) -> str:
    path = Path(str(pkg_resources.files("opentasks") / "resources" / filename))
    return str(path).replace("\\", "/")


STYLES = """
    * {
        font-family: ".AppleSystemUIFont", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    #sidebar {
        background-color: #1E1E1E;
    }

    #navList {
        background: transparent;
        border: none;
        outline: none;
    }
    #navList::item {
        color: #D1D1D1;
        padding: 8px 12px;
        margin-bottom: 4px;
        border-radius: 6px;
        font-size: 14px;
    }
    #navList::item:hover {
        background-color: #2A2A2A;
    }
    #navList::item:selected {
        background-color: #4A90D9;
        color: white;
        font-weight: 500;
    }

    #contentArea {
        background-color: #FFFFFF;
    }

    #headerLabel {
        font-size: 28px;
        font-weight: bold;
        color: #222222;
    }

    #headerIcon {
        font-size: 24px;
    }

    #taskEditor {
        background-color: #FFFFFF;
        border-radius: 12px;
    }

    #modalOverlay {
        background-color: rgba(0, 0, 0, 0.3);
    }

    #inlineTaskEditor {
        background-color: #FFFFFF;
        border-radius: 8px;
    }

    #editorTitleInput, #inlineEditorTitleInput {
        border: none;
        background: transparent;
        font-size: 15px;
        color: #333333;
        padding: 0px;
        selection-background-color: #4A90D9;
        selection-color: white;
    }

    #editorNotesInput, #inlineEditorNotesInput {
        border: none;
        background: transparent;
        font-size: 13px;
        color: #666666;
        padding: 4px;
        selection-background-color: #4A90D9;
        selection-color: white;
    }

    #editorActionButton {
        background: transparent;
        border: none;
        border-radius: 4px;
        font-size: 14px;
        color: #888888;
    }
    #editorActionButton:hover {
        background-color: #F0F0F0;
    }

    #taskList {
        background: transparent;
        border: none;
        outline: none;
    }
    #taskList::item {
        background: transparent;
        border: none;
        border-bottom: 1px solid #F0F0F0;
        margin-bottom: 0px;
    }
    #taskList::item:hover {
        background-color: #F8F8F8;
    }
    #taskList::item:selected {
        background-color: #EDF4FC;
    }

    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid #C0C0C0;
        background-color: transparent;
    }
    QCheckBox::indicator:hover {
        border: 1px solid #4A90D9;
    }
    QCheckBox::indicator:checked {
        background-color: #4A90D9;
        border: 1px solid #4A90D9;
        image: url(%%CHECKMARK%%);
    }
    QCheckBox::indicator:disabled {
        border: 1px solid #D0D0D0;
    }

    #bottomToolbar {
        background-color: #2A2A2A;
        border-top: 1px solid #3A3A3A;
    }

    #addButton {
        background-color: #4A90D9;
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 20px;
        font-weight: bold;
    }
    #addButton:hover {
        background-color: #5A9FE8;
    }
    #addButton:pressed {
        background-color: #3A80C9;
    }

    #toolbarButton {
        background-color: transparent;
        color: #A0A0A0;
        border: none;
        border-radius: 6px;
        font-size: 16px;
    }
    #toolbarButton:hover {
        background-color: #3A3A3A;
        color: #FFFFFF;
    }
    #toolbarButton:pressed {
        background-color: #4A4A4A;
    }

    #checklistWidget {
        background: transparent;
    }

    #checklistItemsContainer {
        background: transparent;
    }

    #checklistItemWidget QCheckBox::indicator {
        width: 14px;
        height: 14px;
        border-radius: 7px;
        border: 1.5px solid #4A90D9;
        background-color: transparent;
    }
    #checklistItemWidget QCheckBox::indicator:hover {
        border: 1.5px solid #5A9FE8;
        background-color: rgba(74, 144, 217, 0.1);
    }
    #checklistItemWidget QCheckBox::indicator:checked {
        background-color: #4A90D9;
        border: 1.5px solid #4A90D9;
    }

    #checklistItemInput {
        border: none;
        background: transparent;
        font-size: 14px;
        color: #333333;
        padding: 4px 0px;
    }

    #checklistGripBtn {
        background: transparent;
        color: #CCCCCC;
        font-size: 16px;
    }

    #checklistDeleteBtn {
        background: transparent;
        border: none;
        color: #999999;
        font-size: 16px;
        font-weight: bold;
    }
    #checklistDeleteBtn:hover {
        color: #CC6666;
    }

    #checklistAddBtn {
        background: transparent;
        border: none;
        color: #4A90D9;
        font-size: 13px;
        text-align: left;
        padding: 4px 8px;
    }
    #checklistAddBtn:hover {
        color: #5A9FE8;
        background-color: #F0F0F0;
        border-radius: 4px;
    }

    #checklistIndicator {
        color: #888888;
        font-size: 12px;
        margin-left: 8px;
    }

    #taskTitle {
        font-size: 15px;
        color: #333333;
    }

    #taskNotes {
        font-size: 12px;
        color: #999999;
    }

    #taskTag {
        font-size: 11px;
        color: #4A90D9;
        background-color: rgba(74, 144, 217, 0.1);
        border-radius: 3px;
        padding: 1px 6px;
    }

    #taskDueDate {
        font-size: 11px;
        color: #888888;
    }

    #taskProject {
        font-size: 11px;
        color: #AAAAAA;
    }

    #taskFlag {
        font-size: 11px;
        color: #E8833A;
    }
""".replace("%%CHECKMARK%%", _res("checkmark.svg"))
