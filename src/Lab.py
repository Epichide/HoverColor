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
        dy=la/127*self.pie_radius
        dx=lb/127*self.pie_radius
        self.hue_cur.move(self.pie_center-QPoint(dx,dy))

        color_string = ",".join([str(r), str(g), str(b)])
        self.hue_cur.setStyleSheet("Qlabel{background-color: rgb(" + color_string + ");}")
        self.pos_value_signal.emit(v,la,lb)
        return v,la,lb

def create_lab_img(l=50,nsize=500):
    x=np.linspace(-1,1,nsize)
    y=np.linspace(-1,1,nsize)
    B,A=np.mgrid[1:-1:nsize*-1j,1:-1:nsize*-1j]
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
