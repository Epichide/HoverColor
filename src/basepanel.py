#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/14 0:19
# @File: basepanel.py
# @Software: PyCharm
import  sys,os
from PyQt5.QtCore import  Qt,pyqtSlot,QPoint,pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QCloseEvent,QColor,QIcon,QMouseEvent,QCursor
from PyQt5.QtWidgets import  QWidget,QHBoxLayout,QApplication,QMenu,QAction,QMessageBox

class BaseWidget(QWidget):
    pos_value_signal=pyqtSignal(float,float,float)
    def pick_color(self,v1,v2,v3):
        pass
    def freeze_cursor(self):
        pass


