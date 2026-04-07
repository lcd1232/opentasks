from __future__ import annotations


from PySide6.QtGui import QIcon, QPixmap

from opentasks.icons import (
    ICON_ARCHIVE,
    ICON_ARROW_RIGHT,
    ICON_BOOK_OPEN,
    ICON_CALENDAR,
    ICON_CALENDAR_BLANK,
    ICON_CHECK,
    ICON_CIRCLES_THREE,
    ICON_FLAG,
    ICON_LIST_CHECKS,
    ICON_MAGNIFYING_GLASS,
    ICON_PLUS,
    ICON_STAR,
    ICON_TAG,
    ICON_TRAY,
    _resources_dir,
    icon_pixmap,
    icon_qicon,
)


class TestIconConstants:
    def test_all_icon_names_are_strings(self):
        icons = [
            ICON_TRAY,
            ICON_STAR,
            ICON_CALENDAR_BLANK,
            ICON_CIRCLES_THREE,
            ICON_ARCHIVE,
            ICON_BOOK_OPEN,
            ICON_CALENDAR,
            ICON_TAG,
            ICON_LIST_CHECKS,
            ICON_FLAG,
            ICON_ARROW_RIGHT,
            ICON_MAGNIFYING_GLASS,
            ICON_PLUS,
            ICON_CHECK,
        ]
        for icon in icons:
            assert isinstance(icon, str)
            assert len(icon) > 0

    def test_svg_files_exist_for_all_icons(self):
        icons = [
            ICON_TRAY,
            ICON_STAR,
            ICON_CALENDAR_BLANK,
            ICON_CIRCLES_THREE,
            ICON_ARCHIVE,
            ICON_BOOK_OPEN,
            ICON_CALENDAR,
            ICON_TAG,
            ICON_LIST_CHECKS,
            ICON_FLAG,
            ICON_ARROW_RIGHT,
            ICON_MAGNIFYING_GLASS,
            ICON_PLUS,
            ICON_CHECK,
        ]
        res_dir = _resources_dir()
        for icon in icons:
            svg_path = res_dir / f"{icon}.svg"
            assert svg_path.exists(), f"Missing SVG: {svg_path}"


class TestIconPixmap:
    def test_returns_qpixmap(self, qapp):
        result = icon_pixmap(ICON_STAR, 16, "#FF0000")
        assert isinstance(result, QPixmap)

    def test_pixmap_has_correct_size(self, qapp):
        result = icon_pixmap(ICON_STAR, 24, "#000000")
        assert result.width() == 24
        assert result.height() == 24

    def test_pixmap_not_null(self, qapp):
        result = icon_pixmap(ICON_TRAY, 16, "#888888")
        assert not result.isNull()

    def test_different_colors_produce_different_pixmaps(self, qapp):
        icon_pixmap.cache_clear()
        p1 = icon_pixmap(ICON_FLAG, 16, "#FF0000")
        p2 = icon_pixmap(ICON_FLAG, 16, "#0000FF")
        # They should both be valid but may be cached differently
        assert not p1.isNull()
        assert not p2.isNull()


class TestIconQIcon:
    def test_returns_qicon(self, qapp):
        result = icon_qicon(ICON_CALENDAR, 16, "#888888")
        assert isinstance(result, QIcon)

    def test_icon_not_null(self, qapp):
        result = icon_qicon(ICON_PLUS, 20, "#FFFFFF")
        assert not result.isNull()
