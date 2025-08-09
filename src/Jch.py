#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2025/4/26 22:45
# @File: Jch.py
# @Software: PyCharm


from colorspacious import cspace_convert


import numpy as np

from PyQt5.QtCore import  Qt,pyqtSlot,QPoint,pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QCloseEvent, QColor, QIcon,QPainter, QImage, QPixmap,QMouseEvent, QCursor

try:
    from .hue import  HueChart
except:
    from hue import  HueChart
class JchChart(HueChart):

    def __init__(self,parent=None,mode="hsv"):
        super().__init__(parent)
        self.colorspace = "Jch"
        self.metrics ={
            "Jch":0,
        }
        self.metric = ""

    def create_background(self):
        self.load_jch_img()
    def load_jch_img(self):
        nsize=500
        filename="src/resource/JCH/30_jch_proj_30-100.png"
        import os
        print(os.path.abspath(filename))
        qpix=QPixmap(filename).scaled(self.hue.width()-1,self.hue.height()-1)
        #
        painter=QPainter(qpix)
        painter.setPen((QColor(0,0,0)))
        painter.drawLine(self.hue.width()/2,0,self.hue.width()/2,self.hue.height())

        painter.drawLine(0, self.hue.height() / 2,  self.hue.width() , self.hue.height()/2)
        painter.end()
        self.hue.setPixmap(qpix)
    def pick_color(self,r,g,b):
        from skimage import  color
        jch=cspace_convert(np.array([r,g,b])/255.0,"sRGB1","JCh")
        v,c,h=jch


        self.bar_length = self.luma.height()
        self.pie_radius=self.hue.height()/2
        s_ratio =  c/100
        h_ratio = h/360
        dy = -np.cos(h_ratio * 2 * np.pi) * s_ratio * self.pie_radius
        dx = np.sin(h_ratio * 2 * np.pi) * s_ratio * self.pie_radius

        self.luma_cur.move(QPoint(0,self.bar_length*(1-v/100)-self.luma_cur.height()/2))
        self.pie_center=(
            QPoint(self.pie_radius,self.pie_radius)-
            QPoint(self.hue_cur.height()/2,self.hue_cur.height()/2)

        )

        self.hue_cur.move(self.pie_center-QPoint(dy,dx))

        color_string = ",".join([str(r), str(g), str(b)])
        self.hue_cur.setStyleSheet("Qlabel{background-color: rgb(" + color_string + ");}")
        self.metrics["Jch"]=[v,c,h]
        self.pos_value_signal.emit(self.metrics)
        return v,c,h

def create_jch_img(l=50,nsize=500):
    x=np.linspace(-1,1,nsize)
    y=np.linspace(-1,1,nsize)
    y,x=np.mgrid[-1:1:nsize*1j,1:-1:nsize*-1j]

    A=np.ones([nsize,nsize,1],dtype=np.uint8)*255
    C=np.sqrt(x*x+y*y)
    ang=np.arctan2(y,x)+np.pi
    H=ang/np.pi*180
    J=np.ones([nsize,nsize],dtype=np.uint8)*l
    C*=100
    arr=np.ones([nsize,nsize,3])
    arr[:,:,0]=J
    arr[:,:,1]=C
    arr[:,:,2]=H

    rgb=cspace_convert(arr,"JCh","sRGB1")
    rgb2=np.clip(rgb,0,1)
    A2=np.max(np.abs(rgb-rgb2),axis=-1)>0.01
    rgb2=rgb2*255
    rgb2=np.array(rgb2,dtype=np.uint8)
    rgb2[A2]=0

    A[:,:,0][A2]=0

    img=np.array(rgb2,dtype=np.uint8)
    img=np.concatenate([img,A],axis=2)
    area=np.sum(A2)

    return img
def create_lab_proj(nsize=500,initial=30):
    img=np.zeros([nsize,nsize,4],dtype=np.uint8)
    mid=initial
    # for v in range(mid,1,-1):
    #     img_plane=create_jch_img(l=v,nsize=nsize)
    #     new_mask=img_plane[:,:,-1]>img[:,:,-1]
    #     img[new_mask]=img_plane[new_mask]
    for v in range(100,mid,-1):
        img_plane=create_jch_img(l=v,nsize=nsize)
        new_mask=img_plane[:,:,-1]>img[:,:,-1]
        img[new_mask]=img_plane[new_mask]
    from  skimage import  io
    io.imsave(str(mid)+f"_jch_proj_{mid}-100.png",img)

if __name__ == '__main__':
    create_lab_proj(500,30)
