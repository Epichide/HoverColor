# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/27 22:14
# @File: XYZ.py
# @Software: PyCharm
#ref1:https://www.jianshu.com/p/854ca5f13ce6
#ref2:https://zhajiman.github.io/post/chromaticity_diagram/#%E6%9C%80%E7%BB%88%E6%95%88%E6%9E%9C
from PIL import Image

from src.color_utils.color_utils import WEIGHTS_YPBPR_rbuv, color_RGB_to_XYZ, color_XYZ_to_RGB, color_XYZ_to_xyY, \
    color_xyY_to_XYZ

import  sys,os


try:
    from .color_utils.color_utils import color_RGB_to_YCbCr,color_RGB_to_YPbPr,color_YPbPr_to_RGB
    from .utils.file_utils import _get_file
    from .hue import  HueChart,BaseWidget
except:
    from color_utils.color_utils import color_RGB_to_YCbCr,color_RGB_to_YPbPr,color_YPbPr_to_RGB
    from utils.file_utils import _get_file
    from  hue import  HueChart,BaseWidget

import numpy as np
from PyQt5.QtCore import  Qt,pyqtSlot,QPoint,pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QCloseEvent, QColor, QIcon,QPainter, QImage, QPixmap,QMouseEvent, QCursor


class YUVChart(HueChart):
    def set_zoom_size(self, ratio=1):
        super().set_zoom_size(ratio)
        self.hue.setObjectName("hue")
        self.hue.setStyleSheet("""
                        border-style: outset; border-width: 0px; border-radius: 0px;
                        """)
    def __init__(self,parent=None,criteria="ITU-R-BT.601"):
        BaseWidget.__init__(self,parent)
        self.XYZ_1 = None
        self.XYZ_2 = None
        self.colorspace = "YUV"
        self.metrics={
            "YUV-470":0,
            "YUV-709":0,
            "YPbPr-601":0,
            "YCbCr-601": 0,
            "YPbPr-709": 0,
            "YCbCr-709": 0,
            "YPbPr-2020": 0,
            "YCbCr-2020": 0,
            "YPbPr-SMPTE-240M": 0,
            "YCbCr-SMPTE-240M": 0,
        }
        self.name_dict={
            "YUV-470": "SDTV-with-BT.470",
            "YUV-709": "HDTV-with-BT.709",
            "YPbPr-601": "ITU-R-BT.601",
            "YCbCr-601": "ITU-R-BT.601",
            "YPbPr-709": "ITU-R-BT.709",
            "YCbCr-709": "ITU-R-BT.709",
            "YPbPr-2020": "ITU-R-BT.2020",
            "YCbCr-2020": "ITU-R-BT.2020",
            "YPbPr-SMPTE-240M": "SMPTE-240M",
            "YCbCr-SMPTE-240M": "SMPTE-240M",
        }

        self.metric = "YCbCr-601"
        self.criteria= criteria
        self.init_ui()
        self.get_suggest_size(parent)
        self.set_zoom_size(1)


    def create_background(self):
        self.load_yuv_img()
    def load_yuv_img(self):
        nsize=500
        import os
        filename = _get_file(os.path.join(os.path.join("resource","YUV",f"100_yuv_proj_0-100_{self.criteria}.png")))
        print(os.path.abspath(filename))
        qpix=QPixmap(filename).scaled(self.hue.width()-1,self.hue.height()-1)
        painter=QPainter(qpix)
        painter.setPen((QColor(0,0,0)))
        painter.drawLine(self.hue.width() / 2, 0, self.hue.width() / 2, self.hue.height())
        painter.drawLine(0, self.hue.height() / 2, self.hue.width(), self.hue.height() / 2)

        # painter.drawLine(0,0,0,self.hue.height())
        # painter.drawLine(0, self.hue.height()-3,  self.hue.width() , self.hue.height()-3 )
        painter.end()
        self.hue.setPixmap(qpix)
    def set_criteria(self,criteria="ITU-R-BT.601"):
        self.criteria=criteria
        self.load_yuv_img()
    def freeze_cursor(self):
        super().freeze_cursor()
        self.XYZ_1=self.XYZ_2
    def pick_color(self,r,g,b):
        YPbPr=color_RGB_to_YPbPr(np.array([r,g,b]),criteria=self.criteria)
        Y,pb,pr=YPbPr

        self.bar_length = self.luma.height()
        self.pie_radius=self.hue.height()/2

        self.luma_cur.move(QPoint(0,self.bar_length*(1-Y/1)-self.luma_cur.height()/2))

        self.left_bottom=QPoint(0,self.hue.height())
        dx=pr/0.62*self.pie_radius
        dy=pb/0.62*self.pie_radius
        self.pie_center = (
                QPoint(self.pie_radius, self.pie_radius) -
                QPoint(self.hue_cur.height() / 2, self.hue_cur.height() / 2)

        )
        self.hue_cur.move(self.pie_center + QPoint(dy, dx))
        r,g,b=round(r),round(g),round(b)
        color_string = ",".join([str(r), str(g), str(b),str(1)])
        self.hue_cur.setStyleSheet("border-width: 1px;\n")
        self.XYZ_2=[Y,pb,pr]
        for metric in self.metrics:
            if "YCbCr" in metric:
                Ycbcr=color_RGB_to_YCbCr(np.array([r,g,b]),criteria=self.name_dict[metric])
                self.metrics[metric]=list(np.round(Ycbcr,3))
            else:
                YPbPr=color_RGB_to_YPbPr(np.array([r,g,b]),criteria=self.name_dict[metric])
                self.metrics[metric]=list(np.round(YPbPr,2))

        self.pos_value_signal.emit(self.metrics)
        return Y,pb,pr

