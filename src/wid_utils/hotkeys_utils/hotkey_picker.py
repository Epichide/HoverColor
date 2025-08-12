#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: Epichide
# @Email: no email
# @Time: 2025/7/16 23:57
# @File: hotkey_picker.py
# @Software: PyCharm
import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QPushButton


class HotkeyPicker(QPushButton):

    # Signal that hotkey has changed
    hotkeyChanged = pyqtSignal(object, object)

    # Key code map
    __key_code_map = {}
    for key, value in vars(Qt).items():
        if isinstance(value, Qt.Key):
            __key_code_map[value] = key.partition('_')[2]

    # Manually change name for some keys
    __key_code_map[Qt.Key.Key_Space] = 'Space'
    __key_code_map[Qt.Key.Key_Adiaeresis] = 'Ä'
    __key_code_map[Qt.Key.Key_Odiaeresis] = 'Ö'
    __key_code_map[Qt.Key.Key_Udiaeresis] = 'Ü'

    def __init__(self, parent=None,
                 default_text: str = 'None',
                 selection_text: str = '..',
                 cancel_key: Qt.Key = Qt.Key.Key_Escape,
                 key_filter_enabled: bool = False,
                 whitelisted_keys: list[Qt.Key] = [],
                 blacklisted_keys: list[Qt.Key] = [Qt.Key_Enter,Qt.Key_Return,Qt.Key_Shift],
                 max_key_num=1):
        """Create a new HotkeyPicker instance

        :param parent: the parent widget
        :param default_text: the text shown when no hotkey is selected
        :param selection_text: the text shown when in selection
        :param cancel_key: the key that is used to exit the current key selection
        :param key_filter_enabled: if the hotkey picker should use a filter instead of accepting every key
        :param whitelisted_keys: list of keys that can be chosen (key_filter_enabled must be True)
        :param blacklisted_keys: list of keys that cannot be chosen (key_filter_enabled must be True)
        """

        super(HotkeyPicker, self).__init__(parent)

        self._release=False
        # Init arguments
        self.__default_text = default_text
        self.__selection_text = selection_text
        self.__cancel_key = cancel_key
        self.__key_filter_enabled = key_filter_enabled
        self.__whitelisted_keys = whitelisted_keys
        self.__blacklisted_keys = blacklisted_keys

        # Make sure either whitelisted_keys or blacklisted_keys is emtpy
        if whitelisted_keys and blacklisted_keys:
            self.__blacklisted_keys = []

        # Init variables
        self.__selected_key = [] # multi keys
        self.max_key_num=max_key_num
        self.__in_selection = False

        self.setText(self.__default_text)
        self.load_style()

        # Prevent the hotkey picker from focusing automatically (e.g. if it is the only widget)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
    def load_style(self):
        def load_stylesheet(self):
            """加载CSS样式表"""
            # 假设CSS文件与当前文件在同一目录
            css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resource/css/hotkey_picker.css")

            if os.path.exists(css_path):
                with open(css_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
            else:
                # 如果CSS文件不存在，使用默认样式
                default_style = """
                QPushButton.hotkey-picker {
                    background-color: #f0f0f0;
                    border: 1px solid #999999;
                    color: #999999;
                }
                QPushButton.hotkey-picker:focus {
                    background-color: #d0d0d0;
                    border: 2px solid #4444ff;
                }
                """
                self.setStyleSheet(default_style)
    def focusInEvent(self, event):
        """Set text to selection text

        :param event: event sent by PyQt
        """

        self.__in_selection = True
        self.__selected_key=[]
        self.set_key_text()

    def focusOutEvent(self, event):
        """Unset selection text if focused out without new key being selected

        :param event: event sent by PyQt
        """
        # Focus out without a new key being selected
        if self.__selected_key is None and self.__in_selection:
            self.set_key_text()
            self.__in_selection = False
            self.update()
        elif self.__selected_key is not None and self.__in_selection:
            self.set_key_text()
            self.__in_selection = False
            self.update()

    def CheckNotInBlack(self,hotkeys):
        return not any(hotkey in self.__blacklisted_keys for hotkey in hotkeys)
    def CheckInWhite(self,hotkeys):
        if self.__whitelisted_keys:
            return all(hotkey in self.__whitelisted_keys for hotkey in hotkeys)
        return True
    def keyPressEvent(self, event):
        """Get key from event and set it as the hotkey

        :param event: event sent by PyQt
        """

        key = event.key()

        # event.modifiers()
        # if event.isAutoRepeat():
        #     print("isAutoRepeat",True,key)
        # Check if entered key is cancel key


        if event.key() == Qt.Key_Shift :

            msg_box = QMessageBox(self)

            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Information")
            msg_box.setText("Key <b> Shift </b>  is not supported")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()



            self.setText(self.__default_text)
            self.__selected_key = []
            self._release = False
            self.clearFocus()
            self.set_key_text()
        if key == self.__cancel_key:
            self.setText(self.__default_text)
            self.__selected_key = []
            self._release = False
            self.clearFocus()
            self.set_key_text()
        else:
            # Ignore key press if key is not in whitelisted_keys
            if self.__key_filter_enabled and self.__whitelisted_keys and not self.CheckInWhite([key]):
                self.__in_selection = False
                self._release = False
                self.clearFocus()
                self.set_key_text()
                print("W")
                return
            # Ignore key press if key is in blacklisted_keys
            elif self.__key_filter_enabled and self.__blacklisted_keys and not self.CheckNotInBlack([key]):
                self.__in_selection = False
                self._release = False
                self.clearFocus()
                self.set_key_text()

                return
            elif self._release:
                self._release = False
                self.__selected_key=[key]
                self.set_key_text()
            if self.max_key_num>len(self.__selected_key):
                if key not in self.__selected_key:
                    self.__selected_key.append(key)
                    self.set_key_text()
        if self.max_key_num==len(self.__selected_key):
            # Clear selection and widget focus
            self.__in_selection = False
            self._release=False
            self.clearFocus()

        # Emit signal
        self.__emit_hotkey_changed_signal()
    def keyReleaseEvent(self,event):
        if self.hasFocus():
            if not event.isAutoRepeat():
                self._release=True
    def clearFocus(self):
        super().clearFocus()
        self.update()
    def set_key_text(self):
        key_names=self.getHotkeyName()
        key_names_str="+".join(key_names)
        self.setText(key_names_str)


    def getHotkey(self) :
        """Get the currently selected hotkey

        :return: key code, None if no hotkey is selected
        """

        return self.__selected_key

    def getHotkeyName(self) -> str:
        """Get the name of the currently selected hotkey

        :return: string with the key name, None if no hotkey is selected
        """
        key_names=[HotkeyPicker.getKeyName(key) for key in self.__selected_key]


        return key_names

    def isInSelection(self) -> bool:
        """Get whether the hotkey picker is in selection state

        :return: whether the hotkey picker is in selection
        """

        return self.__in_selection

    def setHotkey(self, hotkeys: [int]):
        """Set the hotkey

        :param hotkey: the key code of the hotkey (e.g. 65 or Qt.Key.Key_A)
        """
        if len(hotkeys)>self.max_key_num:
            return
        # Ignore if filter is enabled and key code is not in whitelisted_keys
        if (self.__key_filter_enabled and self.__whitelisted_keys) and (not self.CheckInWhite(hotkeys)):

            return
        # Ignore if filter is enabled and key code is in blacklisted_keys
        elif (self.__key_filter_enabled and self.__blacklisted_keys) and (not self.CheckNotInBlack(hotkeys)):

            return

        # Set hotkey if input key valid
        key_strings = [HotkeyPicker.getKeyName(hotkey) for hotkey in hotkeys]

        if all(key_strings):
            self.__selected_key = [int(hotkey) for hotkey in hotkeys]
            self.set_key_text()
            # Emit signal
            self.__emit_hotkey_changed_signal()

    def reset(self):
        """Reset the hotkey picker to the default state with no hotkey selected"""

        self.setText(self.__default_text)
        self.__selected_key = []

        # Emit signal
        self.__emit_hotkey_changed_signal()

    def getDefaultText(self) -> str:
        """Get the default text"""

        return self.__default_text

    def setDefaultText(self, default_text: str):
        """Set the default text

        :param default_text: the new default text
        """

        self.__default_text = default_text
        if not self.__in_selection and self.__selected_key is None:
            self.setText(default_text)

    def getSelectionText(self) -> str:
        """Get the selecting text"""

        return self.__selection_text

    def setSelectionText(self, selecting_text: str):
        """Set the selecting text

        :param selecting_text: the new selecting text
        """

        self.__selection_text = selecting_text
        if self.__in_selection:
            self.setText(selecting_text)

    def getCancelKey(self) -> Qt.Key:
        """Get the cancel key"""

        return self.__cancel_key

    def setCancelKey(self, cancel_key:int):
        """Set the cancel key

        :param cancel_key: the new cancel key
        """

        self.__cancel_key = cancel_key

    def isKeyFilterEnabled(self) -> bool:
        """Get whether keys are being filtered

        :return: whether keys are being filtered
        """

        return self.__key_filter_enabled

    def setKeyFilterEnabled(self, on: bool):
        """Enable or disable key filtering

        :param on: if keys should be filtered
        """

        self.__key_filter_enabled = on

    def getWhitelistedKeys(self) -> list[Qt.Key]:
        """Get list of whitelisted keys

        :return: whitelisted keys
        """

        return self.__whitelisted_keys

    def setWhitelistedKeys(self, whitelisted_keys: list[ int]):
        """Set whitelisted keys (keys that can be selected)

        :param whitelisted_keys: the new list of whitelisted keys
        """

        if whitelisted_keys and self.__blacklisted_keys:
            self.__blacklisted_keys = []
        self.__whitelisted_keys = whitelisted_keys

    def getBlacklistedKeys(self) -> list[Qt.Key]:
        """Get list of blacklisted keys

        :return: blacklisted keys
        """

        return self.__blacklisted_keys

    def setBlacklistedKeys(self, blacklisted_keys: list[ int]):
        """Set blacklisted keys (keys that cannot be selected)

        :param blacklisted_keys: the new list of blacklisted keys
        """

        if blacklisted_keys and self.__whitelisted_keys:
            self.__whitelisted_keys = []
        self.__blacklisted_keys = blacklisted_keys

    def __emit_hotkey_changed_signal(self):
        """Emit a signal that the selected hotkey has changed"""

        self.hotkeyChanged.emit(self.__selected_key,self.getHotkeyName())

    @staticmethod
    def getKeyName(key:  int) -> str:
        """Get the key name from a key

        :param key: key you want to get the name of (e.g. 65 or Qt.Key_A)
        :return: name of the key
        """

        return HotkeyPicker.__key_code_map.get(key)

    @staticmethod
    def setKeyName(key: Qt.Key, name: str):
        """Override the name of a key

        :param key: key you want to rename
        :param name: new name of the key
        """

        HotkeyPicker.__key_code_map[key] = name
