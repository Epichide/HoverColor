"""Shared table UI helpers for ICC inspector widgets.

The helpers keep tables readable by allowing cell-level selection and fitting
column widths to the visible viewport using content-based proportions.
"""

from typing import Optional, Sequence

from PyQt5.QtCore import QObject, QEvent, Qt, QTimer
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTreeWidget


def configure_content_fit_table(
    table: QTableWidget,
    min_widths: Optional[Sequence[int]] = None,
    max_widths: Optional[Sequence[int]] = None,
) -> None:
    """Configure a read-only table for cell selection and adaptive columns.

    Args:
        table: QTableWidget to configure.
        min_widths: Optional per-column minimum widths.
        max_widths: Optional per-column soft maximum widths used before extra
            space is distributed.
    """
    table.setSelectionBehavior(QAbstractItemView.SelectItems)
    table.setSelectionMode(QAbstractItemView.ExtendedSelection)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    header = table.horizontalHeader()
    header.setStretchLastSection(False)
    for column in range(table.columnCount()):
        header.setSectionResizeMode(column, QHeaderView.Interactive)

    controller = AdaptiveColumnWidthController(table, min_widths=min_widths, max_widths=max_widths)
    table._adaptive_column_width_controller = controller
    table.installEventFilter(controller)
    QTimer.singleShot(0, controller.fit_columns)


def refit_table_columns(table: QTableWidget) -> None:
    """Refit table columns when table content changes."""
    controller = getattr(table, "_adaptive_column_width_controller", None)
    if controller is not None:
        QTimer.singleShot(0, controller.fit_columns)


def configure_copyable_tree(tree: QTreeWidget, select_items: bool = True) -> None:
    """Configure a tree widget for selecting and copying visible cells.

    Args:
        tree: QTreeWidget to configure.
        select_items: Select individual cells when True, otherwise whole rows.
    """
    behavior = QAbstractItemView.SelectItems if select_items else QAbstractItemView.SelectRows
    tree.setSelectionBehavior(behavior)
    tree.setSelectionMode(QAbstractItemView.ExtendedSelection)


class AdaptiveColumnWidthController(QObject):
    """Resize table columns based on content while filling the viewport."""

    def __init__(
        self,
        table: QTableWidget,
        min_widths: Optional[Sequence[int]] = None,
        max_widths: Optional[Sequence[int]] = None,
    ):
        """Initialize the controller."""
        super().__init__(table)
        self.table = table
        self.min_widths = list(min_widths or [])
        self.max_widths = list(max_widths or [])

    def eventFilter(self, watched, event) -> bool:
        """Refit columns after table resize/show events."""
        if watched is self.table and event.type() in (QEvent.Resize, QEvent.Show):
            QTimer.singleShot(0, self.fit_columns)
        return False

    def fit_columns(self) -> None:
        """Fit all columns into the table viewport using content proportions."""
        table = self.table
        column_count = table.columnCount()
        if column_count <= 0:
            return

        available_width = max(1, table.viewport().width() - 2)
        min_widths = [self._min_width(column) for column in range(column_count)]
        ideal_widths = [self._ideal_width(column, min_widths[column]) for column in range(column_count)]
        fitted_widths = _fit_widths_to_available(ideal_widths, min_widths, available_width)

        for column, width in enumerate(fitted_widths):
            table.setColumnWidth(column, max(1, int(round(width))))

    def _min_width(self, column: int) -> int:
        """Return minimum width for one column."""
        if column < len(self.min_widths):
            return self.min_widths[column]
        return 70

    def _max_width(self, column: int) -> int:
        """Return soft maximum width for one column."""
        if column < len(self.max_widths):
            return self.max_widths[column]
        return 420

    def _ideal_width(self, column: int, min_width: int) -> int:
        """Return content-based ideal width capped by a soft maximum."""
        table = self.table
        header_text = table.horizontalHeaderItem(column).text() if table.horizontalHeaderItem(column) else ""
        header_width = table.fontMetrics().horizontalAdvance(header_text) + 28
        content_width = table.sizeHintForColumn(column)
        if content_width <= 0:
            content_width = header_width
        ideal_width = max(header_width, content_width, min_width)
        return min(ideal_width, self._max_width(column))


def _fit_widths_to_available(ideal_widths: Sequence[int], min_widths: Sequence[int], available_width: int) -> list:
    """Scale ideal widths into available viewport width."""
    if not ideal_widths:
        return []

    min_total = sum(min_widths)
    if min_total >= available_width:
        # View is very narrow; scale minima to avoid a horizontal scrollbar.
        ratio = available_width / max(min_total, 1)
        return [max(1, width * ratio) for width in min_widths]

    ideal_total = sum(ideal_widths)
    if ideal_total == available_width:
        return list(ideal_widths)

    if ideal_total > available_width:
        shrinkable = [max(0, ideal - minimum) for ideal, minimum in zip(ideal_widths, min_widths)]
        shrink_total = sum(shrinkable)
        overflow = ideal_total - available_width
        if shrink_total <= 0:
            return list(min_widths)
        return [
            ideal - overflow * (shrink / shrink_total)
            for ideal, shrink in zip(ideal_widths, shrinkable)
        ]

    extra = available_width - ideal_total
    weight_total = sum(ideal_widths)
    return [
        ideal + extra * (ideal / weight_total)
        for ideal in ideal_widths
    ]
