#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: Epichide
# @Email: no email
# @Time: 2025/8/9 9:59
# @File: basewid_utils.py
# @Software: PyCharm

import sys

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout,
                             QPushButton, QVBoxLayout, QHBoxLayout)


class DynamicGridLayout(QHBoxLayout):
    def __init__(self, parent=None, max_cols=3):
        super().__init__(parent)
        self.nrow=2
        self.record=None
        self.max_cols = max_cols  # 最多列数

        # self.comp_layout = QHBoxLayout()  # 组件布局
        # self.record_layout = QHBoxLayout()  # 记录布局
        # self.addLayout(self.comp_layout)
        # self.addLayout(self.record_layout)

        self.components = []  # 存储所有组件
    def add_component(self,wid):
        """添加一个新组件到网格布局，并自动调整位置"""

        self.components.append(wid)
        self.addWidget(wid)  # 添加到组件布局中
        # 重新布局所有组件
        self.update_layout()
    def add_record(self,wid):
        self.record = wid
        self.components.append(wid)
        self.addWidget(wid)  # 添加到记录布局中
        self.update_layout()

    def clear_components(self):
        """清空所有组件并重置布局"""
        # 移除并删除所有组件
        for comp in self.components:
            self.removeWidget(comp)
            comp.deleteLater()
        self.components.clear()
        # 重置布局
        self.update_grid_layout()

    def update_layout(self):
        if self.record:
            self.record.adjust_column_width( )

        return QSize(self.get_total_size())


    def calculate_total_width(self):
        """计算布局所需的总宽度"""

        w = 0
        for wid in self.components:
            if wid.isVisible():
                w += wid.width() * 1.2

        return w


    def calculate_total_height(self):
        """计算布局所需的总高度"""
        total_height = 0
        if self.record:
            total_height1 = self.record.height() + self.contentsMargins().top() + self.contentsMargins().bottom()

        if self.components:
            total_height1 = self.components[0].height() + self.contentsMargins().top() + self.contentsMargins().bottom()

        return max(total_height, total_height1)

    def get_total_size(self):
        """返回布局总尺寸（宽度和高度）"""
        return QSize(self.calculate_total_width(), self.calculate_total_height())

