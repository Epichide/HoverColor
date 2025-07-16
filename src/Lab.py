#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/27 22:14
# @File: hue.py
# @Software: PyCharm
import math
import  sys,os

import colour
import numpy as np
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import  Qt,pyqtSlot,QPoint,pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QCloseEvent, QColor, QIcon,QPainter, QImage, QPixmap,QMouseEvent, QCursor
from PyQt5.QtWidgets import  (QWidget,QHBoxLayout,QFrame,QLabel,
                              QApplication,QMenu,QAction,QMessageBox)
try:
    from .hue import  HueChart
except:
    from  hue import  HueChart
class LabChart(HueChart):

    def __init__(self,parent=None,mode="hsv"):
        super().__init__(parent)
        self.Lab_1 = None
        self.Lab_2 = None
        self.colorspace = "Lab"
        self.metric = "ΔE2000"
        self.load_lab_img()
    def load_lab_img(self):
        nsize=500
        filename="src/80_lab_proj_0-100.png"
        import os
        print(os.path.abspath(filename))
        qpix=QPixmap(filename).scaled(self.hue.width()-1,self.hue.height()-1)
        painter=QPainter(qpix)
        painter.setPen((QColor(0,0,0)))
        painter.drawLine(self.hue.width()/2,0,self.hue.width()/2,self.hue.height())
        painter.drawLine(0, self.hue.height() / 2,  self.hue.width() , self.hue.height()/2)
        painter.end()
        self.hue.setPixmap(qpix)
    def freeze_cursor(self):
        super().freeze_cursor()
        self.Lab_1=self.Lab_2
    def get_deltaE(self):

        '''Calculates CIEDE2000 color distance between two CIE L*a*b* colors'''
        C_25_7 = 6103515625  # 25**7
        Lab_1=self.Lab_1
        Lab_2=self.Lab_2
        if Lab_1 is None:
            return 0
        L1, a1, b1 = Lab_1[0], Lab_1[1], Lab_1[2]
        L2, a2, b2 = Lab_2[0], Lab_2[1], Lab_2[2]
        C1 = math.sqrt(a1 ** 2 + b1 ** 2)
        C2 = math.sqrt(a2 ** 2 + b2 ** 2)
        C_ave = (C1 + C2) / 2
        G = 0.5 * (1 - math.sqrt(C_ave ** 7 / (C_ave ** 7 + C_25_7)))

        L1_, L2_ = L1, L2
        a1_, a2_ = (1 + G) * a1, (1 + G) * a2
        b1_, b2_ = b1, b2

        C1_ = math.sqrt(a1_ ** 2 + b1_ ** 2)
        C2_ = math.sqrt(a2_ ** 2 + b2_ ** 2)

        if b1_ == 0 and a1_ == 0:
            h1_ = 0
        elif a1_ >= 0:
            h1_ = math.atan2(b1_, a1_)
        else:
            h1_ = math.atan2(b1_, a1_) + 2 * math.pi

        if b2_ == 0 and a2_ == 0:
            h2_ = 0
        elif a2_ >= 0:
            h2_ = math.atan2(b2_, a2_)
        else:
            h2_ = math.atan2(b2_, a2_) + 2 * math.pi

        dL_ = L2_ - L1_
        dC_ = C2_ - C1_
        dh_ = h2_ - h1_
        if C1_ * C2_ == 0:
            dh_ = 0
        elif dh_ > math.pi:
            dh_ -= 2 * math.pi
        elif dh_ < -math.pi:
            dh_ += 2 * math.pi
        dH_ = 2 * math.sqrt(C1_ * C2_) * math.sin(dh_ / 2)

        L_ave = (L1_ + L2_) / 2
        C_ave = (C1_ + C2_) / 2

        _dh = abs(h1_ - h2_)
        _sh = h1_ + h2_
        C1C2 = C1_ * C2_

        if _dh <= math.pi and C1C2 != 0:
            h_ave = (h1_ + h2_) / 2
        elif _dh > math.pi and _sh < 2 * math.pi and C1C2 != 0:
            h_ave = (h1_ + h2_) / 2 + math.pi
        elif _dh > math.pi and _sh >= 2 * math.pi and C1C2 != 0:
            h_ave = (h1_ + h2_) / 2 - math.pi
        else:
            h_ave = h1_ + h2_

        T = 1 - 0.17 * math.cos(h_ave - math.pi / 6) + 0.24 * math.cos(2 * h_ave) + 0.32 * math.cos(
            3 * h_ave + math.pi / 30) - 0.2 * math.cos(4 * h_ave - 63 * math.pi / 180)

        h_ave_deg = h_ave * 180 / math.pi
        if h_ave_deg < 0:
            h_ave_deg += 360
        elif h_ave_deg > 360:
            h_ave_deg -= 360
        dTheta = 30 * math.exp(-(((h_ave_deg - 275) / 25) ** 2))

        R_C = 2 * math.sqrt(C_ave ** 7 / (C_ave ** 7 + C_25_7))
        S_C = 1 + 0.045 * C_ave
        S_H = 1 + 0.015 * C_ave * T

        Lm50s = (L_ave - 50) ** 2
        S_L = 1 + 0.015 * Lm50s / math.sqrt(20 + Lm50s)
        R_T = -math.sin(dTheta * math.pi / 90) * R_C

        k_L, k_C, k_H = 1, 1, 1

        f_L = dL_ / k_L / S_L
        f_C = dC_ / k_C / S_C
        f_H = dH_ / k_H / S_H
        dE_00 = math.sqrt(f_L ** 2 + f_C ** 2 + f_H ** 2 + R_T * f_C * f_H)
        return dE_00
    def pick_color(self,r,g,b):
        from skimage import  color
        lab=color.rgb2lab(np.array([r,g,b])/255.0)
        v,la,lb=lab
        self.bar_length = self.luma.height()
        self.pie_radius=self.hue.height()/2

        self.luma_cur.move(QPoint(0,self.bar_length*(1-v/100)-self.luma_cur.height()/2))
        self.pie_center=(
            QPoint(self.pie_radius,self.pie_radius)-
            QPoint(self.hue_cur.height()/2,self.hue_cur.height()/2)

        )
        dx=-la/127*self.pie_radius
        dy=lb/127*self.pie_radius
        self.hue_cur.move(self.pie_center-QPoint(dx,dy))

        color_string = ",".join([str(r), str(g), str(b)])
        self.hue_cur.setStyleSheet("Qlabel{background-color: rgb(" + color_string + ");}")
        self.Lab_2=[v,la,lb]
        deltaE=self.get_deltaE()
        self.pos_value_signal.emit([v,la,lb,deltaE])
        return v,la,lb

