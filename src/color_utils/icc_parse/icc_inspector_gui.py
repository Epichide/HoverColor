#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ICC Inspector GUI - PyQt5 Version.

This module provides a desktop UI for importing ICC/JSON data and browsing
profile header fields, tag metadata, and parsed tag payloads.
"""

import os
import sys
import json
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
                             QLabel, QPushButton, QFileDialog, QMessageBox, QTabWidget,
                             QSplitter, QMenuBar, QMenu, QAction, QToolBar, QStatusBar,
                             QHeaderView, QActionGroup)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QIcon, QColor
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_binary import parse_icc_binary
from icc_serialize import to_json_compatible
from iccinspector_builtin import load_icc, save_icc, warp_file
from icc_widget.copy_utils import install_copy_shortcut
from icc_widget.gamut_widget import ICCGamutWidget
from icc_widget.i18n import DEFAULT_LANGUAGE, tr
from icc_widget.summary_widget import ICCSummaryWidget
from icc_widget.table_utils import configure_content_fit_table, configure_copyable_tree, refit_table_columns


METADATA_KEYS = {'offset', 'bytesize', 'datatype', 'datasize'}


class ICCInspectorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.source_origin = None  # 'icc', 'image', 'json'
        self.parsed_data = None
        self.language = DEFAULT_LANGUAGE
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('ICC Inspector')
        self.setGeometry(100, 100, 1200, 700)
        
        # Central widget - single tab widget for all tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Tab widget containing all views
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # ===== Tab 1: ICC Summary =====
        self.summary_widget = ICCSummaryWidget()
        self.tab_widget.addTab(self.summary_widget, tr('tab.summary', self.language))

        # ===== Tab 2: Profile Info =====
        profile_tab = QWidget()
        profile_layout = QVBoxLayout(profile_tab)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter between basic and header info (vertical, stretchable)
        splitter = QSplitter(Qt.Vertical)
        
        # Basic Info container (top panel in splitter)
        basic_container = QWidget()
        basic_container_layout = QVBoxLayout(basic_container)
        basic_container_layout.setContentsMargins(0, 0, 0, 0)
        basic_container_layout.addWidget(QLabel('<b>Basic Info</b>'))
        self.basic_table = QTableWidget()
        self.basic_table.setColumnCount(2)
        self.basic_table.setHorizontalHeaderLabels(tr('table.basic.headers', self.language))
        self.basic_table.verticalHeader().setVisible(False)
        self.basic_table.setEditTriggers(QTableWidget.NoEditTriggers)
        install_copy_shortcut(self.basic_table)
        configure_content_fit_table(self.basic_table, min_widths=[130, 180], max_widths=[260, 520])
        
        basic_container_layout.addWidget(self.basic_table)
        
        # Header info table inside splitter (bottom panel)
        header_container = QWidget()
        header_container_layout = QVBoxLayout(header_container)
        header_container_layout.setContentsMargins(0, 0, 0, 0)
        header_container_layout.addWidget(QLabel('<b>Header Info</b>'))
        self.header_table = QTableWidget()
        self.header_table.setColumnCount(6)
        self.header_table.setHorizontalHeaderLabels(tr('table.detail.headers', self.language))
        self.header_table.verticalHeader().setVisible(False)
        self.header_table.setEditTriggers(QTableWidget.NoEditTriggers)
        install_copy_shortcut(self.header_table)
        configure_content_fit_table(
            self.header_table,
            min_widths=[130, 180, 70, 90, 100, 80],
            max_widths=[260, 420, 110, 130, 180, 120],
        )
        
        header_container_layout.addWidget(self.header_table)
        
        # Add both containers to splitter
        splitter.addWidget(basic_container)
        splitter.addWidget(header_container)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        # Set initial sizes: prefer showing basic info (smaller initially)
        splitter.setSizes([200, 400])
        
        profile_layout.addWidget(splitter, 1)
        
        self.tab_widget.addTab(profile_tab, 'Profile Info')
        
        # ===== Tab 3: Tags & Tag Details (combined with horizontal splitter) =====
        tag_combined_tab = QWidget()
        tag_combined_layout = QHBoxLayout(tag_combined_tab)
        tag_combined_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left panel: Tags list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel('<b>Tags</b>'))
        self.tag_tree = QTreeWidget()
        self.tag_tree.setHeaderLabel(tr('table.tag_name.header', self.language))
        self.tag_tree.itemClicked.connect(self.on_tag_select)
        configure_copyable_tree(self.tag_tree, select_items=False)
        install_copy_shortcut(self.tag_tree)
        left_layout.addWidget(self.tag_tree)
        
        # Right panel: Tag details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.tag_detail_label = QLabel('<b>Tag Details</b>')
        right_layout.addWidget(self.tag_detail_label)
        
        # Tag tree with expandable nodes (Item, Value, Offset, Bytesize, Datatype, Datasize)
        self.tag_tree_view = QTreeWidget()
        self.tag_tree_view.setHeaderLabels(tr('table.detail.headers', self.language))
        self.tag_tree_view.setColumnWidth(0, 300)
        self.tag_tree_view.setAlternatingRowColors(True)
        configure_copyable_tree(self.tag_tree_view, select_items=True)
        install_copy_shortcut(self.tag_tree_view)
        # Make columns interactive (user can resize) and stretch last section to fill visible widget width
        for c in range(6):
            self.tag_tree_view.header().setSectionResizeMode(c, QHeaderView.Interactive)
        self.tag_tree_view.header().setStretchLastSection(True)
        right_layout.addWidget(self.tag_tree_view)
        
        # Horizontal splitter between left (tags) and right (details)
        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.addWidget(left_panel)
        h_splitter.addWidget(right_panel)
        h_splitter.setCollapsible(0, False)
        h_splitter.setCollapsible(1, False)
        h_splitter.setSizes([250, 650])  # Prefer more space for details
        
        tag_combined_layout.addWidget(h_splitter)
        self.tab_widget.addTab(tag_combined_tab, 'Tags & Details')

        # ===== Tab 4: Gamut =====
        self.gamut_widget = ICCGamutWidget()
        self.tab_widget.addTab(self.gamut_widget, tr('tab.gamut', self.language))
        
        main_layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        # Label to show current imported file (left side)
        self.status_file_label = QLabel('No file')
        self.status_file_label.setMinimumWidth(180)
        self.status_file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_bar.addWidget(self.status_file_label)
        self.status_bar.showMessage('Ready')
        # Create menu bar after status bar so status label exists for actions
        self.create_menu_bar()
        self.load_stylesheet()

    def load_stylesheet(self):
        """Load ICC Inspector stylesheet from the local resource/css directory."""
        css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resource', 'css', 'icc_inspector.css')
        if not os.path.exists(css_path):
            return
        with open(css_path, 'r', encoding='utf-8') as css_file:
            style = css_file.read()

        font_sizes = self._get_adaptive_font_sizes()
        for name, value in font_sizes.items():
            style = style.replace(f"__{name}__", str(value))
        self.setStyleSheet(style)

        # Force tab/menu fonts via setFont so the new sizes actually apply
        # even on platforms where QSS font-size on QMenuBar is ignored.
        tab_font = QFont()
        tab_font.setPointSizeF(float(font_sizes['TAB_FONT_PT']))
        self.menuBar().setFont(tab_font)
        for menu in self.menuBar().findChildren(QMenu):
            menu.setFont(tab_font)
        for tabs in self.findChildren(QTabWidget):
            tabs.tabBar().setFont(tab_font)
        self.statusBar().setFont(tab_font)
        print(
            "ICC_INSPECTOR_FONT_SIZES:",
            f"base={font_sizes['BASE_FONT_PT']}pt",
            f"tab={font_sizes['TAB_FONT_PT']}pt",
            f"body={font_sizes['BODY_FONT_PT']}pt",
            f"table={font_sizes['TABLE_FONT_PT']}pt",
            f"title={font_sizes['TITLE_FONT_PT']}pt",
        )

    def _get_adaptive_font_sizes(self):
        """Return UI font sizes derived from the current Qt application font."""
        base_font = QApplication.font()
        base_pt = base_font.pointSizeF()
        if base_pt <= 0:
            base_pt = 9.0

        # Keep tabs compact, while making content/table slightly more readable.
        tab_pt = max(8.0, min(base_pt - 1.0, 9.0))
        body_pt = max(9.5, min(base_pt + 0.5, 11.0))
        table_pt = max(9.5, min(base_pt + 1.0, 11.5))
        title_pt = max(11.0, min(body_pt + 1.5, 13.5))

        return {
            "BASE_FONT_PT": round(base_pt, 1),
            "TAB_FONT_PT": round(tab_pt, 1),
            "BODY_FONT_PT": round(body_pt, 1),
            "TABLE_FONT_PT": round(table_pt, 1),
            "TITLE_FONT_PT": round(title_pt, 1),
        }
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Import submenu
        import_menu = file_menu.addMenu('Import')

        import_icc_action = QAction('Import ICC File...', self)
        import_icc_action.triggered.connect(self.import_icc)
        import_menu.addAction(import_icc_action)

        import_json_action = QAction('Import JSON File...', self)
        import_json_action.triggered.connect(self.import_json)
        import_menu.addAction(import_json_action)

        import_img_action = QAction('Import Image (extract ICC)...', self)
        import_img_action.triggered.connect(self.import_image)
        import_menu.addAction(import_img_action)

        # Export submenu
        export_menu = file_menu.addMenu('Export')
        export_json_action = QAction('Export JSON...', self)
        export_json_action.setShortcut('Ctrl+S')
        export_json_action.triggered.connect(self.export_json)
        export_menu.addAction(export_json_action)

        export_excel_action = QAction('Export Excel...', self)
        export_excel_action.triggered.connect(self.export_excel)
        export_menu.addAction(export_excel_action)
        
        export_icc_action = QAction('Export ICC...', self)
        export_icc_action.triggered.connect(self.export_icc)
        export_menu.addAction(export_icc_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Language menu switches selected user-facing table and tab text.
        self.language_menu = menubar.addMenu(tr('language.menu', self.language))
        self.language_action_group = QActionGroup(self)
        self.language_action_group.setExclusive(True)

        self.english_action = QAction(tr('language.english', self.language), self, checkable=True)
        self.english_action.setData('en')
        self.english_action.setChecked(self.language == 'en')
        self.english_action.triggered.connect(lambda checked=False: self.set_language('en'))
        self.language_action_group.addAction(self.english_action)
        self.language_menu.addAction(self.english_action)

        self.chinese_action = QAction(tr('language.chinese', self.language), self, checkable=True)
        self.chinese_action.setData('zh')
        self.chinese_action.setChecked(self.language == 'zh')
        self.chinese_action.triggered.connect(lambda checked=False: self.set_language('zh'))
        self.language_action_group.addAction(self.chinese_action)
        self.language_menu.addAction(self.chinese_action)

        # Help menu
        help_menu = menubar.addMenu('Help')
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def set_language(self, language):
        """Switch bilingual text for selected ICC inspector UI parts."""
        self.language = language
        self.tab_widget.setTabText(0, tr('tab.summary', self.language))
        self.tab_widget.setTabText(3, tr('tab.gamut', self.language))
        self.summary_widget.set_language(self.language)
        self.gamut_widget.set_language(self.language)
        self.retranslate_table_headers()
        self.language_menu.setTitle(tr('language.menu', self.language))
        self.english_action.setText(tr('language.english', self.language))
        self.chinese_action.setText(tr('language.chinese', self.language))
        self.english_action.setChecked(self.language == 'en')
        self.chinese_action.setChecked(self.language == 'zh')

    def retranslate_table_headers(self):
        """Refresh table/tree column names that are allowed to switch language."""
        self.basic_table.setHorizontalHeaderLabels(tr('table.basic.headers', self.language))
        self.header_table.setHorizontalHeaderLabels(tr('table.detail.headers', self.language))
        self.tag_tree.setHeaderLabel(tr('table.tag_name.header', self.language))
        self.tag_tree_view.setHeaderLabels(tr('table.detail.headers', self.language))
        refit_table_columns(self.basic_table)
        refit_table_columns(self.header_table)
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Open ICC File', '', 
            'ICC Profile (*.icc *.icm);;All Files (*.*)'
        )
        
        if not file_path:
            return
            
        self.open_file_from_path(file_path)
            
    def load_profile_info(self):
        # Basic info
        self.basic_table.setRowCount(0)
        basic_info = [
            ('Parser', self.parsed_data.get('parser', 'N/A')),
            ('File Path', self.parsed_data.get('file_path', 'N/A')),
            ('File Size', str(self.parsed_data.get('file_size', 0)) + ' bytes'),
            ('Tag Count', str(self.parsed_data.get('tag_count', 0))),
        ]
        for row, (name, value) in enumerate(basic_info):
            self.basic_table.insertRow(row)
            self.basic_table.setItem(row, 0, QTableWidgetItem(name))
            self.basic_table.setItem(row, 1, QTableWidgetItem(str(value)))
        refit_table_columns(self.basic_table)
        
        # Header info - display list format: [value, offset, bytesize, datatype, datasize]
        self.header_table.setRowCount(0)
        header = self.parsed_data.get('header', {})
        
        # Header fields in desired order
        header_fields = [
            'profile_size', 'preferred_cmm', 'version', 'device_class',
            'color_space', 'pcs', 'datetime', 'signature', 'primary_platform',
            'flags', 'device_manufacturer', 'device_model', 'device_attributes',
            'rendering_intent', 'illuminant_xyz', 'creator'
        ]

        for field_name in header_fields:
            if field_name in header:
                field_data = header[field_name]
                if isinstance(field_data, list) and len(field_data) >= 5:
                    # Format: [value, offset, bytesize, datatype, datasize]
                    value, offset, bytesize, datatype, datasize = field_data[:5]
                    display_value = str(value) if not isinstance(value, (dict, list)) else str(value)
                    self.header_table.insertRow(self.header_table.rowCount())
                    row = self.header_table.rowCount() - 1
                    self.header_table.setItem(row, 0, QTableWidgetItem(field_name))
                    self.header_table.setItem(row, 1, QTableWidgetItem(display_value))
                    self.header_table.setItem(row, 2, QTableWidgetItem(str(offset)))
                    self.header_table.setItem(row, 3, QTableWidgetItem(str(bytesize)))
                    self.header_table.setItem(row, 4, QTableWidgetItem(str(datatype)))
                    self.header_table.setItem(row, 5, QTableWidgetItem(str(datasize)))
        
        refit_table_columns(self.header_table)
        
    def load_tag_list(self):
        self.tag_tree.clear()
        tags = self.parsed_data.get('tags', {})
        for tag_name in sorted(tags.keys()):
            tag_meta = tags.get(tag_name, {})
            tag_type = tag_meta.get('type') if isinstance(tag_meta, dict) else None
            label = f"{tag_name} ({tag_type})" if tag_type else tag_name
            item = QTreeWidgetItem(self.tag_tree, [label])
            item.setData(0, Qt.UserRole, tag_name)
            self.tag_tree.addTopLevelItem(item)
            
    def on_tag_select(self, item, column):
        tag_name = item.data(0, Qt.UserRole) or item.text(0)
        tag_data = self.parsed_data.get('tag_data', {}).get(tag_name, {})
        tag_meta = self.parsed_data.get('tags', {}).get(tag_name, {})

        self.tag_detail_label.setText(f'<b>Tag: {tag_name}</b>')

        # Fill tag tree
        self.tag_tree_view.clear()

        # Summary row: show tag as a single row with metadata in columns
        tag_payload_meta = tag_data if isinstance(tag_data, dict) else {}

        offset = tag_payload_meta.get('offset')
        if offset is None:
            offset = _field_value(tag_meta.get('data_offset')) if tag_meta else None
        if offset is None:
            offset = tag_meta.get('offset') if tag_meta else None

        size = tag_payload_meta.get('bytesize')
        if size is None:
            size = _field_value(tag_meta.get('data_size')) if tag_meta else None
        if size is None:
            size = tag_meta.get('size') if tag_meta else None

        dtype = tag_payload_meta.get('datatype')
        if dtype is None:
            dtype = tag_meta.get('type') if tag_meta else None

        datasize = tag_payload_meta.get('datasize', '')

        summary_cols = [
            tag_name,
            '',
            _format_optional(offset),
            _format_optional(size),
            _format_optional(dtype),
            _format_optional(datasize)
        ]

        summary = QTreeWidgetItem(self.tag_tree_view, _tree_cols(summary_cols))

        # Then add parsed value as child rows under the summary
        self._fill_tag_tree(summary, tag_data, 'value')
        # Expand summary and all children by default
        summary.setExpanded(True)
        self.tag_tree_view.expandAll()
        
    def _fill_tag_tree(self, parent, data, key_name=''):
        """递归填充树形结构"""
        if _is_parsed_field(data):
            values = [
                key_name,
                _format_display_value(data.get('value')),
                _format_optional(data.get('offset')),
                _format_optional(data.get('bytesize')),
                _format_optional(data.get('datatype')),
                _format_optional(data.get('datasize')),
            ]
            if parent is None:
                QTreeWidgetItem(self.tag_tree_view, _tree_cols(values))
            else:
                QTreeWidgetItem(parent, _tree_cols(values))
            return

        # If data is a dict, show each key as a row with columns
        if isinstance(data, dict):
            # Container-level metadata is shown in the row columns, not repeated as children.
            display_items = ((k, v) for k, v in data.items() if k not in METADATA_KEYS)
            for k, v in display_items:
                # Create row with Item and Value; other columns empty by default
                if parent is None:
                    row = QTreeWidgetItem(self.tag_tree_view, _tree_cols([k, '' , '', '', '', '']))
                else:
                    row = QTreeWidgetItem(parent, _tree_cols([k, '' , '', '', '', '']))

                # If value is simple, put into Value column; if complex, show metadata in columns and recurse
                if _is_parsed_field(v):
                    row.setText(1, _format_display_value(v.get('value')))
                    row.setText(2, _format_optional(v.get('offset')))
                    row.setText(3, _format_optional(v.get('bytesize')))
                    row.setText(4, _format_optional(v.get('datatype')))
                    row.setText(5, _format_optional(v.get('datasize')))
                elif isinstance(v, (str, int, float, bool)) or v is None:
                    row.setText(1, str(v))
                elif isinstance(v, list) and all(isinstance(x, (int, float, str)) for x in v):
                    row.setText(1, _format_display_value(v))
                elif isinstance(v, dict):
                    # If dict contains metadata keys, extract them into columns
                    offset = v.get('offset')
                    bytesize = v.get('bytesize')
                    dtype = v.get('datatype')
                    datasize = v.get('datasize')
                    if offset is not None:
                        row.setText(2, str(offset))
                    if bytesize is not None:
                        row.setText(3, str(bytesize))
                    if dtype is not None:
                        row.setText(4, str(dtype))
                    if datasize is not None:
                        row.setText(5, str(datasize))

                    # Recurse on dict contents but skip metadata keys so they don't appear as separate child rows
                    child_copy = {k: vv for k, vv in v.items() if k not in METADATA_KEYS}
                    if child_copy:
                        self._fill_tag_tree(row, child_copy, '')
                else:
                    # fallback: complex type
                    self._fill_tag_tree(row, v, '')
            return
        elif isinstance(data, dict):
            # handled above
            return
        elif isinstance(data, list):
            if all(isinstance(item, (int, float, str)) for item in data):
                values_str = _format_display_value(data)
                if parent is None:
                    QTreeWidgetItem(self.tag_tree_view, _tree_cols([key_name, values_str, '', '', '', '']))
                else:
                    QTreeWidgetItem(parent, _tree_cols([key_name, values_str, '', '', '', '']))
            else:
                cols = _tree_cols([key_name + f' [{len(data)} items]', '', '', '', ''])
                node = QTreeWidgetItem(parent, cols) if parent else QTreeWidgetItem(self.tag_tree_view, cols)
                for i, item in enumerate(data):
                    self._fill_tag_tree(node, item, f'[{i}]')
        else:
            # Simple value
            if parent is None:
                QTreeWidgetItem(self.tag_tree_view, _tree_cols([key_name, data, '', '', '', '']))
            else:
                QTreeWidgetItem(parent, _tree_cols([key_name, data, '', '', '', '']))
            
    def export_json(self):
        if not self.parsed_data:
            QMessageBox.warning(self, 'Warning', 'Please open an ICC file first')
            return
            
        # Default filename based on current ICC file
        icc_name = os.path.splitext(os.path.basename(self.current_file))[0] if self.current_file else 'profile'
        default_name = icc_name + '_parsed.json'
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export JSON', default_name, 'JSON Files (*.json)'
        )
        
        if not file_path:
            return
            
        try:
            export_data = to_json_compatible(self.parsed_data)
            export_data['export_time'] = datetime.now().isoformat()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, 'Success', f'Exported to:\n{file_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Export failed:\n{str(e)}')

    def export_excel(self):
        """Export parsed ICC data to a multi-sheet Excel workbook."""
        if not self.parsed_data:
            QMessageBox.warning(self, 'Warning', 'Please import a profile first')
            return

        icc_name = os.path.splitext(os.path.basename(self.current_file))[0] if self.current_file else 'profile'
        default_name = icc_name + '_parsed.xlsx'

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export Excel', default_name, 'Excel Files (*.xlsx)'
        )

        if not file_path:
            return

        try:
            from icc_export_excel import export_to_excel

            export_to_excel(self.parsed_data, file_path)
            QMessageBox.information(self, 'Success', f'Exported Excel to:\n{file_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Excel export failed:\n{str(e)}')

    def export_icc(self):
        """Export ICC file. Only supported when source was ICC or image import."""
        if not self.parsed_data:
            QMessageBox.warning(self, 'Warning', 'Please import a profile first')
            return

        if self.source_origin == 'json' or self.current_file is None:
            QMessageBox.information(self, 'Not Supported', 'Converting JSON to ICC is not supported yet — coming soon.')
            return

        # current_file should be path to ICC when origin is 'icc' or 'image'
        src_icc = self.current_file
        if not os.path.exists(src_icc):
            QMessageBox.critical(self, 'Error', 'Original ICC file not available for export')
            return

        icc_name = os.path.splitext(os.path.basename(src_icc))[0]
        default_name = icc_name + '.icc'
        file_path, _ = QFileDialog.getSaveFileName(self, 'Export ICC', default_name, 'ICC Profile (*.icc *.icm)')
        if not file_path:
            return

        try:
            shutil.copyfile(src_icc, file_path)
            QMessageBox.information(self, 'Success', f'ICC exported to:\n{file_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Export ICC failed:\n{str(e)}')
            
    def import_icc(self):
        """导入 ICC 文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Import ICC File', '', 
            'ICC Profile (*.icc *.icm);;All Files (*.*)'
        )
        
        if not file_path:
            return
        
        # 使用 open_file 的同样逻辑
        self.open_file_from_path(file_path)
        self.source_origin = 'icc'
        
    def import_json(self):
        """导入 JSON 文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Import JSON File', '', 
            'JSON Files (*.json);;All Files (*.*)'
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.parsed_data = json.load(f)
            self.current_file = file_path
            self.source_origin = 'json'

            self.summary_widget.set_profile_data(self.parsed_data)
            self.gamut_widget.set_profile_data(self.parsed_data)
            self.load_profile_info()
            self.load_tag_list()
            # update left status label with current imported file
            try:
                self.status_file_label.setText(os.path.basename(file_path))
                print('STATUS_LABEL_SET:', os.path.basename(file_path))
                QApplication.processEvents()
            except Exception:
                pass

            self.status_bar.showMessage(f'JSON Loaded: {os.path.basename(file_path)}')
            
        except Exception as e:
            import traceback
            QMessageBox.critical(self, 'Error', f'Failed to load JSON:\n{str(e)}\n\n{traceback.format_exc()}')
            
    def import_image(self):
        """导入图片文件，如果包含 ICC Profile 则提取"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Import Image File', '', 
            'Image Files (*.jpg *.jpeg *.png *.tiff *.bmp);;All Files (*.*)'
        )
        
        if not file_path:
            return
            
        try:
            # 使用 iccinspector_builtin 的 load_icc 函数提取 ICC
            prf = load_icc(file_path)
            
            if prf is None:
                QMessageBox.warning(self, 'No ICC Profile', f'No ICC profile found in image:\n{os.path.basename(file_path)}')
                return
            
            # 获取 profile description 作为文件名
            profile_description = prf.profile.profile_description if hasattr(prf.profile, 'profile_description') else None
            
            # 创建 temp 目录并保存 ICC
            temp_dir = os.path.join(os.getcwd(), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            if profile_description:
                icc_filename = f'extracted_{profile_description}.icc'
            else:
                img_name = os.path.splitext(os.path.basename(file_path))[0]
                icc_filename = f'extracted_{img_name}.icc'
            
            icc_path = os.path.join(temp_dir, icc_filename)
            save_icc(prf, icc_path)
            print(f'ICC extracted and saved to: {icc_path}')
            
            # 记住来源为 image，然后加载提取的 ICC 文件
            self.source_origin = 'image'
            # prepare a full descriptive status text and preserve it across open_file
            full_msg = f'Extracted ICC from image: {os.path.basename(file_path)} → temp/{icc_filename}'
            try:
                self.status_file_label.setText(full_msg)
                print('STATUS_LABEL_SET:', full_msg)
                QApplication.processEvents()
                # mark to preserve this exact label text during open_file_from_path
                self._preserve_status_label = True
            except Exception:
                pass
            self.open_file_from_path(icc_path)
            self.status_bar.showMessage(full_msg)
            
        except Exception as e:
            import traceback
            QMessageBox.critical(self, 'Error', f'Failed to extract ICC from image:\n{str(e)}\n\n{traceback.format_exc()}')
            
    def open_file_from_path(self, file_path):
        """从给定路径打开 ICC 文件（内部使用）"""
        try:
            # Parse ICC
            self.parsed_data = parse_icc_binary(file_path)
            self.current_file = file_path
            
            # Auto-save JSON to temp directory
            temp_dir = os.path.join(os.getcwd(), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            icc_name = os.path.splitext(os.path.basename(file_path))[0]
            json_path = os.path.join(temp_dir, icc_name + '_parsed.json')
            export_data = to_json_compatible(self.parsed_data)
            export_data['export_time'] = datetime.now().isoformat()
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            print('JSON auto-saved to:', json_path)

            self.summary_widget.set_profile_data(self.parsed_data)
            self.gamut_widget.set_profile_data(self.parsed_data)
            self.load_profile_info()
            self.load_tag_list()
            
            # update status label with current imported file
            try:
                if getattr(self, '_preserve_status_label', False):
                    # keep label as previously set (e.g. full extracted message)
                    try:
                        del self._preserve_status_label
                    except Exception:
                        pass
                    label_text = self.status_file_label.text()
                else:
                    if self.source_origin == 'image':
                        # fallback short extracted label
                        label_text = f'extracted_{icc_name}'
                    else:
                        label_text = os.path.basename(file_path)
                    self.status_file_label.setText(label_text)
                print('STATUS_LABEL_SET:', label_text)
                QApplication.processEvents()
            except Exception:
                pass

            self.status_bar.showMessage(f'Loaded: {os.path.basename(file_path)} → temp/{icc_name}_parsed.json')
            
        except Exception as e:
            import traceback
            QMessageBox.critical(self, 'Error', f'Failed to parse ICC:\n{str(e)}\n\n{traceback.format_exc()}')
            
    def show_about(self):
        QMessageBox.about(self, 'About ICC Inspector',
                         'ICC Inspector v1.0\n\nICC Profile Viewer\nSupports ICC.1:2022')
        
    @staticmethod
    def get_device_class(code):
        classes = {
            'scnr': 'Scanner',
            'mntr': 'Monitor',
            'prtr': 'Printer',
            'link': 'DeviceLink',
            'spac': 'ColorSpace',
            'abst': 'Abstract',
            'nmcl': 'NamedColor'
        }
        return classes.get(code, code)
        
    @staticmethod
    def get_intent(code):
        intents = {
            0: 'Perceptual',
            1: 'Media-rel Colorimetric',
            2: 'Saturation',
            3: 'ICC-absolute Colorimetric'
        }
        return intents.get(code, f'Unknown ({code})')


def _is_parsed_field(value):
    """判断是否为单个解析字段包装: {value, offset, bytesize, datatype, datasize}。"""
    if not isinstance(value, dict):
        return False

    required_keys = {"value", "offset", "bytesize", "datatype"}
    allowed_keys = required_keys | {"datasize"}
    return required_keys.issubset(value.keys()) and set(value.keys()).issubset(allowed_keys)


def _field_value(value, default=None):
    """兼容裸值和 ParsedField 结构，取出实际 value。"""
    if _is_parsed_field(value):
        return value.get("value", default)
    return value if value is not None else default


def _format_optional(value):
    """格式化可为空的表格单元格。"""
    return "" if value is None else str(value)


def _tree_cols(values):
    """QTreeWidgetItem 要求每一列都是字符串。"""
    return [_format_display_value(value) if isinstance(value, (list, dict)) else _format_optional(value)
            for value in values]


def _format_display_value(value, max_items=12, max_chars=240):
    """格式化树形表格中的值，长数组只显示摘要，避免 GUI 卡顿。"""
    if isinstance(value, list):
        preview = ", ".join(str(item) for item in value[:max_items])
        if len(value) > max_items:
            preview = f"{preview}, ... ({len(value)} items)"
        return f"[{preview}]"

    if isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)

    if len(text) > max_chars:
        return text[:max_chars] + f"... ({len(text)} chars)"
    return text


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = ICCInspectorGUI()
    gui.show()
    sys.exit(app.exec_())
