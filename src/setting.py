#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: Epichide
# @Email: no email
# @Time: 2025/8/6 19:56
# @File: setting.py
# @Software: PyCharm
import os
import traceback


#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5.QtCore import QSize, Qt

from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import (
    QDialog, QRadioButton, QTableWidgetItem, QGroupBox, QGridLayout, QFileDialog,
    QHBoxLayout,
    QMessageBox, QTabWidget
)

from PyQt5.QtWidgets import (QWidget, QVBoxLayout)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from .color_utils.iccinspector import iccProfile
from .record import RecordForm
from .color_utils.color_utils import *
from .wid_utils.hotkeys_utils.hotkey_wid import HotKeyWindow
from .utils.file_utils import _get_file
from .color_utils.icc import load_icc, save_icc, warp_file
from .wid_utils.basewid_utils import ScrollTab
from .wid_utils.icc_wid import ICCProfile, ICCRadio
from .wid_utils.gamutsviewer_wid import GamutsViewer
# 设置 matplotlib 支持中文显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题




class SettingDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SettingDialog, self).__init__(parent)
        self.profile={}
        self.setWindowTitle("Settings")

        self.setObjectName("Setting Dialog")
        self.resize(450, 650)
        style_file = _get_file("resource/css/SettingDialog.css")
        self.load_style_from_file(style_file)  # 加载外部CSS
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.setObjectName("buttonBox")
        # 绑定按钮事件（使用内置的accept和reject方法）
        self.buttonBox.accepted.connect(self.accept)  # OK按钮触发accept
        self.buttonBox.rejected.connect(self.reject)  # Cancel按钮触发reject
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)

        self.tabWidget = ScrollTab(self)
        self.verticalLayout.addWidget(self.tabWidget)
        self.verticalLayout.addWidget(self.buttonBox)
        self.setLayout(self.verticalLayout)
        # 设置默认字体

    def accept(self):
        self.metrics=self.metric_wid.get_metrics()
        self.hot_keys = self.hotkey_wid.get_hot_keys()[1] #  funcname: qtkeys

        self.seleted_gamut_info = self.gamut_viewer.gamut_info.radio.get_gamut() if self.gamut_viewer.gamut_info.radio else None  # 获取选中的gamut信息
        if self.seleted_gamut_info is None:
            QMessageBox.information(self, "Error", "Invalid custom icc profile.\n"
                                                   "Use the default sRGB gamutAutomatically")
            for radio in self.gamut_viewer.gamut_radios:
                if radio.objectName() == "sRGB":
                    radio.click()

                    self.seleted_gamut_info = self.gamut_viewer.gamut_info.radio.get_gamut() if self.gamut_viewer.gamut_info.radio else None  # 获取选中的gamut信息
                    break

        for radio in self.gamut_viewer.gamut_radios:
            if radio.objectName()=="CUSTOM":
                break
        custom_gamut=radio.get_gamut()
        if custom_gamut and (self.old_icc_file != custom_gamut.get("icc_file","")): # valid and return a profile dict

            gmsg=QMessageBox.information(self, "load icc ?", "Whether to save the custom icc profile ?",
                                QMessageBox.Ok| QMessageBox.Cancel)
            if gmsg!=QMessageBox.Ok:
                custom_gamut=None

        self.custom_gamut=custom_gamut




        super().accept()
    def load_style_from_file(self, style_file):
        """从CSS文件加载样式表"""
        try:
            # 检查文件是否存在
            if not os.path.exists(style_file):
                print(f"警告：样式文件 {style_file} 不存在，使用默认样式")
                return

            # 读取CSS文件内容
            with open(style_file, "r", encoding="utf-8") as f:
                style_content = f.read()

            # 应用样式表
            self.setStyleSheet(style_content)
            print(f"成功加载样式文件：{style_file}")

        except Exception as e:
            print(f"加载样式文件失败：{str(e)}")


    def func(self,ffunc,value):
        print(value)
        ffunc()

    def setupUi(self):

        self.wid_hotkey = self.Hotkey_Setting()  # 快捷键
        self.wid_colorspace = self.ColorSapce_Setting()  # 颜色空间



    def add_headder_title(self, layout, text):
        lab = QtWidgets.QLabel(self)
        # 使用传入的text参数，而不是固定文本
        lab.setText(f"<b> {text}:</b>")
        # 增加内边距让文字不贴边，更美观
        # lab.setStyleSheet("QLabel { "
        #                   "background-color: gray; "
        #                   "color: white; "
        #                   "padding: 2px 8px; }")
        # 设置水平扩展，垂直固定
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        lab.setSizePolicy(size_policy)
        # 文本左对齐
        lab.setAlignment(Qt.AlignLeft | Qt.AlignHCenter)
        # 移除alignment参数，允许标签水平扩展
        layout.addWidget(lab)
        return lab

    def Record_Setting(self, record: RecordForm = None):
        wid = self.tabWidget.add_tab("Record Setting")
        layout = wid.layout()
        if record is None:
            record = RecordForm(self)
        self.metric_wid = record.get_metric_choose()
        layout.addWidget(self.metric_wid)
        return wid
    def ColorSapce_Setting(self, gamuts=[],custom_gamut="CUSTOM",cur_gamut=""):
        """_summary_

        Args:
            gamuts (list, optional): _description_. Defaults to [].
            custom_gamut (str, optional): _description_. Defaults to "CUSTOM".
            cur_gamut (str, optional): _description_. built in gamuts or CUSTOM

        Returns:
            _type_: _description_
        """
        wid=self.tabWidget.add_tab("Color Space")
        self.old_icc_file=""
        if custom_gamut!="CUSTOM" and custom_gamut: # 如果 存在custom 的 icc文件,读取; 否则,跳过
            self.old_icc_file=_get_file(custom_gamut)
            custom_gamut=self.old_icc_file
        if cur_gamut=="CUSTOM":
            cur_gamut=custom_gamut
        if gamuts[-1]=="CUSTOM":
            gamuts[-1]=custom_gamut
           
        layout=wid.layout()
        
        # 使用新的GamutsViewer组件
        self.gamut_viewer = GamutsViewer(self, gamuts, cur_gamut)
        layout.addWidget(self.gamut_viewer)
        
        return wid


    def Hotkey_Setting(self, func_hotkeys={}):
        self.hotkey_wid = HotKeyWindow()
        for funcname,(func,qtkeys) in func_hotkeys.items():
            self.hotkey_wid.register(funcname, qtkeys)

        wid = self.tabWidget.add_tab("Hotkey",self.hotkey_wid)
        return self.hotkey_wid






if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    dialog = SettingDialog()
    dialog.setupUi()
    result =dialog.exec_()
    if result==QDialog.Accepted:
        print(dialog.profile)

    sys.exit(result!=1)