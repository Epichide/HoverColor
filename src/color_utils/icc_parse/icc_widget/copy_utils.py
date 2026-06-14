"""Shared copy helpers for ICC inspector table-like widgets.

The helpers install Ctrl+C support for QTableWidget and QTreeWidget. Copied
content is formatted as tab-separated text so it can be pasted into Excel,
spreadsheets, or plain text editors.
"""

from typing import List

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QShortcut, QTableWidget, QTreeWidget


def install_copy_shortcut(view) -> None:
    """Install Ctrl+C copy support on a table or tree widget.

    Args:
        view: QTableWidget or QTreeWidget instance.

    Returns:
        None. The QShortcut is stored on the widget to keep it alive.
    """
    shortcut = QShortcut(QKeySequence.Copy, view)
    shortcut.activated.connect(lambda: copy_selection_to_clipboard(view))
    view._copy_shortcut = shortcut


def copy_selection_to_clipboard(view) -> None:
    """Copy the current selection from a supported widget to the clipboard."""
    if isinstance(view, QTableWidget):
        text = _table_selection_to_tsv(view)
    elif isinstance(view, QTreeWidget):
        text = _tree_selection_to_tsv(view)
    else:
        text = ""

    if text:
        QApplication.clipboard().setText(text)


def _table_selection_to_tsv(table: QTableWidget) -> str:
    """Convert QTableWidget selected cells to TSV text."""
    selected_ranges = table.selectedRanges()
    if not selected_ranges and table.currentItem() is not None:
        return _cell_text(table.currentItem())

    blocks = []
    for selected_range in selected_ranges:
        lines = []
        for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
            values = []
            for column in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                values.append(_cell_text(table.item(row, column)))
            lines.append("\t".join(values))
        blocks.append("\n".join(lines))
    return "\n".join(block for block in blocks if block)


def _tree_selection_to_tsv(tree: QTreeWidget) -> str:
    """Convert QTreeWidget selected cells or rows to TSV text."""
    indexes = tree.selectedIndexes()
    if indexes:
        return _tree_indexes_to_tsv(tree, indexes)

    current_item = tree.currentItem()
    if current_item is None:
        return ""
    return "\t".join(current_item.text(column) for column in range(tree.columnCount()))


def _tree_indexes_to_tsv(tree: QTreeWidget, indexes) -> str:
    """Group selected tree indexes by row item and serialize selected columns."""
    grouped = {}
    for index in indexes:
        item = tree.itemFromIndex(index)
        if item is None:
            continue
        grouped.setdefault(item, {})[index.column()] = item.text(index.column())

    lines: List[str] = []
    for item, columns in grouped.items():
        if len(columns) == 1:
            lines.append(next(iter(columns.values())))
        else:
            max_column = tree.columnCount()
            lines.append("\t".join(item.text(column) for column in range(max_column)))
    return "\n".join(lines)


def _cell_text(item) -> str:
    """Return safe cell text for a QTableWidgetItem-like value."""
    return "" if item is None else item.text()
