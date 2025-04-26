#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/27 22:14
# @File: hue.py
# @Software: PyCharm

import  sys,os

import colour
import numpy as np
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import  Qt,pyqtSlot,QPoint,pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QCloseEvent, QColor, QIcon, QImage, QMouseEvent, QCursor
from PyQt5.QtWidgets import  (QWidget,QHBoxLayout,QFrame,QLabel,
                              QApplication,QMenu,QAction,QMessageBox)
try:
    from .basepanel import  BaseWidget
except:
    from basepanel import  BaseWidget

class HueChart(BaseWidget):
    def __init__(self,parent=None,mode="hsv"):
        super().__init__(parent)
        self.setFixedSize(200,200)
        self.hue=QLabel(self)
        self.hue.setGeometry(QtCore.QRect(10,10,150,150))
        font=QtGui.QFont()
        font.setPointSize(8)
        self.hue.setFont(font)
        self.hue.setStyleSheet(
            "border-style: outset;\n"
            "border-width: 1px;\n"
            "border-radius: 75px;\n"
        )
        self.hue.setFrameShape(QFrame.StyledPanel)
        self.hue.setFrameShadow(QFrame.Raised)
        self.hue.setLineWidth(2)
        self.setObjectName("hue")
        palatte=QtGui.QPalette()
        self.luma = QFrame(self)
        self.luma.setGeometry(QtCore.QRect(170,10,10,150))
        self.luma.setStyleSheet(
            "background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255,255,255,255), stop:1 rgba(0,0,0,255));\n"
            "border-radius: 4px;"
        )
        self.luma.setFrameShape(QFrame.StyledPanel)
        self.luma.setFrameShadow(QFrame.Raised)
        # self.horizontallayout = QHBoxLayout(self)
        # self.horizontallayout.setContentsMargins(0, 0, 0, 0)
        # self.horizontallayout.addWidget(self.hue)
        # self.horizontallayout.addWidget(self.luma)
        self.create_hsv_img()
        self.hue_cur=self.add_cur_hue_widget(self.hue)
        self.luma_cur=self.add_cur_luma_widget(self.luma)
        self.hue_old1=self.add_pos_hue_widget(self.hue,"1")
        self.hue_old2=self.add_pos_hue_widget(self.hue,"2")
        self.luma_old1=self.add_pos_luma_widget(self.luma,"1")
        self.luma_old2=self.add_pos_luma_widget(self.luma,"2")


    def create_hsv_img(self):
        nsize=500
        x=np.linspace(-1,1,nsize)
        y=np.linspace(-1,1,nsize)
        x,y=np.mgrid[-1:1:nsize*1j,-1:1:nsize*1j]
        S=x*x+y*y
        ang=np.arctan2(y,x)+np.pi
        H=ang/np.pi/2
        A=np.ones([nsize,nsize,1],dtype=np.uint8)*255
        A[:,:,0][S>1]=0
        S[S>1]=0
        arr=np.zeros([nsize,nsize,3])
        arr[:,:,0]=H
        arr[:,:,1]=S
        arr[:,:,2]=0.8
        S[S>1]=0
        img=colour.HSV_to_RGB(arr)*255
        img=np.array(img,dtype=np.uint8)
        img=np.concatenate([img,A],axis=2)
        h,w,c=img.shape
        qimg=QImage(img.data,w,h,w*c,QImage.Format.Format_RGBA8888)
        qpix=QtGui.QPixmap(qimg)
        qpix2=qpix.scaled(self.hue.width()-1,self.hue.height()-1)
        self.scale=qpix2.height()/qpix.height()
        self.hue.setPixmap(qpix2)
    def pick_color(self,r,g,b):
        h,s,v=colour.RGB_to_HSV(np.array([r/255,g/255,b/255]))
        nsize=500
        self.pie_radius=self.hue.height()/2
        self.bar_length=self.luma.height()
        self.luma_cur.move(QPoint(0,self.bar_length*(1-v)-self.luma_cur.height()/2))
        s_ratio=np.sqrt(s)
        h_ratio=h
        dx=np.cos(h_ratio*2*np.pi)*s_ratio*self.pie_radius
        dy=np.sin(h_ratio*2*np.pi)*s_ratio*self.pie_radius
        self.pie_center=(
            QPoint(self.pie_radius,self.pie_radius)-
            QPoint(self.hue_cur.height()/2,self.hue_cur.height()/2)

        )
        self.hue_cur.move(self.pie_center-QPoint(dy,dx))

        h = min(255, h * 255)
        v = min(255, v * 255)
        s = min(255, s * 255)
        color_string = ",".join([str(r), str(g), str(b)])
        self.hue_cur.setStyleSheet("Qlabel{background-color: rgb(" + color_string + ");}")
        self.pos_value_signal.emit(h,s,v)
        return h,s,v
    def add_pos_hue_widget(self,wid,tex=""):
        pos_wid=QLabel(wid)
        pos_wid.setText(tex)
        pos_wid.setGeometry(QtCore.QRect(70,70,12,12))
        pos_wid.setStyleSheet(
            # "background-color: qlinear()"
            "border-radius: 4px;"
        )
        return pos_wid
    def add_cur_hue_widget(self,wid):
        pos_wid=QLabel(wid)
        pos_wid.setGeometry(QtCore.QRect(70,40,10,10))
        pos_wid.setFrameShape(QFrame.NoFrame)
        pos_wid.setText("")
        # pos_wid.setStyleSheet(
        #     # "background-color: qlinear()"
        #     "border-radius: 4px;"
        # )
        return pos_wid

    def add_pos_luma_widget(self, wid, tex=""):
        pos_wid = QLabel(wid, text=tex)
        pos_wid.setGeometry((QtCore.QRect(5, 145, 10, 10)))
        pos_wid.setStyleSheet(
            "background-color: rgba(255,255,255,0.5);\n"
            "border-radius: 50px;"
        )
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        font.setBold(True)
        pos_wid.setFont(font)
        pos_wid.setAlignment(QtCore.Qt.AlignCenter)
        return pos_wid

    def add_cur_luma_widget(self, wid):
        pos_wid = QLabel(wid)
        pos_wid.setGeometry((QtCore.QRect(0, 0, 30, 5)))
        pos_wid.setStyleSheet(
            "background-color: rgba(255,255,255,0.5);\n"
            "border-radius: 50px;\n"
            "border-style: outset;\n"
            "border-width: 1px;\n"

        )
        pos_wid.setText("")
        return pos_wid
    def freeze_cursor(self):
        self.hue_old2.move(self.hue_old1.pos())
        self.hue_old1.move(self.hue_cur.pos())
        self.luma_old2.move(self.luma_old1.pos())
        self.luma_old1.move(self.luma_cur.pos())

