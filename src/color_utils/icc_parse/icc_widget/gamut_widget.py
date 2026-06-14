"""ICC gamut visualization widget for parsed ICC profile data.

This module provides a standalone tab widget that reads parsed ICC JSON data,
extracts RGB primary XYZ tags and white points, then displays them on a CIE
1931 xy chromaticity diagram. It is intentionally independent from
GamutsViewer, which is a profile selection widget.
"""

import os
from typing import Any, Dict, List, Optional, Tuple

import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from icc_gamut_extract import WHITE_ILLUMINANTS_XY, build_gamut_data
    from icc_widget.copy_utils import install_copy_shortcut
    from icc_widget.conversion_chain_widget import ConversionChainWidget
    from icc_widget.i18n import DEFAULT_LANGUAGE, tr, tr_display
    from icc_widget.table_utils import configure_content_fit_table, refit_table_columns
except ImportError:
    from ..icc_gamut_extract import WHITE_ILLUMINANTS_XY, build_gamut_data
    from .copy_utils import install_copy_shortcut
    from .conversion_chain_widget import ConversionChainWidget
    from .i18n import DEFAULT_LANGUAGE, tr, tr_display
    from .table_utils import configure_content_fit_table, refit_table_columns


class ICCGamutWidget(QWidget):
    """Display an ICC RGB gamut on a CIE xy chromaticity diagram."""

    def __init__(self, parent=None):
        """Initialize the gamut widget.

        Args:
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self.gamut_data: Dict[str, Any] = {}
        self.language = DEFAULT_LANGUAGE
        self._init_ui()

    def _init_ui(self) -> None:
        """Create chromaticity and conversion-chain sub-tabs."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel()
        self.title_label.setObjectName("iccTitleLabel")
        layout.addWidget(self.title_label)

        self.content_tabs = QTabWidget()
        layout.addWidget(self.content_tabs, 1)

        chromaticity_tab = QWidget()
        chromaticity_layout = QVBoxLayout(chromaticity_tab)
        chromaticity_layout.setContentsMargins(0, 0, 0, 0)

        self.help_label = QLabel()
        self.help_label.setWordWrap(True)
        self.help_label.setObjectName("iccHelpLabel")
        chromaticity_layout.addWidget(self.help_label)

        splitter = QSplitter(Qt.Vertical)

        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        layer_layout = QHBoxLayout()
        layer_layout.setContentsMargins(0, 0, 0, 0)
        self.show_pcs_checkbox = QCheckBox()
        self.show_pcs_checkbox.setChecked(False)
        self.show_pcs_checkbox.toggled.connect(self._refresh_plot)
        self.show_source_checkbox = QCheckBox()
        self.show_source_checkbox.setChecked(True)
        self.show_source_checkbox.toggled.connect(self._refresh_plot)
        self.reset_view_button = QPushButton()
        self.reset_view_button.clicked.connect(self._reset_plot_view)
        layer_layout.addWidget(self.show_pcs_checkbox)
        layer_layout.addWidget(self.show_source_checkbox)
        layer_layout.addWidget(self.reset_view_button)
        layer_layout.addStretch(1)
        plot_layout.addLayout(layer_layout)
        self.canvas = GamutCanvas()
        plot_layout.addWidget(SquarePlotContainer(self.canvas), 1)
        splitter.addWidget(plot_container)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(len(tr("gamut.headers", self.language)))
        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        install_copy_shortcut(self.detail_table)
        configure_content_fit_table(
            self.detail_table,
            min_widths=[180, 250, 160, 180],
            max_widths=[300, 420, 240, 420],
        )

        splitter.addWidget(self.detail_table)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setSizes([560, 120])
        chromaticity_layout.addWidget(splitter, 1)

        self.content_tabs.addTab(chromaticity_tab, "")

        self.conversion_chain_widget = ConversionChainWidget()
        self.content_tabs.addTab(self.conversion_chain_widget, "")
        self.retranslate_ui()

    def set_language(self, language: str) -> None:
        """Switch this gamut widget between English and Chinese."""
        self.language = language
        self.retranslate_ui()
        self.canvas.set_language(language)
        self._refresh_plot()
        self._populate_table()
        self.conversion_chain_widget.set_language(language)

    def retranslate_ui(self) -> None:
        """Refresh static labels, sub-tab titles, and table headers."""
        self.title_label.setText(tr("gamut.title", self.language))
        self.help_label.setText(tr("gamut.help", self.language))
        self.show_pcs_checkbox.setText(tr("gamut.show_pcs", self.language))
        self.show_source_checkbox.setText(tr("gamut.show_source", self.language))
        self.reset_view_button.setText(tr("gamut.reset_view", self.language))
        self.detail_table.setHorizontalHeaderLabels(tr("gamut.headers", self.language))
        self.content_tabs.setTabText(0, tr("gamut.chromaticity", self.language))
        self.content_tabs.setTabText(1, tr("gamut.conversion_chain", self.language))
        refit_table_columns(self.detail_table)
        self._fit_detail_table_height()

    def set_profile_data(self, parsed_data: dict) -> None:
        """Refresh the gamut plot from parsed ICC data.

        Args:
            parsed_data: Parsed ICC dictionary, or None to clear the widget.
        """
        self.gamut_data = build_gamut_data(parsed_data or {}) if parsed_data else {}
        self._refresh_plot()
        self._populate_table()
        self.conversion_chain_widget.set_profile_data(parsed_data or {})

    def clear(self) -> None:
        """Clear current plot and table."""
        self.gamut_data = {}
        self._refresh_plot()
        self.detail_table.setRowCount(0)
        self._fit_detail_table_height()
        self.conversion_chain_widget.clear()

    def _refresh_plot(self) -> None:
        """Redraw the gamut plot using the current layer visibility options."""
        self.canvas.plot_gamut(
            self.gamut_data,
            show_pcs=self.show_pcs_checkbox.isChecked(),
            show_source=self.show_source_checkbox.isChecked(),
        )

    def _reset_plot_view(self) -> None:
        """Reset plot zoom and pan to the default chromaticity range."""
        self.canvas.reset_view()

    def _populate_table(self) -> None:
        """Fill the detail table with primary and white point rows."""
        self.detail_table.setRowCount(0)
        for row_index, row_data in enumerate(self.gamut_data.get("rows", [])):
            self.detail_table.insertRow(row_index)
            values = [
                tr_display(row_data.get("item", ""), self.language),
                row_data.get("xyz", ""),
                row_data.get("xy", ""),
                tr_display(row_data.get("note", ""), self.language),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.detail_table.setItem(row_index, column, item)
        self.detail_table.resizeRowsToContents()
        refit_table_columns(self.detail_table)
        self._fit_detail_table_height()

    def _fit_detail_table_height(self) -> None:
        """Limit the chromaticity detail table height to its visible text rows."""
        header_height = self.detail_table.horizontalHeader().height()
        row_height = sum(self.detail_table.rowHeight(row) for row in range(self.detail_table.rowCount()))
        frame_height = self.detail_table.frameWidth() * 2
        content_height = header_height + row_height + frame_height + 6
        self.detail_table.setMaximumHeight(max(header_height + frame_height + 12, content_height))


class SquarePlotContainer(QWidget):
    """Center a plot widget in a square area based on available space."""

    def __init__(self, plot_widget: QWidget, parent=None):
        """Create a square wrapper around an interactive plot widget.

        Args:
            plot_widget: Plot widget to resize as a square.
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self.plot_widget = plot_widget
        self.plot_widget.setParent(self)
        self.plot_widget.setMinimumSize(1, 1)
        self.plot_widget.setMaximumSize(16777215, 16777215)
        self.plot_widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def resizeEvent(self, event) -> None:
        """Keep the wrapped plot square and centered during layout changes."""
        super().resizeEvent(event)
        side = max(1, min(self.width(), self.height()))
        left = (self.width() - side) // 2
        top = (self.height() - side) // 2
        self.plot_widget.setGeometry(left, top, side, side)


class GamutCanvas(pg.PlotWidget):
    """PyQtGraph widget for interactive CIE xy gamut plotting."""

    def __init__(self, parent=None):
        """Initialize the interactive PyQtGraph plot widget."""
        pg.setConfigOptions(antialias=True)
        super().__init__(parent=parent)
        self.language = DEFAULT_LANGUAGE
        self.setBackground("w")
        self.showGrid(x=True, y=True, alpha=0.25)
        self.getViewBox().setAspectLocked(True)
        self.legend = self.addLegend(offset=(20, 20), labelTextColor="#333333", labelTextSize="12pt")
        self._init_axes()

    def set_language(self, language: str) -> None:
        """Switch plot labels between English and Chinese."""
        self.language = language

    def _init_axes(self) -> None:
        """Reset axes to the chromaticity diagram baseline."""
        fonts = _get_plot_font_sizes()
        self.clear()
        self.legend.clear()
        self.setTitle("")
        self.setLabel("bottom", "x", **{"font-size": f"{fonts['axis']}pt", "font-weight": "bold"})
        self.setLabel("left", "y", **{"font-size": f"{fonts['axis']}pt", "font-weight": "bold"})
        tick_font = QFont()
        tick_font.setPointSizeF(fonts["tick"])
        tick_font.setBold(True)
        label_font = QFont()
        label_font.setPointSizeF(fonts["axis"])
        label_font.setBold(True)
        for axis_name in ("bottom", "left"):
            axis = self.getAxis(axis_name)
            axis.setPen(pg.mkPen("#333333", width=2.0))
            axis.setTextPen(pg.mkPen("#333333"))
            axis.setStyle(tickFont=tick_font)
            axis.label.setFont(label_font)
        self.getViewBox().setBorder(pg.mkPen("#555555", width=1.5))
        self.reset_view()
        self._plot_spectral_locus()
        self._plot_illuminants()

    def reset_view(self) -> None:
        """Restore the default CIE xy plot range."""
        self.setXRange(0.0, 0.8, padding=0.02)
        self.setYRange(0.0, 0.9, padding=0.02)

    def plot_gamut(self, gamut_data: Dict[str, Any], show_pcs: bool = True, show_source: bool = True) -> None:
        """Plot primary triangles and white points."""
        self._init_axes()
        if not gamut_data:
            self._add_center_message(tr("gamut.no_profile", self.language))
            return

        if not show_pcs and not show_source:
            self._add_center_message(tr("gamut.no_layers", self.language))
            return

        pcs_points = gamut_data.get("pcs_points", [])
        plotted_pcs = show_pcs and bool(pcs_points)
        if plotted_pcs:
            self._plot_triangle(pcs_points, tr("gamut.pcs_primaries", self.language), "-", "#555555")
            for point in pcs_points:
                self._plot_point(
                    point["xy"],
                    tr_display(point["label"], self.language),
                    point["color"],
                    point["color"],
                    text_color=point["color"],
                )

        source_points = gamut_data.get("source_points", [])
        plotted_source = show_source and bool(source_points)
        if plotted_source:
            self._plot_triangle(source_points, tr("gamut.source_primaries", self.language), "--", "#8e24aa")
            for point in source_points:
                label = tr("gamut.source_label_prefix", self.language).format(label=tr_display(point["label"], self.language))
                self._plot_point(point["xy"], label, point["color"], point["color"], marker="x", text_color=point["color"])

        media_white = gamut_data.get("media_white")
        if show_pcs and media_white:
            self._plot_point(
                media_white["xy"],
                tr("gamut.media_white_point", self.language),
                "white",
                "#333333",
                size=70,
                show_near=True,
                text_color="#111111",
            )

        source_white = gamut_data.get("source_white")
        if show_source and source_white:
            self._plot_point(
                source_white["xy"],
                tr("gamut.source_white_point", self.language),
                "#fff3e0",
                "#ef6c00",
                size=70,
                show_near=True,
                text_color="#111111",
            )

    def _plot_triangle(self, points: List[Dict[str, Any]], label: str, linestyle: str, color: str) -> None:
        """Draw a closed RGB primary triangle."""
        xy_points = [point["xy"] for point in points if point.get("xy")]
        if len(xy_points) != 3:
            return
        closed = xy_points + [xy_points[0]]
        xs = [point[0] for point in closed]
        ys = [point[1] for point in closed]
        line = self.plot(
            xs,
            ys,
            pen=_make_pen(color, width=3.0, linestyle=linestyle),
        )
        self.legend.addItem(line, label)

    def _plot_point(
        self,
        xy: Optional[Tuple[float, float]],
        label: str,
        face_color: str,
        edge_color: str,
        marker: str = "o",
        size: int = 55,
        show_near: bool = False,
        text_color: str = "#333333",
        text_outline_color: Optional[str] = None,
    ) -> None:
        """Draw one labeled xy point."""
        if xy is None:
            return
        fonts = _get_plot_font_sizes()
        symbol = "x" if marker == "x" else "o"
        base_symbol_size = max(12, int(size ** 0.5 * 2.2))
        symbol_size = base_symbol_size * 2 if marker == "x" else base_symbol_size
        self.plot(
            [xy[0]],
            [xy[1]],
            pen=None,
            symbol=symbol,
            symbolSize=symbol_size,
            symbolBrush=pg.mkBrush(face_color),
            symbolPen=_make_pen(edge_color, width=2.0),
        )
        self._add_point_label(
            _format_point_label(label, xy, show_near),
            xy[0],
            xy[1] + 0.015,
            text_color,
            fonts["label"],
            text_outline_color,
        )

    def _add_point_label(
        self,
        text: str,
        x_value: float,
        y_value: float,
        color: str,
        font_size: float,
        outline_color: Optional[str] = None,
    ) -> None:
        """Add a point label, optionally using small offsets as a dark outline."""
        if outline_color:
            for dx, dy in ((-0.002, 0.0), (0.002, 0.0), (0.0, -0.002), (0.0, 0.002)):
                outline = pg.TextItem(text, color=outline_color, anchor=(0.5, 1.0))
                outline.setFont(_make_qfont(font_size, bold=True))
                outline.setPos(x_value + dx, y_value + dy)
                self.addItem(outline)
        label_item = pg.TextItem(text, color=color, anchor=(0.5, 1.0))
        label_item.setFont(_make_qfont(font_size, bold=True))
        label_item.setPos(x_value, y_value)
        self.addItem(label_item)

    def _plot_illuminants(self) -> None:
        """Draw standard illuminant reference points."""
        fonts = _get_plot_font_sizes()
        for name, xy in WHITE_ILLUMINANTS_XY.items():
            if name not in {"A", "C", "D50", "D55", "D65", "D75", "E", "F2", "F7", "F11"}:
                continue
            self.plot(
                [xy[0]],
                [xy[1]],
                pen=None,
                symbol="o",
                symbolSize=7,
                symbolBrush=pg.mkBrush(QColor(158, 158, 158, 165)),
                symbolPen=None,
            )
            text = pg.TextItem(name, color="#757575", anchor=(0.5, 0.0))
            text.setFont(_make_qfont(fonts["small"], bold=True))
            text.setPos(xy[0], xy[1] - 0.018)
            self.addItem(text)

    def _plot_spectral_locus(self) -> None:
        """Draw the CIE spectral locus when the local CSV resource is available."""
        csv_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "resource",
            "CIEdata",
            "cie_1931_2deg_xyz_cc.csv",
        ))
        points = _read_spectral_locus_xy(csv_path)
        if not points:
            return
        closed = points + [points[0]]
        self.plot(
            [p[0] for p in closed],
            [p[1] for p in closed],
            pen=_make_pen("#90a4ae", width=6.0, alpha=204),
        )

    def _add_center_message(self, message: str) -> None:
        """Show a centered plot message."""
        text = pg.TextItem(message, color="#333333", anchor=(0.5, 0.5))
        text.setFont(_make_qfont(_get_plot_font_sizes()["label"], bold=True))
        text.setPos(0.4, 0.45)
        self.addItem(text)


def _read_spectral_locus_xy(csv_path: str) -> List[Tuple[float, float]]:
    """Read x/y columns from the local CIE 1931 chromaticity CSV file."""
    if not os.path.exists(csv_path):
        return []

    points: List[Tuple[float, float]] = []
    with open(csv_path, "r", encoding="utf-8") as file_obj:
        header = file_obj.readline().strip().split(",")
        try:
            x_index = header.index("x")
            y_index = header.index("y")
        except ValueError:
            return []

        for line in file_obj:
            parts = line.strip().split(",")
            if len(parts) <= max(x_index, y_index):
                continue
            try:
                points.append((float(parts[x_index]), float(parts[y_index])))
            except ValueError:
                continue
    return points


def _get_plot_font_sizes() -> Dict[str, float]:
    """Return plot font sizes derived from the current Qt application font."""
    base_pt = QApplication.font().pointSizeF()
    if base_pt <= 0:
        base_pt = 9.0

    body_pt = max(10.0, min(base_pt + 1.0, 12.0))
    return {
        "title": max(12.0, min(body_pt + 2.0, 15.0)),
        "axis": max(13.0, min(body_pt + 2.0, 15.0)),
        "tick": max(12.0, min(body_pt + 1.0, 14.0)),
        "label": max(10.0, min(body_pt, 12.0)),
        "legend": max(11.0, min(body_pt, 13.0)),
        "small": max(7.5, min(body_pt - 2.5, 9.5)),
    }


def _format_point_label(label: str, xy: Tuple[float, float], show_near: bool = False) -> str:
    """Return a compact point label with xy coordinates and optional illuminant hint."""
    parts = [f"x={xy[0]:.4f}", f"y={xy[1]:.4f}"]
    if show_near:
        near_illuminant = _get_near_illuminant(xy)
        if near_illuminant:
            parts.append(near_illuminant)
    return f"{label}\n({', '.join(parts)})"


def _get_near_illuminant(xy_value: Tuple[float, float]) -> str:
    """Return the nearest named illuminant by xy Euclidean distance."""
    nearest_name = ""
    min_distance = None
    x_value, y_value = float(xy_value[0]), float(xy_value[1])
    for illuminant, illuminant_xy in WHITE_ILLUMINANTS_XY.items():
        dx = x_value - illuminant_xy[0]
        dy = y_value - illuminant_xy[1]
        distance = (dx * dx + dy * dy) ** 0.5
        if min_distance is None or distance < min_distance:
            min_distance = distance
            nearest_name = illuminant

    return f"Near {nearest_name}" if nearest_name else ""


def _make_qfont(point_size: float, bold: bool = False) -> QFont:
    """Create a Qt font for PyQtGraph text items."""
    font = QFont()
    font.setPointSizeF(point_size)
    font.setBold(bold)
    return font


def _make_pen(color: str, width: float = 1.0, linestyle: str = "-", alpha: int = 255) -> QPen:
    """Create a PyQtGraph pen with optional dashed style."""
    qcolor = QColor(color)
    qcolor.setAlpha(alpha)
    pen = pg.mkPen(qcolor, width=width)
    if linestyle == "--":
        pen.setStyle(Qt.DashLine)
    return pen
