#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/27 22:14
# @File: XYZ.py
# @Software: PyCharm
#ref1:https://www.jianshu.com/p/854ca5f13ce6
#ref2:https://zhajiman.github.io/post/chromaticity_diagram/#%E6%9C%80%E7%BB%88%E6%95%88%E6%9E%9C


from src.color_utils.color_utils import color_RGB_to_XYZ, color_XYZ_to_RGB, color_XYZ_to_xyY, color_xyY_to_XYZ
import math
import  sys,os


try:
    from .color_utils.color_utils import color_Lab_to_RGB,color_RGB_to_Lab
except:
    from color_utils.color_utils import color_Lab_to_RGB,color_RGB_to_Lab

import numpy as np
from PyQt5.QtCore import  Qt,pyqtSlot,QPoint,pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QCloseEvent, QColor, QIcon,QPainter, QImage, QPixmap,QMouseEvent, QCursor

try:
    from .hue import  HueChart
except:
    from  hue import  HueChart
class XYZChart(HueChart):
    def set_zoom_size(self, ratio=1):
        super().set_zoom_size(ratio)
        self.hue.setObjectName("hue")
        self.hue.setStyleSheet("""
                        border-style: outset; border-width: 0px; border-radius: 0px;
                        """)
    def __init__(self,parent=None,mode="XYZ",gamut="P3-D65"):

        super().__init__(parent, mode=mode)
        self.XYZ_1 = None
        self.XYZ_2 = None
        self.colorspace = "XYZ"
        self.metric = ""
        self.gamut= gamut

        self.create_background()

    def create_background(self):
        self.load_xy_img()
    def load_xy_img(self):
        nsize=500
        import os
        filename = os.path.join("src","resource", "XYZ",  f"CIE_1931_chromaticity_diagram_{self.gamut}.png")

        print(os.path.abspath(filename))
        qpix=QPixmap(filename).scaled(self.hue.width()-1,self.hue.height()-1)
        painter=QPainter(qpix)
        painter.setPen((QColor(0,0,0)))
        # painter.drawLine(0,0,0,self.hue.height())
        # painter.drawLine(0, self.hue.height()-3,  self.hue.width() , self.hue.height()-3 )
        painter.end()
        self.hue.setPixmap(qpix)
    def set_gamut(self,gamut="P3-D65"):
        self.gamut=gamut
        self.load_xy_img()
    def freeze_cursor(self):
        super().freeze_cursor()
        self.XYZ_1=self.XYZ_2
    def pick_color(self,r,g,b):
        XYZ=color_RGB_to_XYZ(np.array([r,g,b])/255.0,gamut=self.gamut)
        X,Y,Z=XYZ
        x,y,Y=color_XYZ_to_xyY(XYZ)

        self.bar_length = self.luma.height()
        self.pie_radius=self.hue.height()/2

        self.luma_cur.move(QPoint(0,self.bar_length*(1-Y/1)-self.luma_cur.height()/2))

        self.left_bottom=QPoint(0,self.hue.height())
        dx=x/0.75*self.pie_radius*2
        dy=y/0.85*self.pie_radius*2
        self.hue_cur.move(self.left_bottom+QPoint(dx,-dy)
                          -QPoint(self.hue_cur.height()/2,self.hue_cur.height()/2))
        r,g,b=round(r),round(g),round(b)
        color_string = ",".join([str(r), str(g), str(b),str(1)])
        self.hue_cur.setStyleSheet("border-width: 1px;\n")
        self.XYZ_2=[X,Y,Z]
        self.pos_value_signal.emit([X,Y,Z,0])
        return X,Y,Z



def create_xyz_proj_cus(nsize=500,gamut="P3-D65"):
    import numpy as np
    import pandas as pd
    from skimage import io
    from skimage.draw import line
    import skimage
    # RGB Rectangle
    y_max = int(nsize / 0.85)
    x_max = int(nsize / 0.75)
    x = np.linspace(0, 0.75, nsize)
    y = np.linspace(0.85, 0.0, nsize).clip(1e-3, 0.85)
    X, Y = np.meshgrid(x, y)
    Z = 1 - X - Y
    XYZ = np.dstack((X, Y, Z))
    rgb = color_XYZ_to_RGB(XYZ, gamut=gamut)
    rgb /= rgb.max(axis=-1, keepdims=True)
    AP = np.ones([nsize, nsize, 1], dtype=np.uint8) * 255
    A5 = np.isnan(rgb)
    # rgb=rgb.clip(0,1)
    xyz = color_RGB_to_XYZ(rgb, gamut=gamut)
    # A2=np.max(np.abs(arr-xyz),axis=2)>0.001
    A3 = np.max(np.abs(rgb), axis=2) > 1
    A4 = np.min((rgb), axis=2) < 0
    A2 = A3 | A4 | A5[:, :, 0] | A5[:, :, 1] | A5[:, :, 2] | (Z < 0)
    # A2=A2+(rgb>1)[:,:,0]+(rgb<0)[:,:,0]
    AP[:, :, 0][A2] = 0
    rgb = rgb * 255
    rgb.clip(0, 255)
    img = np.array(rgb, dtype=np.uint8)

    # load CIE xyz CMF curve

    xyz_cc = pd.read_csv('./resource/CIEdata/cie_1931_2deg_xyz_cc.csv', index_col=0)
    xy = xyz_cc[['x', 'y']]
    r, c = xy["x"].values, xy["y"].values
    r = np.int16(np.round(r * x_max))
    c = np.int16(np.round(c * y_max))

    img = np.concatenate([img, AP], axis=2)
    # draw poly lines
    mask= np.zeros((nsize, nsize), dtype=bool)
    for i in range(len(r) - 1):
        rr, cc = line(r[i], c[i], r[i + 1], c[i + 1])
        cc = nsize - cc
        mask[cc, rr] = 1
    # draw the last line to close the polygon
    rr, cc = line(r[-1], c[-1], r[0], c[0])
    cc = nsize - cc
    mask[cc, rr] = 1
    #dilation
    from skimage.morphology import binary_dilation
    from skimage.morphology import disk
    mask = binary_dilation(mask, disk(2))
    img[mask]=[0,0,0,255]

    area = np.sum(A2)
    # plt.imshow(img)
    # plt.show()

    outfile=os.path.join("resource","XYZ",f"CIE_1931_chromaticity_diagram_{gamut}.png")
    io.imsave(outfile,img)

if __name__ == '__main__':
    # create_xyz_proj_cus(gamut="P3-D65")
    # create_xyz_proj_cus(gamut="P3-DCI")
    # create_xyz_proj_cus(gamut="sRGB")
    # create_xyz_proj_cus(gamut="Rec.2020")
    # create_xyz_proj_cus(gamut="Rec.709")
    create_xyz_proj_cus(gamut="AdobeRGB")

