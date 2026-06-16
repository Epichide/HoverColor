"""ICC Summary tab widget for the ICC inspector GUI.

The widget displays high-value ICC profile information extracted from parsed
data. It also marks rows that can later be connected to double-click
visualizations for curves, LUTs, matrices, and illuminants.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

try:
    from icc_summary_extract import build_icc_summary
    from icc_widget.copy_utils import install_copy_shortcut
    from icc_widget.conversion_chain_widget import _create_curve_plot
    from icc_widget.i18n import DEFAULT_LANGUAGE, tr, tr_display
    from icc_widget.table_utils import configure_content_fit_table, refit_table_columns
except ImportError:
    from .copy_utils import install_copy_shortcut
    from .conversion_chain_widget import _create_curve_plot
    from .i18n import DEFAULT_LANGUAGE, tr, tr_display
    from .table_utils import configure_content_fit_table, refit_table_columns
    from ..icc_summary_extract import build_icc_summary


class ICCSummaryWidget(QWidget):
    """Display concise and interpreted ICC profile information."""

    def __init__(self, parent=None):
        """Initialize the summary widget.

        Args:
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self.summary_rows = []
        self.parsed_data = {}
        self.language = DEFAULT_LANGUAGE
        self._init_ui()

    def _init_ui(self) -> None:
        """Create table-based summary UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel()
        self.title_label.setObjectName("iccTitleLabel")
        layout.addWidget(self.title_label)

        self.help_label = QLabel()
        self.help_label.setWordWrap(True)
        self.help_label.setObjectName("iccHelpLabel")
        layout.addWidget(self.help_label)

        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(len(tr("summary.headers", self.language)))
        self.summary_table.verticalHeader().setVisible(False)
        self.summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.setWordWrap(True)
        self.summary_table.itemDoubleClicked.connect(self.on_item_double_clicked)
        install_copy_shortcut(self.summary_table)
        configure_content_fit_table(
            self.summary_table,
            min_widths=[100, 170, 220, 170, 180, 100],
            max_widths=[160, 260, 520, 280, 420, 140],
        )
        layout.addWidget(self.summary_table)
        self.retranslate_ui()

    def set_language(self, language: str) -> None:
        """Switch this summary widget between English and Chinese."""
        self.language = language
        self.retranslate_ui()
        self._populate_table()

    def retranslate_ui(self) -> None:
        """Refresh static labels and table headers for the current language."""
        self.title_label.setText(tr("summary.title", self.language))
        self.help_label.setText(tr("summary.help", self.language))
        self.summary_table.setHorizontalHeaderLabels(tr("summary.headers", self.language))
        refit_table_columns(self.summary_table)

    def set_profile_data(self, parsed_data: dict) -> None:
        """Refresh the table from parsed ICC data.

        Args:
            parsed_data: Parsed ICC dictionary, or None to clear the table.
        """
        self.parsed_data = parsed_data or {}
        self.summary_rows = build_icc_summary(self.parsed_data) if parsed_data else []
        self._populate_table()

    def clear(self) -> None:
        """Clear current summary rows."""
        self.summary_rows = []
        self.parsed_data = {}
        self.summary_table.setRowCount(0)

    def on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        """Handle future visualization entry points."""
        row = item.row()
        if row < 0 or row >= len(self.summary_rows):
            return

        visualizable = self.summary_rows[row].get("visualizable", "")
        if not visualizable:
            return

        row_data = self.summary_rows[row]
        label = row_data.get("item", "Selected item")
        if visualizable == "curve":
            self._show_curve_dialog(row_data)
            return

        QMessageBox.information(
            self,
            tr("summary.visualization_title", self.language),
            tr("summary.visualization_message", self.language).format(
                label=tr_display(label, self.language),
                visualizable=tr_display(visualizable, self.language),
            ),
        )

    def _show_curve_dialog(self, row_data: dict) -> None:
        """Open a curve visualization dialog for a TRC summary row."""
        curve_data = self._curve_data_from_source(row_data.get("source", ""))
        if not curve_data:
            QMessageBox.information(self, tr("summary.visualization_title", self.language), tr("summary.no_curve_data", self.language))
            return

        title = tr_display(row_data.get("item", "Curve"), self.language)
        component = {
            "kind": "curve",
            "title": title,
            "curves": [(title, curve_data)],
        }
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)
        layout.addWidget(_create_curve_plot(component, self.language))
        dialog.resize(760, 520)
        dialog.exec_()

    def _curve_data_from_source(self, source: str) -> dict:
        """Resolve a source path like tag_data.rTRC into parsed curve data."""
        parts = source.split(".")
        if len(parts) != 2 or parts[0] != "tag_data":
            return {}
        value = self.parsed_data.get("tag_data", {}).get(parts[1], {})
        return value if isinstance(value, dict) else {}

    def _populate_table(self) -> None:
        """Fill the table with summary rows."""
        self.summary_table.setRowCount(0)
        for row_index, row_data in enumerate(self.summary_rows):
            self.summary_table.insertRow(row_index)
            values = [
                tr_display(row_data.get("section", ""), self.language),
                tr_display(row_data.get("item", ""), self.language),
                row_data.get("value", ""),
                row_data.get("source", ""),
                tr_display(row_data.get("note", ""), self.language),
                tr_display(row_data.get("visualizable", ""), self.language),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 5 and value:
                    item.setText(tr("summary.visualize_prefix", self.language).format(value=value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.summary_table.setItem(row_index, column, item)

        self.summary_table.resizeRowsToContents()
        refit_table_columns(self.summary_table)
