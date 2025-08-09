#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/14 1:40
# @File: screenshoot.py
# @Software: PyCharm
import numpy as np
from PyQt5 import  QtCore, QtGui
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QWidget
from PyQt5.QtCore import  Qt, QPoint,pyqtSignal,QTimer

from src.wid_utils.pyqt_screenshot import constant
from src.wid_utils.pyqt_screenshot.screenshot import Screenshot


class Screenshoot(QWidget):
    cursor_moved = pyqtSignal(object)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.press_pos = self.pos()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.default_width=5
        self.default_height=5
        self.setMinimumWidth(self.default_width)
        self.setMinimumHeight(self.default_height)
        self.setGeometry((QtCore.QRect(5, 5, self.default_width, self.default_height)))
        # print(11111,self.height(),self.width())
        self.qbox=QHBoxLayout()
        self.qbox.setContentsMargins(0,0,0,0)
        # self.setContentsMargins(0,0,0,0)
        self.setLayout(self.qbox)

        self.label=QLabel(self)
        self.label.setStyleSheet(
            "background: transparent;\n"
            "border-style: solid;\n"
            "border-color: red;\n"
            "border-width: 1px;"
        )
        self.qbox.addWidget(self.label)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        font.setBold(True)
        self.label.setFont(font)
        self._initSignals()
        # self.setAlignment(QtCore.Qt.AlignCenter)

    ##------- move whole widget
    # def mouseReleaseEvent(self,event=None):
    #     self.m_flag=False
    #     self.setCursor(Qt.ArrowCursor)
    # def mousePressEvent(self, event=None):
    #     if event.button() ==Qt.LeftButton:
    #         self.m_flag=True
    #         self.press_pos=event.pos()
    #         event.accept()
    #         self.setCursor(Qt.OpenHandCursor)
    # def mouseMoveEvent(self, event=None):
    #     cur=event.pos()-self.press_pos
    #     self.move(self.mapToParent(cur))
    #     event.accept()
    def _initSignals(self):
        self.ctrled=0
        self.cur=None
        self.cursor_moved.connect(self.handleCursorMove)
        self.timer=QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.pullCursor)
        self.timer.start()
        self.m_flag=False
        self.press_pos=self.pos()

    def handleCursorMove(self,pos):
        height=self.height()/2
        width=self.width()/2
        cur=QPoint(pos.x(),pos.y())-self.press_pos-QPoint(width,height)
        self.move(self.mapToParent(cur))
        self.press_pos=self.pos()

    # def pullCursor(self):
    #     import win32api,win32con
    #     step=2
    #     if (win32api.GetAsyncKeyState(win32con.VK_CONTROL) and
    #             not (win32api.GetAsyncKeyState(0x31) or win32api.GetAsyncKeyState(0x32)or win32api.GetAsyncKeyState(0x30)) ):
    #         self.ctrled=1
    #         self.hide()
    #     elif (win32api.GetAsyncKeyState(win32con.VK_CONTROL) and  win32api.GetAsyncKeyState(0x31) and self.ctrled) :
    #         self.ctrled=0
    #         width=self.width()
    #         self.setFixedSize(width+step,width+step)
    #         self.show()
    #         print("222", self.width(), self.height(), self.label.width(), self.label.height())
    #     elif (win32api.GetAsyncKeyState(win32con.VK_CONTROL) and  win32api.GetAsyncKeyState(0x30) and self.ctrled) :
    #         self.ctrled=0
    #         self.setFixedSize(self.default_width,self.default_height)
    #         # self.hot_key_event("")
    #         self.show()
    #     elif (win32api.GetAsyncKeyState(win32con.VK_CONTROL) and  win32api.GetAsyncKeyState(0x32) and self.ctrled) :
    #         self.ctrled=0
    #         width = self.width()
    #         if width-step>=5:
    #             self.setFixedSize(width - step, width - step)
    #         # print("222", self.width(), self.height(), self.label.width(), self.label.height())
    #         self.show()
    #     else:self.hide()
    #     pos=QCursor.pos()
    #     # if pos!=self.cur:
    #     self.cur=pos
    #     self.cursor_moved.emit(pos)
    def expand_range(self):
        step=2
        width = self.width()
        self.setFixedSize(width + step, width + step)
        self.show()
    def shrink_range(self):
        step=2
        width = self.width()
        if width - step >= 5:
            self.setFixedSize(width - step, width - step)
        # print("222", self.width(), self.height(), self.label.width(), self.label.height())
        self.show()
    def reset_range(self):
        self.setFixedSize(self.default_width, self.default_height)
        # self.hot_key_event("")
        self.show()


    def pullCursor(self):
        self.hide()
        pos=QCursor.pos()
        # if pos!=self.cur:
        self.cur=pos
        self.cursor_moved.emit(pos)
    def getAverageColor(self,x,y):

        window=int(QApplication.desktop().winId())
        width=self.width()-2
        height=self.height()-2
        screenshoot=QApplication.primaryScreen().grabWindow(window,x-width//2,y-height//2,width,height)
        # screenshoot.save('shot.jpg', 'jpg')
        # raise
        image=screenshoot.toImage()
        # 转换图像数据为NumPy数组

        channels_count = 4

        b = image.bits()
        # sip.voidptr must know size to support python buffer interface
        b.setsize(height * width * channels_count)
        arr = np.frombuffer(b, np.uint8).reshape((height, width, channels_count))
        b,g,r,a=np.mean(arr.astype(np.float32),axis=(0,1))
        # b,g,r=arr[2,2]
        b,g,r=np.uint8(b),np.uint8(g),np.uint8(r)
        # print("rgb",r,g,b)
        #
        # color=image.pixelColor(2,2)
        # r1,g1,b1=color.red(),color.green(),color.blue()
        # print("rgb1",r1,g1,b1)

        return (r,g,b),screenshoot


    def getCustomColor(self):
        pix = Screenshot.take_screenshot(constant.CLIPBOARD)#pixmap
        if pix is None:
            return None
        # raise
        width=pix.width()
        height=pix.height()
        image = pix.toImage()
        # 转换图像数据为NumPy数组

        channels_count = 4

        b = image.bits()
        # sip.voidptr must know size to support python buffer interface
        b.setsize(height * width * channels_count)
        arr = np.frombuffer(b, np.uint8).reshape((height, width, channels_count))
        b, g, r, a = np.mean(arr.astype(np.float32), axis=(0, 1))
        # b,g,r=arr[2,2]
        b, g, r = np.uint8(b), np.uint8(g), np.uint8(r)
        # print("rgb",r,g,b)
        #
        # color=image.pixelColor(2,2)
        # r1,g1,b1=color.red(),color.green(),color.blue()
        # print("rgb1",r1,g1,b1)

        return (r, g, b), pix