#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/27 22:14
# @File: XYZ.py
# @Software: PyCharm
#ref1:https://www.jianshu.com/p/854ca5f13ce6
#ref2:https://zhajiman.github.io/post/chromaticity_diagram/#%E6%9C%80%E7%BB%88%E6%95%88%E6%9E%9C
from PIL import Image

from src.color_utils.color_utils import color_RGB_to_XYZ, color_XYZ_to_RGB, color_XYZ_to_xyY, color_xyY_to_XYZ
import math
import  sys,os
from .utils.file_utils import _get_file


try:
    from .color_utils.color_utils import color_Lab_to_RGB,color_RGB_to_Lab
except:
    from color_utils.color_utils import color_Lab_to_RGB,color_RGB_to_Lab

import numpy as np
from PyQt5.QtCore import  Qt,pyqtSlot,QPoint,pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QCloseEvent, QColor, QIcon,QPainter, QImage, QPixmap,QMouseEvent, QCursor

try:
    from .hue import  HueChart,BaseWidget
except:
    from  hue import  HueChart,BaseWidget
class XYZChart(HueChart):
    def set_zoom_size(self, ratio=1):
        super().set_zoom_size(ratio)
        self.hue.setObjectName("hue")
        self.hue.setStyleSheet("""
                        border-style: outset; border-width: 0px; border-radius: 0px;
                        """)
    def __init__(self,parent=None,gamut="P3-D65"):

        BaseWidget.__init__(self,parent)
        self.XYZ_1 = None
        self.XYZ_2 = None
        self.colorspace = "XYZ"
        self.metrics={
            "XYZ":0,
            # "xyY":0
        }
        self.metric = ""
        self.gamut= gamut
        self.init_ui()
        self.get_suggest_size(parent)
        self.set_zoom_size(1)


    def create_background(self):
        self.load_xy_img()
    def load_xy_img(self):
        nsize=500
        import os

        filename=_get_file(os.path.join("resource", "XYZ",  f"CIE_1931_chromaticity_diagram_{self.gamut}.png"))


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
        self.metrics["XYZ"]=[round(X,4), round(Y,4), round(Z,4)]
        self.pos_value_signal.emit(self.metrics)
        return X,Y,Z



def create_xyz_proj_cus(nsize=500,gamut="P3-D65"):
    import numpy as np



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

    # 读取CSV文件
    # 使用genfromtxt，跳过表头，自动处理数据类型
    data = np.genfromtxt(
        _get_file('./resource/CIEdata/cie_1931_2deg_xyz_cc.csv'),
        delimiter=',',  # 分隔符为逗号
        # skip_header=1,  # 跳过表头行
        dtype=None,  # 自动推断数据类型
        encoding='utf-8',  # 指定编码
        names=True  # 使用第一行作为字段名
    )


    r, c = data['x'], data['y']
    r = np.int16(np.round(r * x_max))
    c = np.int16(np.round(c * y_max))
    c= nsize-c  # invert y axis

    img = np.concatenate([img, AP], axis=2)
    # draw poly lines
    mask= np.zeros((nsize, nsize), dtype=bool)
    mask=plot_close_line(c,r, mask,thickness=4)


    img[mask]=[0,0,0,255]

    area = np.sum(A2)
    # plt.imshow(img)
    # plt.show()

    outfile=_get_file(os.path.join("resource","XYZ",f"CIE_1931_chromaticity_diagram_{gamut}.png"))
    if img.dtype != np.uint8:
        img = (img * 255).astype(np.uint8)  # 若原图在[0,1]范围，需转换为[0,255]
    # 转换为PIL图像并保存
    Image.fromarray(img).save(outfile)


def bresenham_line(x0, y0, x1, y1):
    """Bresenham线段算法，返回线段上所有点的坐标"""
    rows = []
    cols = []

    dx = x1 - x0
    dy = y1 - y0

    sx = 1 if dx > 0 else -1 if dx < 0 else 0
    sy = 1 if dy > 0 else -1 if dy < 0 else 0

    dx = abs(dx)
    dy = abs(dy)

    x, y = x0, y0
    rows.append(y)
    cols.append(x)

    # 处理特殊情况：水平线或垂直线
    if dx == 0:  # 垂直线
        while y != y1:
            y += sy
            rows.append(y)
            cols.append(x)
        return np.array(rows), np.array(cols)
    if dy == 0:  # 水平线
        while x != x1:
            x += sx
            rows.append(y)
            cols.append(x)
        return np.array(rows), np.array(cols)

    # 通用情况
    err = dx - dy
    while x != x1 or y != y1:
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
        rows.append(y)
        cols.append(x)

    return np.array(rows), np.array(cols)


def plot_close_line(r, c, mask,thickness=2):
    """
    绘制闭合多边形线段，返回布尔型掩码
    参数:
        r: 多边形顶点的行坐标列表
        c: 多边形顶点的列坐标列表
        nsize: 掩码尺寸（nsize x nsize）
    返回:
        mask: 布尔型掩码数组，线段位置为True
    """
    # 验证输入
    if len(r) != len(c):
        raise ValueError("r和c的长度必须相同")
    if len(r) < 2:
        raise ValueError("至少需要2个顶点才能形成闭合多边形")


    nsizeh, nsizew = mask.shape[:2]
    # 绘制多边形各边
    for i in range(len(r) - 1):
        rr, cc = bresenham_line(r[i], c[i], r[i + 1], c[i + 1])
        # 过滤超出边界的坐标

        valid = (cc >= 0) & (cc < nsizeh) & (rr >= 0) & (rr < nsizew)
        mask[cc[valid], rr[valid]] = True  # 布尔型赋值


    rr, cc = bresenham_line(r[-1], c[-1], r[0], c[0])


    valid = (cc >= 0) & (cc < nsizeh) & (rr >= 0) & (rr < nsizew)
    mask[cc[valid], rr[valid]] = True
    cc,rr=np.where(mask)
    # 绘制线段的厚度
    for i in range(-thickness // 2, thickness // 2 + 1):
        if i == 0:
            continue
        mask[cc + i, rr] = True
        mask[cc, rr + i] = True

    return mask


if __name__ == '__main__':
    # create_xyz_proj_cus(gamut="P3-D65")
    # create_xyz_proj_cus(gamut="P3-DCI")
    # create_xyz_proj_cus(gamut="sRGB")
    # create_xyz_proj_cus(gamut="Rec.2020")
    # create_xyz_proj_cus(gamut="Rec.709")
    create_xyz_proj_cus(gamut="AdobeRGB")

