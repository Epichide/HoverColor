#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: Epichide
# @Email: no email
# @Time: 2025/8/6 19:56
# @File: gamutsviewer_wid.py
# @Software: PyCharm

import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel)

from .icc_wid import ICCProfile, ICCRadio
from ..utils.file_utils import _get_file
from .flow_wid import FlowLayout

class GamutsViewer(QWidget):
    def __init__(self, parent=None, gamuts=[], cur_gamut=""):
        super(GamutsViewer, self).__init__(parent)
        self.gamuts = gamuts
  
        self.cur_gamut = cur_gamut
        self.gamut_radios = []
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Gamut选择区域
        self.gamut_selection_widget = QWidget(self)
        self.gamut_selection_layout = FlowLayout(self.gamut_selection_widget)
        self.gamut_selection_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        
        # 创建Gamut标签
        gamut_label = QLabel(self, text="Gamut:")
        self.gamut_selection_layout.addWidget(gamut_label)
        
        # 创建QButtonGroup来管理单选按钮，确保互斥性
        self.gamut_button_group = QtWidgets.QButtonGroup(self)
        self.gamut_button_group.setExclusive(True)
        
        # 设置按钮网格布局
        gamut_ncol = 4
        if not self.gamuts:
            self.gamuts = ["P3-D65", "sRGB", "P3-DCI", "Rec.709", "Rec.2020", "AdobeRGB", "CUSTOM"]
        
        # 先创建ICC信息显示区域
        self.gamut_info = ICCProfile(self)
        
        for n, gamut in enumerate(self.gamuts):
            if gamut == "CUSTOM":
                itype = "icc"
            elif os.path.exists(gamut):
              
                itype = "icc"
            else:
                itype = "built-in"
            
            gamut_radio = ICCRadio(self, text=gamut, itype=itype)
            if itype == "icc":
                gamut_radio.update_profile(gamut)
            
            gamut_radio.clicked.connect(self.on_radio_clicked)
            
            radio_row = n // gamut_ncol
            radio_col = n % gamut_ncol
            
            self.gamut_button_group.addButton(gamut_radio, n)
            self.gamut_selection_layout.addWidget(gamut_radio)
            self.gamut_radios.append(gamut_radio)
            
            if gamut == self.cur_gamut:
                gamut_radio.click()
        
        # 设置选择区域的大小策略
        self.gamut_selection_widget.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.Minimum
        )
        
        # 设置ICCProfile的大小策略为扩展
        self.gamut_info.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.Expanding
        )
        
        # 将两个区域添加到主布局
        self.main_layout.addWidget(self.gamut_selection_widget)
        self.main_layout.addWidget(self.gamut_info)
        
        # 设置主布局的拉伸因子，让ICCProfile区域占据剩余空间
        self.main_layout.setStretchFactor(self.gamut_selection_widget, 0)
        self.main_layout.setStretchFactor(self.gamut_info, 1)
    
    def on_radio_clicked(self):
        for radio in self.gamut_radios:
            if radio.isChecked():
                self.gamut_info.update_profile(radio)
                break
    
    def get_selected_gamut(self):
        for radio in self.gamut_radios:
            if radio.isChecked():
                return radio.get_gamut()
        return None
    
    def get_custom_gamut(self):
        for radio in self.gamut_radios:
            if radio.objectName() == "CUSTOM":
                return radio.get_gamut()
        return None
