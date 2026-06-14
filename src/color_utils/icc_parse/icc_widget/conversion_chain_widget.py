"""Conversion-chain visualization widget for parsed ICC profile data.

The widget displays inferred ICC conversion chains and visualizes selected
curve, matrix, and CLUT components with PyQtGraph.
"""

import os
from typing import Any, Dict, List, Sequence, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
import numpy as np
import pyqtgraph as pg

try:
    import pyqtgraph.opengl as gl
except Exception:
    gl = None

try:
    from icc_conversion_chain_extract import build_conversion_chains
    from icc_summary_extract import _as_dict, _field_value
    from icc_widget.copy_utils import install_copy_shortcut
    from icc_widget.i18n import DEFAULT_LANGUAGE, tr, tr_display
    from icc_widget.table_utils import configure_content_fit_table, refit_table_columns
except ImportError:
    from ..icc_conversion_chain_extract import build_conversion_chains
    from ..icc_summary_extract import _as_dict, _field_value
    from .copy_utils import install_copy_shortcut
    from .i18n import DEFAULT_LANGUAGE, tr, tr_display
    from .table_utils import configure_content_fit_table, refit_table_columns


CHANNEL_COLORS = ["#e53935", "#43a047", "#1e88e5", "#8e24aa", "#fb8c00", "#00acc1"]