def create_yuv_img_cus(l=0.5,nsize=500,criteria="ITU-R-BT.601"):

    range_max=0.62
    x = np.linspace(-range_max, range_max, nsize)
    y = np.linspace(-range_max, range_max, nsize)
    X, Y = np.meshgrid(x, y)

    AP=np.ones([nsize,nsize,1],dtype=np.uint8)*255
    arr=np.ones([nsize,nsize,3])
    arr[:,:,0]=l
    arr[:,:,1]=X
    arr[:,:,2]=Y
    rgb=color_YPbPr_to_RGB(arr,criteria=criteria)
    A5=np.isnan(rgb)
    # rgb=rgb.clip(0,1)
    ypbpr=color_RGB_to_YPbPr(rgb,criteria=criteria)
    A2=np.max(np.abs(arr-ypbpr),axis=2)>0.1
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
def create_yuv_proj_cus(nsize=500,initial=100,criteria="ITU-R-BT.601"):

    img=np.zeros([nsize,nsize,4],dtype=np.uint8)
    mid=initial
    for v in range(mid,0,-1):
        img_plane=create_yuv_img_cus(l=v/100,nsize=nsize,criteria=criteria)
        new_mask=img_plane[:,:,-1]>img[:,:,-1]
        img[new_mask]=img_plane[new_mask]
    for v in range(mid,100,1):
        img_plane=create_yuv_img_cus(l=v/100,nsize=nsize,criteria=criteria)
        new_mask=img_plane[:,:,-1]>img[:,:,-1]
        img[new_mask]=img_plane[new_mask]

    outfile=_get_file(os.path.join("resource","YUV",str(mid)+f"_yuv_proj_0-100_{criteria}.png"))
    # 若图像是numpy数组，需确保数据类型正确（通常为uint8）
    if img.dtype != np.uint8:
        img = (img * 255).astype(np.uint8)  # 若原图在[0,1]范围，需转换为[0,255]
    # 转换为PIL图像并保存
    Image.fromarray(img).save(outfile)

if __name__ == '__main__':
    for criteria in WEIGHTS_YPBPR_rbuv.keys():
        create_yuv_proj_cus(criteria=criteria)