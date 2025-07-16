#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: Epichide
# @Email: no email
# @Time: 2025/7/16 21:55
# @File: hotkey_wid.py
# @Software: PyCharm
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt
from pyqthotkey import HotkeyPicker
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QFormLayout, QWidget
from .hotkey_picker import HotkeyPicker


class HotKeyWindow(QMainWindow):

    def __init__(self):
        super().__init__(parent=None)

        # Window settings
        self.setWindowTitle('Hotkey Setting')
        self.resize(360, 150)
        self.keynames={}

        # Form layout
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(5)
        self.form_layout.setContentsMargins(25, 25, 25, 25)
        # Set layout
        central_widget = QWidget()
        central_widget.setLayout(self.form_layout)
        self.setCentralWidget(central_widget)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.register("pixel pick",[Qt.Key_Control,Qt.Key_QuoteLeft])

        self.register("screen pick", [Qt.Key_Alt, Qt.Key_QuoteLeft])

    def register(self,keyname,defaultkeys):
        if keyname in self.keynames:
            pass
        else:
            self.key_line= HotkeyPicker(self, key_filter_enabled=True, max_key_num=3)
            self.key_line.setHotkey(defaultkeys)
            # Set size constraints
            self.key_line.setFixedHeight(25)

            self.key_line.hotkeyChanged.connect(self.hotkey_picker_1_changed)
            self.form_layout.addRow(keyname, self.key_line)
            self.keynames[keyname]=self.key_line

    def hotkey_picker_1_changed(self, key, key_name):
        # Handle change of hotkey 1
        self.selected_hotkey_1 = key
        self.selected_hotkey_1_name = key_name
        print([key, key_name])

    def keyPressEvent(self, event):
        # React to a selected hotkey being pressed
        if event.key() == self.selected_hotkey_1:
            print('Selected hotkey 1 (' + self.selected_hotkey_1_name + ') has been pressed')
        if event.key() == self.selected_hotkey_2:
            print('Selected hotkey 2 (' + self.selected_hotkey_2_name + ') has been pressed')

# Run example
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())