class ConversionChainWidget(QWidget):
    """Display inferred ICC conversion chains with component visualizations."""

    def __init__(self, parent=None):
        """Initialize the conversion-chain widget."""
        super().__init__(parent)
        self.chain_rows: List[Dict[str, str]] = []
        self.parsed_data: dict = {}
        self.current_pixmap = None
        self.language = DEFAULT_LANGUAGE
        self._init_ui()

    def _init_ui(self) -> None:
        """Create chain table and component visualization UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel()
        self.title_label.setObjectName("iccTitleLabel")
        layout.addWidget(self.title_label)

        self.help_label = QLabel()
        self.help_label.setWordWrap(True)
        self.help_label.setObjectName("iccHelpLabel")
        layout.addWidget(self.help_label)

        splitter = QSplitter(Qt.Vertical)

        self.chain_table = QTableWidget()
        self.chain_table.setColumnCount(len(tr("chain.headers", self.language)))
        self.chain_table.verticalHeader().setVisible(False)
        self.chain_table.verticalHeader().setDefaultSectionSize(28)
        self.chain_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.chain_table.setAlternatingRowColors(True)
        self.chain_table.setWordWrap(False)
        self.chain_table.setTextElideMode(Qt.ElideRight)
        self.chain_table.itemSelectionChanged.connect(self._show_selected_chain)
        install_copy_shortcut(self.chain_table)
        configure_content_fit_table(
            self.chain_table,
            min_widths=[170, 70, 150, 190, 220, 220],
            max_widths=[300, 120, 250, 360, 520, 560],
        )
        splitter.addWidget(self.chain_table)

        component_container = QWidget()
        component_layout = QVBoxLayout(component_container)
        component_layout.setContentsMargins(0, 0, 0, 0)
        component_header_layout = QHBoxLayout()
        component_header_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_title = QLabel()
        self.preview_title.setWordWrap(True)
        self.preview_title.setObjectName("iccPreviewTitle")
        self.reset_view_button = QPushButton()
        self.reset_view_button.setEnabled(False)
        self.reset_view_button.clicked.connect(self._reset_component_views)
        component_header_layout.addWidget(self.preview_title, 1)
        component_header_layout.addWidget(self.reset_view_button)
        component_layout.addLayout(component_header_layout)

        self.visual_panel = QWidget()
        self.visual_layout = QHBoxLayout(self.visual_panel)
        self.visual_layout.setContentsMargins(8, 8, 8, 8)
        self.visual_layout.setSpacing(12)

        self.component_scroll_area = QScrollArea()
        self.component_scroll_area.setWidgetResizable(True)
        self.component_scroll_area.setWidget(self.visual_panel)
        component_layout.addWidget(self.component_scroll_area, 1)
        splitter.addWidget(component_container)

        figure_container = QWidget()
        figure_layout = QVBoxLayout(figure_container)
        figure_layout.setContentsMargins(0, 0, 0, 0)
        self.figure_title = QLabel()
        self.figure_title.setObjectName("iccPreviewTitle")
        figure_layout.addWidget(self.figure_title)

        self.image_label = QLabel()
        self.image_label.setObjectName("iccImagePreview")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(180)
        self.image_label.setScaledContents(False)

        self.figure_scroll_area = QScrollArea()
        self.figure_scroll_area.setWidgetResizable(True)
        self.figure_scroll_area.setWidget(self.image_label)
        figure_layout.addWidget(self.figure_scroll_area, 1)
        splitter.addWidget(figure_container)

        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setCollapsible(2, False)
        splitter.setSizes([190, 320, 260])
        layout.addWidget(splitter, 1)
        self.retranslate_ui()

    def set_language(self, language: str) -> None:
        """Switch this conversion-chain widget between English and Chinese."""
        selected_rows = self.chain_table.selectionModel().selectedRows()
        selected_row = selected_rows[0].row() if selected_rows else -1
        self.language = language
        self.retranslate_ui()
        self._populate_table()
        if self.chain_rows and selected_row >= 0:
            self.chain_table.selectRow(min(selected_row, len(self.chain_rows) - 1))
        elif self.chain_rows:
            self.chain_table.clearSelection()
            self._clear_preview(tr("chain.select_prompt", self.language))
        else:
            self._clear_preview(tr("chain.no_data", self.language))

    def retranslate_ui(self) -> None:
        """Refresh static labels and table headers for the current language."""
        self.title_label.setText(tr("chain.title", self.language))
        self.help_label.setText(tr("chain.help", self.language))
        self.reset_view_button.setText(tr("chain.reset_view", self.language))
        self.chain_table.setHorizontalHeaderLabels(tr("chain.headers", self.language))
        if not self.chain_rows:
            self._clear_preview(tr("chain.select_prompt", self.language))
        refit_table_columns(self.chain_table)

    def set_profile_data(self, parsed_data: dict) -> None:
        """Refresh conversion-chain rows from parsed ICC data."""
        self.parsed_data = parsed_data or {}
        self.chain_rows = build_conversion_chains(self.parsed_data) if self.parsed_data else []
        self._populate_table()
        if self.chain_rows:
            self.chain_table.clearSelection()
            self._clear_preview(tr("chain.select_prompt", self.language))
        else:
            self._clear_preview(tr("chain.no_data", self.language))

    def clear(self) -> None:
        """Clear table and image preview."""
        self.chain_rows = []
        self.parsed_data = {}
        self.chain_table.setRowCount(0)
        self._clear_preview(tr("chain.no_data", self.language))

    def resizeEvent(self, event) -> None:
        """Refit table columns and reference image after widget resize."""
        super().resizeEvent(event)
        refit_table_columns(self.chain_table)
        self._update_scaled_pixmap()

    def _populate_table(self) -> None:
        """Fill the chain table."""
        self.chain_table.setRowCount(0)
        for row_index, row_data in enumerate(self.chain_rows):
            self.chain_table.insertRow(row_index)
            values = [
                tr_display(row_data.get("direction", ""), self.language),
                row_data.get("tag", ""),
                tr_display(row_data.get("intent", ""), self.language),
                row_data.get("figure", ""),
                tr_display(row_data.get("title", ""), self.language),
                tr_display(row_data.get("reason", ""), self.language),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.chain_table.setItem(row_index, column, item)
            self.chain_table.setRowHeight(row_index, 28)
        refit_table_columns(self.chain_table)

    def _show_selected_chain(self) -> None:
        """Show figure for the selected chain table row."""
        selected = self.chain_table.selectedItems()
        if not selected:
            return
        row_index = selected[0].row()
        if row_index < 0 or row_index >= len(self.chain_rows):
            return

        row_data = self.chain_rows[row_index]
        self.preview_title.setText(
            f"{tr_display(row_data.get('direction', ''), self.language)} | {row_data.get('tag', '')} | "
            f"{tr_display(row_data.get('title', ''), self.language)}\n"
            f"{tr_display(row_data.get('reason', ''), self.language)}"
        )
        components = build_visual_components(self.parsed_data, row_data)
        self._render_reference_figure(row_data)
        self._render_components(components)

    def _clear_preview(self, message: str) -> None:
        """Clear image preview and show a message."""
        self.current_pixmap = None
        self.preview_title.setText(message)
        self._show_visual_message(message)
        self.figure_title.setText(tr("chain.reference_figure", self.language))
        self.image_label.clear()
        self.image_label.setText(message)

    def _render_components(self, components: List[Dict[str, Any]]) -> None:
        """Render chain components from left to right."""
        self._clear_visual_layout()
        if not components:
            self.reset_view_button.setEnabled(False)
            self._show_visual_message(tr("chain.no_figure", self.language))
            return

        self.reset_view_button.setEnabled(True)
        self.visual_layout.addStretch(1)
        for index, component in enumerate(components):
            if index:
                self.visual_layout.addWidget(_arrow_label())
            self.visual_layout.addWidget(_create_component_card(component, self.language))
        self.visual_layout.addStretch(1)

    def _render_reference_figure(self, row_data: Dict[str, str]) -> None:
        """Render the selected chain's static JPG reference figure."""
        figure = row_data.get("figure", "")
        self.figure_title.setText(tr("chain.reference_figure", self.language))
        if not figure:
            self.current_pixmap = None
            self.image_label.clear()
            self.image_label.setText(tr("chain.no_reference_figure", self.language))
            return

        image_path = _figure_path(figure)
        if not os.path.exists(image_path):
            self.current_pixmap = None
            self.image_label.clear()
            self.image_label.setText(tr("chain.figure_error", self.language).format(image_path=image_path))
            return

        self.current_pixmap = QPixmap(image_path)
        if self.current_pixmap.isNull():
            self.image_label.clear()
            self.image_label.setText(tr("chain.figure_error", self.language).format(image_path=image_path))
            return
        self.image_label.clear()
        self.image_label.setText("")
        self.image_label.setPixmap(self.current_pixmap)
        self.image_label.setMinimumSize(self.current_pixmap.size())
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self) -> None:
        """Scale the current reference figure to fit the lower preview area."""
        if self.current_pixmap is None or self.current_pixmap.isNull():
            return
        target_size = self.figure_scroll_area.viewport().size()
        if target_size.width() < 8 or target_size.height() < 8:
            self.image_label.setText("")
            self.image_label.setPixmap(self.current_pixmap)
            self.image_label.setMinimumSize(self.current_pixmap.size())
            return
        target_size.setWidth(max(1, target_size.width() - 24))
        target_size.setHeight(max(1, target_size.height() - 24))
        scaled = self.current_pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setText("")
        self.image_label.setPixmap(scaled)
        self.image_label.setMinimumSize(scaled.size())

    def _clear_visual_layout(self) -> None:
        """Remove old visualization widgets."""
        while self.visual_layout.count():
            item = self.visual_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.reset_view_button.setEnabled(False)

    def _reset_component_views(self) -> None:
        """Reset all current conversion-chain visual component views."""
        for plot in self.visual_panel.findChildren(pg.PlotWidget):
            plot.setXRange(0.0, 1.0, padding=0.02)
            plot.setYRange(0.0, 1.0, padding=0.02)
        if gl is None:
            return
        gl_view_class = getattr(gl, "GLViewWidget", None)
        if gl_view_class is None:
            return
        for view in self.visual_panel.findChildren(gl_view_class):
            view.setCameraPosition(distance=2.2, elevation=22, azimuth=35)

    def _show_visual_message(self, message: str) -> None:
        """Show a message in the middle component visualization area."""
        self._clear_visual_layout()
        empty_label = QLabel(message)
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setMinimumHeight(220)
        self.visual_layout.addWidget(empty_label, 1)