def create_lab_img(l=50,nsize=500):
    x=np.linspace(-1,1,nsize)
    y=np.linspace(-1,1,nsize)
    A,B=np.mgrid[1:-1:nsize*-1j,-1:1:nsize*1j]
    S=np.sqrt(A*A+B*B)
    AP=np.ones([nsize,nsize,1],dtype=np.uint8)*255
    arr=np.ones([nsize,nsize,3])
    arr[:,:,0]=l
    arr[:,:,1]=B*127
    arr[:,:,2]=A*127
    from  skimage import color
    rgb=color.lab2rgb(arr)
    lab=color.rgb2lab(rgb)
    A2=np.max(np.abs(arr-lab),axis=2)>0.001
    AP[:,:,0][A2]=0
    rgb=rgb*255
    img=np.array(rgb,dtype=np.uint8)
    img=np.concatenate([img,AP],axis=2)
    area=np.sum(A2)
    # from skimage import io
    # io.imsave(str(l) + "_lab_proj_0-100.png", img)
    return img
def create_lab_proj(nsize=500,initial=50):
    img=np.zeros([nsize,nsize,4],dtype=np.uint8)
    mid=initial
    for v in range(mid,0,-1):
        img_plane=create_lab_img(l=v,nsize=nsize)
        new_mask=img_plane[:,:,-1]>img[:,:,-1]
        img[new_mask]=img_plane[new_mask]
    for v in range(mid,100,1):
        img_plane=create_lab_img(l=v,nsize=nsize)
        new_mask=img_plane[:,:,-1]>img[:,:,-1]
        img[new_mask]=img_plane[new_mask]
    from  skimage import  io
    io.imsave(str(mid)+"_lab_proj_0-100.png",img)

if __name__ == '__main__':
    create_lab_proj(500,80)
