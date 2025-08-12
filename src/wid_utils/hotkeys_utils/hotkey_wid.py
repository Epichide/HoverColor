#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: Epichide
# @Email: no email
# @Time: 2025/7/16 21:55
# @File: hotkey_wid.py
# @Software: PyCharm
from PyQt5.QtWidgets import QLabel, QMainWindow, QMessageBox, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QFormLayout, QWidget
from .hotkey_picker import HotkeyPicker


class HotKeyWindow(QWidget):
    widget_closed = pyqtSignal()
    def __init__(self):
        super().__init__(parent=None)
        self.setWindowFlags(Qt.WindowStaysOnTopHint )
        # Window settings
        self.setWindowTitle('Hotkey Setting')
        self.resize(360, 150)
        self.res=False
        self.keynames={}

        # Form layout
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(5)
        self.form_layout.setContentsMargins(25, 25, 25, 25)
        self.form_layout.addRow("ToolTip",QLabel("Press the key combination. Not support <b> Shift </b> Modifier!"))
        self.ok=QPushButton("OK")
        self.cancel=QPushButton("Cancel")
        self.cancel.clicked.connect(self.close)
        self.ok.clicked.connect(self.accept)

        # Set layout
        self.setLayout(self.form_layout)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        # self.register("pixel pick",[Qt.Key_Control,Qt.Key_QuoteLeft])
        # self.register("screen pick", [Qt.Key_Alt, Qt.Key_QuoteLeft])
    def closeEvent(self,event):
        super(HotKeyWindow, self).closeEvent(event)
        print("CLOSE")
        # super().close()
        self.widget_closed.emit()
    def accept(self):
        self.res=True
        self.close()
    def clear_Focus(self,exeception):
        """
        Clear focus for all widgets except the specified one.
        :param exeception: Widget to keep focused.
        """
        for keyname, wid in self.keynames.items():
            if wid != exeception:
                wid.clearFocus()

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
    def show(self):
        self.form_layout.addRow(self.cancel, self.ok)
        super().show()
    def get_hot_keys(self):
        hot_keys={}
        for keyname,wid in self.keynames.items():
            hot_keys[keyname]=wid.getHotkey()
        return self.res,hot_keys


    def hotkey_picker_1_changed(self, key, key_name):
        # Handle change of hotkey 1
        self.selected_hotkey_1 = key
        self.selected_hotkey_1_name = key_name
        print([key, key_name])

    # def keyPressEvent(self, event):
    #     # React to a selected hotkey being pressed
    #     if event.key() == Qt.Key_Shift:
    #         QMessageBox.information(self, "Warning", "Shift modifier is not supported!")
        #     print('Selected hotkey 1 (' + self.selected_hotkey_1_name + ') has been pressed')
        # if event.key() == self.selected_hotkey_2:
        #     print('Selected hotkey 2 (' + self.selected_hotkey_2_name + ') has been pressed')

# Run example
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())