def build_visual_components(parsed_data: dict, row_data: Dict[str, str]) -> List[Dict[str, Any]]:
    """Build ordered visual component descriptors for a selected conversion chain."""
    tag_name = row_data.get("tag", "")
    tag_data = _as_dict(parsed_data.get("tag_data", {}))
    if tag_name == "Matrix/TRC":
        return _build_matrix_trc_components(tag_data, row_data.get("direction", ""))

    pipeline = _as_dict(tag_data.get(tag_name))
    if not pipeline:
        return []

    tag_type = str(_field_value(pipeline.get("type_signature"), pipeline.get("datatype", "")))
    component_order = _pipeline_component_order(tag_type, row_data.get("direction", ""), tag_name)
    components = []
    for key, label, kind in component_order:
        component_data = _as_dict(pipeline.get(key))
        if not component_data:
            continue
        if kind == "curve":
            components.append(_curve_component(label, component_data))
        elif kind == "matrix":
            components.append(_matrix_component(label, component_data))
        elif kind == "clut":
            axes = _clut_axis_labels(parsed_data, row_data, tag_type)
            components.append(_clut_component(label, component_data, axes))
    return components


def _build_matrix_trc_components(tag_data: dict, direction: str) -> List[Dict[str, Any]]:
    """Build visuals for classic RGB matrix/TRC profiles."""
    inverse = _direction_is_pcs_to_device(direction)
    trc_component = {
        "kind": "curve",
        "title": "B Curves / RGB TRC^-1" if inverse else "B Curves / RGB TRC",
        "curves": [
            ("Red TRC", _as_dict(tag_data.get("rTRC"))),
            ("Green TRC", _as_dict(tag_data.get("gTRC"))),
            ("Blue TRC", _as_dict(tag_data.get("bTRC"))),
        ],
        "inverse": inverse,
    }
    matrix_component = {
        "kind": "matrix",
        "title": "XYZ -> RGB Matrix^-1" if inverse else "RGB -> XYZ Matrix",
        "values": _inverse_3x3(_rgb_xyz_matrix(tag_data)) if inverse else _rgb_xyz_matrix(tag_data),
    }
    if inverse:
        return [matrix_component, trc_component]
    return [trc_component, matrix_component]


def _pipeline_component_order(tag_type: str, direction: str, tag_name: str = "") -> List[Tuple[str, str, str]]:
    """Return mAB/mBA component order from source side to destination side."""
    if tag_type == "mBA ":
        return [
            ("b_curve", "B Curves", "curve"),
            ("matrix", "Matrix", "matrix"),
            ("m_curve", "M Curves", "curve"),
            ("clut", "CLUT", "clut"),
            ("a_curve", "A Curves", "curve"),
        ]
    if tag_type == "mAB ":
        return [
            ("a_curve", "A Curves", "curve"),
            ("clut", "CLUT", "clut"),
            ("m_curve", "M Curves", "curve"),
            ("matrix", "Matrix", "matrix"),
            ("b_curve", "B Curves", "curve"),
        ]
    pcs_to_device = _tag_is_pcs_to_device(tag_name) if tag_name else _direction_is_pcs_to_device(direction)
    if pcs_to_device:
        return [
            ("b_curve", "B Curves", "curve"),
            ("matrix", "Matrix", "matrix"),
            ("m_curve", "M Curves", "curve"),
            ("clut", "CLUT", "clut"),
            ("a_curve", "A Curves", "curve"),
        ]
    return [
        ("a_curve", "A Curves", "curve"),
        ("clut", "CLUT", "clut"),
        ("m_curve", "M Curves", "curve"),
        ("matrix", "Matrix", "matrix"),
        ("b_curve", "B Curves", "curve"),
    ]


def _direction_is_pcs_to_device(direction: str) -> bool:
    """Return whether a display direction starts from the PCS side."""
    source_space = str(direction or "").split("->", 1)[0].strip()
    return source_space in {"PCS", "PCSXYZ", "XYZ", "Lab", "Luv"}


def _tag_is_pcs_to_device(tag_name: str) -> bool:
    """Return whether an ICC conversion tag family maps PCS to device space."""
    return str(tag_name or "").startswith(("B2A", "B2D"))


def _clut_axis_labels(parsed_data: dict, row_data: Dict[str, str], tag_type: str) -> List[str]:
    """Infer three CLUT output-axis labels from the current chain destination space."""
    tag_name = row_data.get("tag", "")
    direction = str(row_data.get("direction", ""))
    if tag_type == "mAB ":
        space = _profile_signature(parsed_data, "pcs")
    elif tag_type == "mBA ":
        space = _profile_signature(parsed_data, "color_space")
    elif _tag_is_pcs_to_device(tag_name) or (not tag_name and _direction_is_pcs_to_device(direction)):
        space = _profile_signature(parsed_data, "color_space")
    else:
        space = _profile_signature(parsed_data, "pcs")
    return _space_axis_labels(space)


