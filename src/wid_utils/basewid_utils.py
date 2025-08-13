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
from PyQt5.QtWidgets import QLayout, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QRect, QSize

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




class QFlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        margin, _, _, _ = self.getContentsMargins()
        size += QSize(2 * margin, 2 * margin)
        return size

    def doLayout(self, rect, testOnly):
        margin, top, _, right = self.getContentsMargins()
        x = rect.x() + margin
        y = rect.y() + top
        lineHeight = 0

        for item in self.itemList:
            widget = item.widget()
            spaceX = self.spacing()
            spaceY = self.spacing()
            if widget:
                spaceX += widget.styleSheet().marginLeft() + widget.styleSheet().marginRight()
                spaceY += widget.styleSheet().marginTop() + widget.styleSheet().marginBottom()

            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() - right and lineHeight > 0:
                x = rect.x() + margin
                y += lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y() + margin