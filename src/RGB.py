#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/14 0:16
# @File: RGB.py
# @Software: PyCharm

import  sys,os

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import  Qt,pyqtSlot,QPoint,pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QCloseEvent,QColor,QIcon,QMouseEvent,QCursor
from PyQt5.QtWidgets import  (QWidget,QHBoxLayout,QFrame,QLabel,
                              QApplication,QMenu,QAction,QMessageBox)
from .basepanel import  BaseWidget
class RGBBar(BaseWidget):
    def get_suggest_size(self,parent):
        if parent is None:
            self.wid_width=50
            self.font=8
            self.wid_height = 150
            self.bar_width = parent.single_wid_width * 0.1

        else:
            #0.02 + 0.850 + 0.01 + 0.06 +0.02
            self.wid_width=parent.single_wid_width*0.3
            self.wid_height=parent.single_wid_width*0.9
            self.bar_width=parent.single_wid_width*0.08
            self.font_size = self.wid_width / 150 * 8

    def __init__(self,parent=None):
        super(RGBBar,self).__init__(parent)
        self.get_suggest_size(parent)
        self.setFixedSize(self.wid_width,self.wid_height)
        self.colorspace = "RGB"
        self.metric = "G"
        self.horizontallayout=QHBoxLayout(self)
        self.horizontallayout.setContentsMargins(0,0,0,0)
        self.red=QFrame(self)
        self.red.setStyleSheet(
            "background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255,0,0,255), stop:1 rgba(0,0,0,255));\n"
            # "border-radius: 4px;"
        )
        self.red.setFrameShape(QFrame.StyledPanel)
        self.red.setFrameShadow(QFrame.Raised)
        self.green = QFrame(self)
        self.green.setStyleSheet(
            "background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0,255,0,255), stop:1 rgba(0,0,0,255));\n"
            # "border-radius: 4px;"
        )
        self.blue = QFrame(self)
        self.blue.setStyleSheet(
            "background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0,0,255,255), stop:1 rgba(0,0,0,255));\n"
            # "border-radius: 4px;"
        )
        self.red.setFixedWidth(self.bar_width)
        self.blue.setFixedWidth(self.bar_width)
        self.green.setFixedWidth(self.bar_width)

        self.horizontallayout.addWidget(self.red)
        self.horizontallayout.addWidget(self.green)
        self.horizontallayout.addWidget(self.blue)
        self.blue.pos_old1=self.add_pos_widget(self.blue,"","black",0.2)
        self.blue.pos_old2=self.add_pos_widget(self.blue,"","rgba(255,255,255,0.8)",0)
        self.red.pos_old1 = self.add_pos_widget(self.red,"","black",0.2)
        self.red.pos_old2 = self.add_pos_widget(self.red,"","rgba(255,255,255,0.8)",0)
        self.green.pos_old1 = self.add_pos_widget(self.green,"","black",0.2)
        self.green.pos_old2 = self.add_pos_widget(self.green,"","rgba(255,255,255,0.8)",0)
        self.red.cur=self.add_cur_widget(self.red)
        self.blue.cur=self.add_cur_widget(self.blue)
        self.green.cur=self.add_cur_widget(self.green)

    def add_pos_widget(self,wid,tex="",color="",shift=0.05):
        pos_wid=QLabel(wid,text=tex)
        pos_wid.setGeometry((QtCore.QRect(shift*self.bar_width,self.wid_height-self.bar_width*0.8,self.bar_width*0.8,self.bar_width*0.8)))
        pos_wid.setStyleSheet(
            f"background-color: {color};\n"
            "border-style: outset;\n"
            "border-color: gray;\n"
            "border-width: 1px;\n"
            f"border-radius: {self.bar_width*0.7/2}px;\n"
        )
        font=QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(self.font_size)
        font.setBold(True)
        pos_wid.setFont(font)
        pos_wid.setAlignment(QtCore.Qt.AlignCenter)
        return pos_wid
    def add_cur_widget(self,wid,color=""):
        pos_wid=QLabel(wid)
        pos_wid.setGeometry((QtCore.QRect(0,0,30,5)))
        pos_wid.setStyleSheet(
            "background-color: rgba(255,255,255,0.5);\n"
            # "border-radius: 50px;\n"
            "border-style: outset;\n"
            "border-width: 1px;\n"
        )
        pos_wid.setText("")
        return pos_wid


    def pick_color(self,r,g,b):
        self.bar_height=self.red.height()
        self.cursor_height=self.red.pos_old1.height()
        self.red.cur.move(QPoint(0,self.bar_height-r/255.0*self.bar_height-self.cursor_height/2.0))
        self.blue.cur.move(QPoint(0,self.bar_height-b/255.0*self.bar_height-self.cursor_height/2.0))
        self.green.cur.move(QPoint(0,self.bar_height-g/255.0*self.bar_height-self.cursor_height/2.0))
        gray=  0.299 *r+ 0.587 *g + 0.114 *b
        self.pos_value_signal.emit([r,g,b,round(gray)])

    def freeze_cursor(self):
        self.red.pos_old2.move(self.red.pos_old2.pos().x(),self.red.pos_old1.pos().y())
        self.red.pos_old1.move(self.red.pos_old1.pos().x(),self.red.cur.pos().y())
        self.blue.pos_old2.move(self.blue.pos_old2.pos().x(),self.blue.pos_old1.pos().y())
        self.blue.pos_old1.move(self.blue.pos_old1.pos().x(),self.blue.cur.pos().y())
        self.green.pos_old2.move(self.green.pos_old2.pos().x(),self.green.pos_old1.pos().y())
        self.green.pos_old1.move(self.green.pos_old1.pos().x(),self.green.cur.pos().y())