def _profile_signature(parsed_data: dict, key: str) -> str:
    """Read a profile header signature from parsed JSON-like data."""
    header = _as_dict(parsed_data.get("header", {}))
    value = _field_value(header.get(key), header.get(key, ""))
    if isinstance(value, (list, tuple)) and value:
        value = value[0]
    return str(value or "").strip()


def _space_axis_labels(space_signature: str) -> List[str]:
    """Return readable axis labels for common ICC colour-space signatures."""
    signature = (space_signature or "").strip()
    labels = {
        "RGB": ["R", "G", "B"],
        "RGB ": ["R", "G", "B"],
        "XYZ": ["X", "Y", "Z"],
        "XYZ ": ["X", "Y", "Z"],
        "Lab": ["L*", "a*", "b*"],
        "Lab ": ["L*", "a*", "b*"],
        "Luv": ["L*", "u*", "v*"],
        "Luv ": ["L*", "u*", "v*"],
        "YCbr": ["Y", "Cb", "Cr"],
        "Yxy": ["Y", "x", "y"],
        "Yxy ": ["Y", "x", "y"],
        "HSV": ["H", "S", "V"],
        "HSV ": ["H", "S", "V"],
        "HLS": ["H", "L", "S"],
        "HLS ": ["H", "L", "S"],
        "CMY": ["C", "M", "Y"],
        "CMY ": ["C", "M", "Y"],
    }
    return labels.get(signature, ["Ch 1", "Ch 2", "Ch 3"])


def _curve_component(title: str, curve_data: dict) -> Dict[str, Any]:
    """Create a curve component, duplicating one parsed curve across channel count when needed."""
    channel_count = _curve_channel_count(curve_data)
    curves = [(f"Ch {index + 1}", curve_data) for index in range(max(1, channel_count))]
    return {"kind": "curve", "title": title, "curves": curves}


def _matrix_component(title: str, matrix_data: dict) -> Dict[str, Any]:
    """Create a matrix component descriptor."""
    values = _field_value(matrix_data.get("values"), _field_value(matrix_data.get("matrix"), []))
    return {"kind": "matrix", "title": title, "values": values}


def _clut_component(title: str, clut_data: dict, axis_labels: Sequence[str]) -> Dict[str, Any]:
    """Create a CLUT component descriptor."""
    return {
        "kind": "clut",
        "title": title,
        "grid_points": _field_value(clut_data.get("grid_points"), []),
        "values": _field_value(clut_data.get("values"), []),
        "input_channels": int(clut_data.get("input_channels", 0) or 0),
        "output_channels": int(clut_data.get("output_channels", 0) or 0),
        "data_type": clut_data.get("data_type", ""),
        "axis_labels": list(axis_labels),
    }


def _create_component_card(component: Dict[str, Any], language: str) -> QWidget:
    """Create a card widget for one conversion component."""
    card = QFrame()
    card.setObjectName("iccComponentCard")
    card.setFrameShape(QFrame.StyledPanel)
    kind = component.get("kind")
    card.setMinimumWidth(540 if kind == "clut" else 320)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(6)

    title = QLabel(tr_display(component.get("title", ""), language))
    title_font = QFont()
    title_font.setBold(True)
    title.setFont(title_font)
    layout.addWidget(title)

    if kind == "curve":
        layout.addWidget(_create_curve_plot(component, language), 1)
    elif kind == "matrix":
        layout.addWidget(_create_matrix_table(component), 1)
    elif kind == "clut":
        layout.addWidget(_create_clut_view(component), 1)
    else:
        layout.addWidget(QLabel(tr_display("Unsupported component", language)))
    return card


def _create_curve_plot(component: Dict[str, Any], language: str) -> QWidget:
    """Create a PyQtGraph plot for one or more channel curves."""
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    plot = pg.PlotWidget()
    plot.setMinimumSize(320, 250)
    plot.setBackground("w")
    plot.showGrid(x=True, y=True, alpha=0.25)
    inverse = bool(component.get("inverse", False))
    plot.setLabel("bottom", "Output" if inverse else "Input")
    plot.setLabel("left", "Input" if inverse else "Output")
    _bold_plot_axes(plot)
    plot.setXRange(0.0, 1.0)
    plot.setYRange(0.0, 1.0)
    plot.addLegend(offset=(8, 8), labelTextSize="12pt")

    for index, (label, curve_data) in enumerate(component.get("curves", [])):
        x_values, y_values = _sample_curve(curve_data)
        if inverse:
            x_values, y_values = y_values, x_values
        color = CHANNEL_COLORS[index % len(CHANNEL_COLORS)]
        plot.plot(x_values, y_values, pen=pg.mkPen(color, width=5.0), name=tr_display(label, language))
    layout.addWidget(plot, 1)

    formula = _curve_formula_text(component.get("curves", []), inverse)
    if formula:
        formula_label = QLabel(formula)
        formula_label.setWordWrap(True)
        formula_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        formula_label.setStyleSheet(
            "QLabel { color: #333333; font-family: Consolas; font-size: 9pt; "
            "background-color: #f7fbff; border: 1px solid #c8dced; padding: 4px; }"
        )
        layout.addWidget(formula_label)
    return container


