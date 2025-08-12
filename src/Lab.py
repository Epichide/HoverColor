#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/27 22:14
# @File: hue.py
# @Software: PyCharm
import math
import  sys,os

from PIL import Image

try:
    from .utils.file_utils import _get_file
    from .color_utils.color_utils import color_Lab_to_Lch, color_Lab_to_RGB, color_RGB_to_Lab
except:
    from color_utils.color_utils import color_Lab_to_RGB,color_RGB_to_Lab

import numpy as np
from PyQt5.QtCore import  Qt,pyqtSlot,QPoint,pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QCloseEvent, QColor, QIcon,QPainter, QImage, QPixmap,QMouseEvent, QCursor

try:
    from .hue import  HueChart
except:
    from  hue import  HueChart
class LabChart(HueChart):

    def __init__(self,parent=None,mode="hsv",gamut="P3-D65"):
        super().__init__(parent)
        self.Lab_1 = None
        self.Lab_2 = None
        self.colorspace = "Lab"
        self.metrics={
            "Lab":0,
            "ΔE2000":0,
            "Lch":0
        }
        self.metric = "ΔE2000"
        self.gamut= gamut
        self.create_background()
    def create_background(self):
        self.load_lab_img()
    def load_lab_img(self):
        nsize=500
        import os
        filename = os.path.join("src","resource", "Lab",  f"80_lab_proj_0-100_{self.gamut}.png")

        print(os.path.abspath(filename))
        qpix=QPixmap(filename).scaled(self.hue.width()-1,self.hue.height()-1)
        painter=QPainter(qpix)
        painter.setPen((QColor(0,0,0)))
        painter.drawLine(self.hue.width()/2,0,self.hue.width()/2,self.hue.height())
        painter.drawLine(0, self.hue.height() / 2,  self.hue.width() , self.hue.height()/2)
        painter.end()
        self.hue.setPixmap(qpix)
    def set_gamut(self,gamut="P3-D65"):
        self.gamut=gamut
        self.load_lab_img()
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
        lab=color_RGB_to_Lab(np.array([r,g,b])/255.0,gamut=self.gamut)
        v,la,lb=lab
        self.bar_length = self.luma.height()
        self.pie_radius=self.hue.height()/2

        self.luma_cur.move(QPoint(0,self.bar_length*(1-v/100)-self.luma_cur.height()/2))
        self.pie_center=(
            QPoint(self.pie_radius,self.pie_radius)-
            QPoint(self.hue_cur.height()/2,self.hue_cur.height()/2)

        )
        dx=-la/180*self.pie_radius
        dy=lb/180*self.pie_radius
        self.hue_cur.move(self.pie_center-QPoint(dx,dy))

        color_string = ",".join([str(r), str(g), str(b)])
        self.hue_cur.setStyleSheet("Qlabel{background-color: rgb(" + color_string + ");}")
        self.Lab_2=[v,la,lb]
        deltaE=self.get_deltaE()
        self.metrics["Lab"]=[round(v,2), round(la,2), round(lb,2)]
        self.metrics["ΔE2000"]=np.round(deltaE,4)
        lch=color_Lab_to_Lch(np.array([v,la,lb]))
        l,c,h=lch
        self.metrics["Lch"]=[round(l,2), round(c,2), round(h,2)]
        self.pos_value_signal.emit(self.metrics)
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
    if img.dtype != np.uint8:
        img = (img * 255).astype(np.uint8)  # 若原图在[0,1]范围，需转换为[0,255]
    # 转换为PIL图像并保存
    Image.fromarray(img).save(str(mid)+"_lab_proj_0-100.png")
def create_lab_img_cus(l=50,nsize=500,gamut="P3-D65"):
    x=np.linspace(-1,1,nsize)
    y=np.linspace(-1,1,nsize)
    B,A=np.mgrid[1:-1:nsize*-1j,-1:1:nsize*1j]
    S=np.sqrt(A*A+B*B)
    AP=np.ones([nsize,nsize,1],dtype=np.uint8)*255
    arr=np.ones([nsize,nsize,3])
    arr[:,:,0]=l
    arr[:,:,1]=A*180
    arr[:,:,2]=B*180
    rgb=color_Lab_to_RGB(arr,gamut=gamut)
    A5=np.isnan(rgb)
    # rgb=rgb.clip(0,1)
    lab=color_RGB_to_Lab(rgb,gamut=gamut)
    A2=np.max(np.abs(arr-lab),axis=2)>0.1
    A3=np.max(np.abs(rgb),axis=2)>1
    A4=np.min((rgb),axis=2)<0
    A2=A2|A3|A4|A5[:,:,0]|A5[:,:,1]|A5[:,:,2]
    # A2=A2+(rgb>1)[:,:,0]+(rgb<0)[:,:,0]
    AP[:,:,0][A2]=0
    rgb=rgb*255
    rgb.clip(0,255)
    img=np.array(rgb,dtype=np.uint8)
    img=np.concatenate([img,AP],axis=2)
    area=np.sum(A2)
    # from matplotlib import pyplot as plt
    # plt.imshow(np.max(np.abs(arr-lab),axis=-1))
    # plt.imshow(img)
    # plt.show()
    # from skimage import io
    # io.imsave(str(l) + "_lab_proj_0-100.png", img)
    return img
def create_lab_proj_cus(nsize=500,initial=80,gamut="P3-D65"):

    img=np.zeros([nsize,nsize,4],dtype=np.uint8)
    mid=initial
    for v in range(mid,0,-1):
        img_plane=create_lab_img_cus(l=v,nsize=nsize,gamut=gamut)
        new_mask=img_plane[:,:,-1]>img[:,:,-1]
        img[new_mask]=img_plane[new_mask]
    for v in range(mid,100,1):
        img_plane=create_lab_img_cus(l=v,nsize=nsize,gamut=gamut)
        new_mask=img_plane[:,:,-1]>img[:,:,-1]
        img[new_mask]=img_plane[new_mask]

    outfile=_get_file(os.path.join("resource","Lab",str(mid)+f"_lab_proj_0-100_{gamut}.png"))
    # 若图像是numpy数组，需确保数据类型正确（通常为uint8）
    if img.dtype != np.uint8:
        img = (img * 255).astype(np.uint8)  # 若原图在[0,1]范围，需转换为[0,255]
    # 转换为PIL图像并保存
    Image.fromarray(img).save(outfile)


if __name__ == '__main__':
    # create_lab_proj_cus(500,80,gamut="P3-D65")
    # create_lab_proj_cus(500,80,gamut="sRGB")
    # create_lab_proj_cus(500,80,gamut="P3-DCI")
    # create_lab_proj_cus(500,80,gamut="Rec.709")
    # create_lab_proj_cus(500,80,gamut="Rec.2020")
    # create_lab_proj_cus(500,80,gamut="AdobeRGB")
    create_lab_proj_cus(500,80,gamut="CUSTOM")
    # create_lab_proj_cus(500,80,gamut="")