def _create_matrix_table(component: Dict[str, Any]) -> QWidget:
    """Create a compact matrix table with selectable/copyable numeric text."""
    values = _matrix_display_values(list(component.get("values") or []))
    column_count = 4 if len(values) >= 12 else 3
    row_count = max(1, (len(values) + column_count - 1) // column_count)

    table = QTableWidget(row_count, column_count)
    table.setObjectName("iccMatrixTable")
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.ExtendedSelection)
    table.setSelectionBehavior(QAbstractItemView.SelectItems)
    table.setWordWrap(False)
    table.setTextElideMode(Qt.ElideNone)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    table.setAlternatingRowColors(False)
    table.setMinimumSize(max(390, column_count * 132 + 78), 210)
    table.setStyleSheet(
        "QTableWidget#iccMatrixTable {"
        "font-family: Consolas;"
        "font-size: 10pt;"
        "font-weight: 600;"
        "gridline-color: #A0C3DC;"
        "background-color: #ffffff;"
        "alternate-background-color: #ffffff;"
        "}"
        "QTableWidget#iccMatrixTable::item {"
        "padding: 3px 6px;"
        "border: 1px solid #DBE7F1;"
        "}"
        "QTableWidget#iccMatrixTable::item:selected {"
        "background-color: #0078d4;"
        "color: #ffffff;"
        "}"
        "QTableWidget#iccMatrixTable QHeaderView::section {"
        "font-family: Arial;"
        "font-size: 9pt;"
        "font-weight: bold;"
        "padding: 3px 6px;"
        "background-color: #DBE7F1;"
        "border: 1px solid #A0C3DC;"
        "}"
    )

    _set_matrix_headers(table, row_count, column_count)
    for row in range(row_count):
        for column in range(column_count):
            value_index = row * column_count + column
            text = "" if value_index >= len(values) else f"{float(values[value_index]):.4f}"
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, column, item)

    for column in range(column_count):
        table.setColumnWidth(column, 128)
    for row in range(row_count):
        table.setRowHeight(row, 34)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
    install_copy_shortcut(table)
    return table


def _matrix_display_values(values: List[float]) -> List[float]:
    """Return matrix values in visual row-major order.

    ICC mAB/mBA stores e1-e9 as the 3x3 coefficients followed by e10-e12
    offsets. The visual 3x4 matrix should therefore append one offset to
    each coefficient row instead of directly reshaping the raw 12 values.
    """
    if len(values) != 12:
        return values
    return [
        values[0], values[1], values[2], values[9],
        values[3], values[4], values[5], values[10],
        values[6], values[7], values[8], values[11],
    ]


def _create_clut_view(component: Dict[str, Any]) -> QWidget:
    """Create a 3D CLUT scatter view, falling back to 2D when OpenGL is unavailable."""
    grid_points = [int(value) for value in component.get("grid_points", []) if int(value) > 0]
    values = [float(value) for value in component.get("values", [])]
    output_channels = int(component.get("output_channels") or 0)
    axis_labels = _normalized_axis_labels(component.get("axis_labels"))
    if len(grid_points) >= 3 and output_channels >= 1 and values and gl is not None:
        return _create_clut_3d_view(grid_points, output_channels, values, axis_labels)
    return _create_clut_2d_view(grid_points, output_channels, values, axis_labels)


def _create_clut_3d_view(
    grid_points: Sequence[int],
    output_channels: int,
    values: Sequence[float],
    axis_labels: Sequence[str],
) -> QWidget:
    """Create an OpenGL 3D scatter plot for 3-channel CLUT samples."""
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    view = gl.GLViewWidget()
    view.setMinimumSize(520, 320)
    view.setBackgroundColor("w")
    view.setCameraPosition(distance=2.2, elevation=22, azimuth=35)
    grid = gl.GLGridItem()
    grid.setColor((0, 0, 0, 55))
    grid.scale(0.1, 0.1, 0.1)
    view.addItem(grid)
    _add_gl_axes(view, axis_labels)

    positions, colors = _sample_clut_output_points(grid_points, output_channels, values)
    scatter = gl.GLScatterPlotItem(pos=positions, color=colors, size=12.0, pxMode=True)
    scatter.setGLOptions("opaque")
    view.addItem(scatter)

    axis_hint = QLabel(_format_axis_hint(axis_labels))
    axis_hint.setAlignment(Qt.AlignCenter)
    axis_hint.setStyleSheet("QLabel { color: #333333; font-weight: 600; padding: 2px; }")
    layout.addWidget(view, 1)
    layout.addWidget(axis_hint)
    return container


def _create_clut_2d_view(
    grid_points: Sequence[int],
    output_channels: int,
    values: Sequence[float],
    axis_labels: Sequence[str],
) -> QWidget:
    """Create a 2D CLUT projection if 3D rendering is unavailable."""
    plot = pg.PlotWidget()
    plot.setMinimumSize(520, 320)
    plot.setBackground("w")
    plot.showGrid(x=True, y=True, alpha=0.25)
    labels = _normalized_axis_labels(axis_labels)
    plot.setLabel("bottom", labels[0])
    plot.setLabel("left", labels[1])
    _bold_plot_axes(plot)
    if not values or output_channels <= 0:
        plot.addItem(pg.TextItem("No CLUT values", color="#333333", anchor=(0.5, 0.5)))
        return plot

    point_count = _clut_point_count(grid_points, output_channels, values)
    step = max(1, point_count // 2500)
    spots = []
    for point_index in range(0, point_count, step):
        position = _clut_output_position(point_index, output_channels, values, dimensions=2)
        _, color = _clut_rgb_position_and_color(point_index, grid_points)
        spots.append({
            "pos": (position[0], position[1]),
            "brush": QColor.fromRgbF(color[0], color[1], color[2], color[3]),
            "size": 16,
        })
    scatter = pg.ScatterPlotItem(spots=spots, pen=None)
    scatter.setPen(pg.mkPen("#333333", width=1.0))
    plot.addItem(scatter)
    return plot


def _set_matrix_headers(table: QTableWidget, row_count: int, column_count: int) -> None:
    """Set readable row/column headers for matrix displays."""
    if row_count == 3 and column_count == 3:
        table.setHorizontalHeaderLabels(["R", "G", "B"])
        table.setVerticalHeaderLabels(["X", "Y", "Z"])
    elif row_count == 3 and column_count == 4:
        table.setHorizontalHeaderLabels(["C1", "C2", "C3", "Offset"])
        table.setVerticalHeaderLabels(["R1", "R2", "R3"])
    else:
        table.setHorizontalHeaderLabels([f"C{index + 1}" for index in range(column_count)])
        table.setVerticalHeaderLabels([f"R{index + 1}" for index in range(row_count)])


def _add_gl_axes(view, axis_labels: Sequence[str]) -> None:
    """Add colored input axes to a 3D CLUT view."""
    labels = _normalized_axis_labels(axis_labels)
    axes = [
        ((1.08, 0.0, 0.0), (0.85, 0.05, 0.05, 1.0), labels[0]),
        ((0.0, 1.08, 0.0), (0.05, 0.55, 0.05, 1.0), labels[1]),
        ((0.0, 0.0, 1.08), (0.05, 0.18, 0.85, 1.0), labels[2]),
    ]
    for end, color, label in axes:
        positions = np.array([[0.0, 0.0, 0.0], list(end)], dtype=float)
        view.addItem(gl.GLLinePlotItem(pos=positions, color=color, width=3.0, antialias=True))
        _add_gl_axis_label(view, np.array(end, dtype=float) * 1.08, label)


def _add_gl_axis_label(view, position: np.ndarray, label: str) -> None:
    """Add an optional 3D axis label when the installed pyqtgraph version supports it."""
    if not hasattr(gl, "GLTextItem"):
        return
    try:
        view.addItem(gl.GLTextItem(pos=position, text=str(label), color=(0, 0, 0, 255)))
    except TypeError:
        view.addItem(gl.GLTextItem(pos=position, text=str(label)))


def _format_axis_hint(axis_labels: Sequence[str]) -> str:
    """Format compact axis labels outside the OpenGL view."""
    labels = _normalized_axis_labels(axis_labels)
    return f"Output axes: {labels[0]} / {labels[1]} / {labels[2]} (point color = input RGB lattice)"


def _normalized_axis_labels(axis_labels: Sequence[str]) -> List[str]:
    """Return three usable axis labels, falling back to generic channel names."""
    defaults = ["Ch 1", "Ch 2", "Ch 3"]
    labels = [str(label).strip() for label in (axis_labels or []) if str(label).strip()]
    return (labels + defaults[len(labels):])[:3]


def _arrow_label() -> QLabel:
    """Create a visual arrow between component cards."""
    label = QLabel("→")
    label.setAlignment(Qt.AlignCenter)
    font = QFont()
    font.setPointSize(18)
    font.setBold(True)
    label.setFont(font)
    return label


def _bold_plot_axes(plot: pg.PlotWidget) -> None:
    """Make PyQtGraph plot axes and tick labels easier to read."""
    axis_font = QFont()
    axis_font.setBold(True)
    axis_font.setPointSize(12)
    label_font = QFont()
    label_font.setBold(True)
    label_font.setPointSize(13)
    for axis_name in ("bottom", "left"):
        axis = plot.getAxis(axis_name)
        axis.setPen(pg.mkPen("#333333", width=2.0))
        axis.setTextPen(pg.mkPen("#333333"))
        axis.setStyle(tickFont=axis_font)
        axis.label.setFont(label_font)
    plot.getPlotItem().getViewBox().setBorder(pg.mkPen("#555555", width=1.5))


def _sample_curve(curve_data: dict, sample_count: int = 256) -> Tuple[List[float], List[float]]:
    """Sample curveType or parametricCurveType into x/y arrays."""
    datatype = str(_field_value(curve_data.get("type_signature"), curve_data.get("datatype", "")))
    x_values = [index / (sample_count - 1) for index in range(sample_count)]
    if datatype == "para" or "function_type" in curve_data:
        function_type = int(_field_value(curve_data.get("function_type"), 0) or 0)
        parameters = _curve_parameter_values(curve_data)
        return x_values, [_eval_parametric_curve(x, function_type, parameters) for x in x_values]

    count = int(_field_value(curve_data.get("count"), 0) or 0)
    curve_values = [float(value) for value in _field_value(curve_data.get("curve_data"), [])]
    if count == 0:
        return x_values, x_values
    if count == 1 and curve_values:
        gamma = curve_values[0]
        return x_values, [x ** gamma for x in x_values]
    if curve_values:
        if len(curve_values) == 1:
            return [0.0, 1.0], [curve_values[0], curve_values[0]]
        x_points = [index / (len(curve_values) - 1) for index in range(len(curve_values))]
        return x_points, curve_values
    return x_values, x_values


def _eval_parametric_curve(x_value: float, function_type: int, parameters: Sequence[float]) -> float:
    """Evaluate common ICC parametric curve functions."""
    params = list(parameters) + [0.0] * 7
    g, a, b, c, d, e, f = params[:7]
    if function_type == 0:
        return _clamp01(x_value ** g if g else x_value)
    if function_type == 1:
        return _clamp01((a * x_value + b) ** g if x_value >= -b / a and a else 0.0)
    if function_type == 2:
        return _clamp01((a * x_value + b) ** g + c if x_value >= -b / a and a else c)
    if function_type == 3:
        return _clamp01((a * x_value + b) ** g if x_value >= d else c * x_value)
    if function_type == 4:
        return _clamp01((a * x_value + b) ** g + e if x_value >= d else c * x_value + f)
    return _clamp01(x_value)


def _curve_formula_text(curves: Sequence[Tuple[str, dict]], inverse: bool) -> str:
    """Return a readable formula or LUT hint for the first curve in a component."""
    for _label, curve_data in curves:
        datatype = str(_field_value(curve_data.get("type_signature"), curve_data.get("datatype", "")))
        if datatype == "para" or "function_type" in curve_data:
            function_type = int(_field_value(curve_data.get("function_type"), 0) or 0)
            parameters = _curve_parameter_values(curve_data)
            text = _parametric_formula_text(function_type, parameters)
            if inverse:
                text += "\nview: inverse chain, plotted with x/y swapped"
            return text
        if datatype == "curv" or "count" in curve_data:
            count = int(_field_value(curve_data.get("count"), 0) or 0)
            curve_values = [_to_float(value) for value in _field_value(curve_data.get("curve_data"), [])]
            text = _curve_type_formula_text(count, curve_values)
            if inverse:
                text += "\nview: inverse chain, plotted with x/y swapped"
            return text
    return ""


def _parametric_formula_text(function_type: int, parameters: Sequence[float]) -> str:
    """Format ICC parametric curve formulas with actual parameter values."""
    names = ["g", "a", "b", "c", "d", "e", "f"]
    params = list(parameters)
    param_text = ", ".join(f"{name}={_format_number(value)}" for name, value in zip(names, params))
    formulas = {
        0: "y = x^g",
        1: "y = (a*x + b)^g if x >= -b/a else 0",
        2: "y = (a*x + b)^g + c if x >= -b/a else c",
        3: "y = (a*x + b)^g if x >= d else c*x",
        4: "y = (a*x + b)^g + e if x >= d else c*x + f",
    }
    formula = formulas.get(function_type, "y = x")
    resolved = _resolved_parametric_formula(function_type, params)
    lines = [
        f"parametric type {function_type}",
        f"generic: {formula}",
        f"resolved: {resolved}",
    ]
    if param_text:
        lines.append(f"parameters: {param_text}")
    return "\n".join(lines)


def _curve_parameter_values(curve_data: dict) -> List[float]:
    """Read parametric curve parameters from binary-parser lists or inspector dicts."""
    names = ["g", "a", "b", "c", "d", "e", "f"]
    raw_parameters = _field_value(curve_data.get("parameters"), [])
    if isinstance(raw_parameters, dict):
        return [_to_float(raw_parameters[name]) for name in names if name in raw_parameters]
    return [_to_float(value) for value in raw_parameters]


def _resolved_parametric_formula(function_type: int, parameters: Sequence[float]) -> str:
    """Substitute numeric ICC parametric parameters into the selected formula."""
    params = list(parameters) + [0.0] * 7
    g, a, b, c, d, e, f = params[:7]
    base = f"({_format_number(a)}*x + {_format_number(b)})^{_format_number(g)}"
    if function_type == 0:
        return f"y = x^{_format_number(g)}"
    if function_type == 1:
        threshold = _format_threshold(b, a)
        return f"y = {base} if {threshold} else 0"
    if function_type == 2:
        threshold = _format_threshold(b, a)
        return f"y = {base} + {_format_number(c)} if {threshold} else {_format_number(c)}"
    if function_type == 3:
        return f"y = {base} if x >= {_format_number(d)} else {_format_number(c)}*x"
    if function_type == 4:
        return (
            f"y = {base} + {_format_number(e)} if x >= {_format_number(d)} "
            f"else {_format_number(c)}*x + {_format_number(f)}"
        )
    return "y = x"


def _curve_type_formula_text(count: int, curve_values: Sequence[float]) -> str:
    """Describe ICC curveType as identity, gamma formula, or sampled 1D LUT."""
    if count == 0:
        return "curveType: identity\nresolved: y = x"
    if count == 1 and curve_values:
        gamma = curve_values[0]
        return (
            "curveType: gamma\n"
            "generic: y = x^g\n"
            f"resolved: y = x^{_format_number(gamma)}\n"
            f"parameters: g={_format_number(gamma)}"
        )
    if curve_values:
        return f"curveType: sampled 1D LUT\nentries: {len(curve_values)}; y = LUT(x) by interpolation"
    return "curveType: empty\nresolved: y = x"


def _format_threshold(b_value: float, a_value: float) -> str:
    """Format the parametric branch threshold, avoiding division by zero text."""
    if a_value == 0:
        return "x >= -b/a"
    return f"x >= {_format_number(-b_value / a_value)}"


def _format_number(value: float) -> str:
    """Format compact numeric values for formula labels."""
    return f"{_to_float(value):.6g}"


def _to_float(value: Any) -> float:
    """Convert parsed scalar/list/numpy values to a plain float."""
    value = _field_value(value, value)
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return 0.0
        return float(value.reshape(-1)[0])
    if isinstance(value, (list, tuple)):
        if not value:
            return 0.0
        return _to_float(value[0])
    return float(value)


def _curve_channel_count(curve_data: dict) -> int:
    """Infer channel count from a mAB/mBA curve block byte size."""
    bytesize = int(curve_data.get("bytesize", 0) or 0)
    datatype = str(_field_value(curve_data.get("type_signature"), curve_data.get("datatype", "")))
    if bytesize <= 0:
        return 1
    if datatype == "para" or "function_type" in curve_data:
        parameters = _field_value(curve_data.get("parameters"), [])
        single_size = 12 + max(1, len(parameters)) * 4
        return max(1, bytesize // single_size)
    count = int(_field_value(curve_data.get("count"), 0) or 0)
    single_size = 12 if count == 0 else 14 if count == 1 else 12 + count * 2
    return max(1, bytesize // single_size)


def _rgb_xyz_matrix(tag_data: dict) -> List[float]:
    """Build a 3x3 RGB-to-PCSXYZ matrix from rXYZ/gXYZ/bXYZ tags."""
    columns = []
    for tag_name in ("rXYZ", "gXYZ", "bXYZ"):
        tag = _as_dict(tag_data.get(tag_name))
        xyz = _field_value(tag.get("value"), None)
        if xyz is None:
            values = _field_value(tag.get("values"), [])
            xyz = values[0] if values else (0.0, 0.0, 0.0)
        columns.append([float(value) for value in xyz])
    return [
        columns[0][0], columns[1][0], columns[2][0],
        columns[0][1], columns[1][1], columns[2][1],
        columns[0][2], columns[1][2], columns[2][2],
    ]


def _inverse_3x3(values: Sequence[float]) -> List[float]:
    """Return inverse matrix values, or original values if singular."""
    if len(values) != 9:
        return list(values)
    try:
        matrix = np.array(values, dtype=float).reshape((3, 3))
        return np.linalg.inv(matrix).reshape(-1).tolist()
    except np.linalg.LinAlgError:
        return list(values)


def _sample_clut_output_points(
    grid_points: Sequence[int],
    output_channels: int,
    values: Sequence[float],
) -> Tuple[np.ndarray, np.ndarray]:
    """Sample CLUT output values as positions and input-grid RGB as point colors."""
    total_points = _clut_point_count(grid_points, output_channels, values)
    step = max(1, total_points // 1200)
    positions = []
    colors = []
    gx, gy, gz = grid_points[:3]
    for point_index in range(0, total_points, step):
        position = _clut_output_position(point_index, output_channels, values, dimensions=3)
        _, color = _clut_rgb_position_and_color(point_index, (gx, gy, gz))
        positions.append(position)
        colors.append(color)
    return np.array(positions, dtype=float), np.array(colors, dtype=float)


def _clut_point_count(
    grid_points: Sequence[int],
    output_channels: int,
    values: Sequence[float],
) -> int:
    """Return drawable CLUT point count from grid dimensions and value length."""
    value_points = len(values) // max(1, output_channels)
    if len(grid_points) < 3:
        return value_points
    grid_total = int(np.prod(grid_points[:3]))
    return min(grid_total, value_points) if value_points else grid_total


def _clut_output_position(
    point_index: int,
    output_channels: int,
    values: Sequence[float],
    dimensions: int,
) -> List[float]:
    """Return one CLUT output tuple padded/clamped for plotting."""
    start = point_index * max(1, output_channels)
    channels = [float(value) for value in values[start:start + max(1, output_channels)]]
    if not channels:
        channels = [0.0]
    padded = channels + [channels[-1]] * max(0, dimensions - len(channels))
    return [_clamp01(value) for value in padded[:dimensions]]


def _clut_rgb_position_and_color(point_index: int, grid_points: Sequence[int]) -> Tuple[List[float], Tuple[float, float, float, float]]:
    """Return one CLUT input-grid position and its display RGB color."""
    gx, gy, gz = (list(grid_points[:3]) + [1, 1, 1])[:3]
    z_index = point_index % max(1, gz)
    y_index = (point_index // max(1, gz)) % max(1, gy)
    x_index = (point_index // max(1, gy * gz)) % max(1, gx)
    position = [
        x_index / max(1, gx - 1),
        y_index / max(1, gy - 1),
        z_index / max(1, gz - 1),
    ]
    return position, _visible_rgb_color(position)


def _visible_rgb_color(rgb_values: Sequence[float]) -> Tuple[float, float, float, float]:
    """Return an RGB color that remains visible on a white background."""
    red, green, blue = (_clamp01(rgb_values[0]), _clamp01(rgb_values[1]), _clamp01(rgb_values[2]))
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    if luminance > 0.72:
        scale = 0.72 / max(luminance, 1e-6)
        red, green, blue = red * scale, green * scale, blue * scale
    return red, green, blue, 1.0


def _rgba_from_channels(channels: Sequence[float], as_tuple: bool = False):
    """Return a QColor or float RGBA tuple from CLUT output channels."""
    values = list(channels) + [channels[0] if channels else 0.0] * 3
    red, green, blue = (_clamp01(values[0]), _clamp01(values[1]), _clamp01(values[2]))
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    if luminance > 0.55:
        # Keep hue but darken very bright samples so they remain visible on a white background.
        scale = 0.55 / max(luminance, 1e-6)
        red, green, blue = red * scale, green * scale, blue * scale
    rgba = (red, green, blue, 1.0)
    if as_tuple:
        return rgba
    return QColor.fromRgbF(rgba[0], rgba[1], rgba[2], rgba[3])


def _clamp01(value: float) -> float:
    """Clamp numeric values into display range."""
    return max(0.0, min(1.0, float(value)))


def _figure_path(figure_name: str) -> str:
    """Return absolute path for a conversion-chain reference figure."""
    return os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "..",
        "resource",
        "ICC-Conversion-Chain",
        figure_name,
    ))
