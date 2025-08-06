#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: Epichide
# @Email: no email
# @Time: 2025/8/6 19:56
# @File: setting.py
# @Software: PyCharm


# !/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5.QtCore import QEventLoop

from hotkeys_utils.hotkey_wid import HotKeyWindow, HotkeyPicker
from PyQt5 import QtCore, QtGui, QtWidgets
from color_utils.color_utils import *

import sys
from PyQt5.QtWidgets import (
    QApplication, QRadioButton, QWidget, QVBoxLayout, QGroupBox, QGridLayout, QLabel
)
from PIL import Image, ImageCms
import io

import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor

# 设置 matplotlib 支持中文显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题


class MplCanvas(FigureCanvas):
    """Matplotlib 画布，嵌入 PyQt 窗口"""
    def __init__(self, parent=None,dpi=100):
        # 创建图形和坐标轴
        self.fig = Figure(constrained_layout=True)
        self.axes = self.fig.add_subplot(111)  # 1行1列第1个子图
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.axes.set_title("TRC（Tone Response Curve，色调响应曲线）")  # 图表标题
        self.axes.set_xlabel("X 轴")     # X轴名称
        self.axes.set_ylabel("Y 轴")     # Y轴名称
        # 存储当前绘制的点
        self.point = None
        self.x_data = None
        self.y_data = None
        self.axes.grid(True)  # 显示网格

        # 初始化坐标显示文本（鼠标悬停时显示）
        self.coord_text = self.axes.text(0.55, 0.15, "", transform=self.axes.transAxes,
                                        bbox=dict(facecolor='white', alpha=0.8))

        # 绑定鼠标移动事件，用于显示坐标
        self.mpl_connect('motion_notify_event', self.on_mouse_move)

    def resizeEvent(self, event):
        """重写 resizeEvent，确保画布大小变化时图形自动调整"""
        super().resizeEvent(event)
        # 手动触发布局调整（可选，增强自适应效果）
        self.fig.tight_layout()
        self.draw()
    def plot_curve(self, x, y, label="曲线"):
        """绘制曲线"""
        if hasattr(self.axes, 'lines') and len(self.axes.lines) > 0:
            # 清除所有线条（plot绘制的曲线）
            for line in self.axes.lines:
                line.remove()

        self.x_data = x
        self.y_data = y
        self.axes.plot(x, y, label=label,color="gray")
        self.axes.set_title(label) # 更新标题
        # self.axes.legend()  # 显示图例
        self.draw()  # 刷新画布

    def on_mouse_move(self, event):
        """鼠标移动时显示坐标"""
        if event.inaxes == self.axes:  # 鼠标在坐标轴内
            """鼠标x轴对应曲线x轴，显示曲线对应y值"""
            # 确保曲线数据已加载，且鼠标在坐标轴内
            if self.x_data is None or self.y_data is None:
                return

            # 1. 只取鼠标的x坐标（忽略鼠标y坐标）
            x_mouse = event.xdata

            # 2. 检查x是否在曲线x范围内（超出范围不绘制）
            x_min, x_max = np.min(self.x_data), np.max(self.x_data)
            if not (x_min <= x_mouse <= x_max):
                # 超出范围：清除点和文本
                if self.point is not None:
                    self.point.remove()
                    self.point = None
                    self.coord_text.set_text("")
                    self.draw_idle()
                return

            # 3. 插值计算曲线在x_mouse处的y值（线性插值）
            # 线性插值：即使x_mouse不在原始数据点上，也能得到对应y
            y_curve = np.interp(x_mouse, self.x_data, self.y_data)

            # 4. 更新坐标文本（显示曲线的x和y）
            self.coord_text.set_text(f"X: {x_mouse:.2f}, Y: {y_curve:.2f}")

            # 5. 清除旧点，绘制新点（曲线对应位置）
            if self.point is not None:
                self.point.remove()
            self.point = self.axes.scatter(x_mouse, y_curve, color='red', s=80,
                                           alpha=0.8, marker='o', edgecolor='black')

            # 刷新画布
            self.draw_idle()




class ICCProfile(QWidget):
    def __init__(self, parent=None):
        super(ICCProfile, self).__init__(parent)
        self.gamut_TRC_info = {}
        self.profile_info = {}

        self.init_ui()

    def init_ui(self):
        # 主布局
        self.main_layout = QVBoxLayout()

        # 分组显示信息：Header Info 类似分组
        self.header_group = QGroupBox("Header Info")
        self.header_layout = QGridLayout(self.header_group)
        self.header_group.setLayout(self.header_layout)
        self.setStyleSheet("""
                   QLabel[objectName="RowLabel"] {
                    border-top: 0px dashed #999;   /* 上边框 */
                    border-bottom: 1px solid #999;/* 下边框 */
                    padding: 5px 0;                /* 上下内边距，左右0避免内容贴边 */
                    margin: 0;                     /* 去除外边距，避免额外间隙 */
                }
                """)
        self.main_layout.addWidget(self.header_group)

        # plot TRC 生成示例数据并绘图
        self.TRC_group = QGroupBox("TRC（Tone Response Curve，色调响应曲线）")
        self.TRC_layout = QGridLayout(self.TRC_group)
        self.TRC_group.setLayout(self.TRC_layout)

        self.gamma_radio_box=QRadioButton("gamma")
        self.degamme_radio_box=QRadioButton("degamma")
        self.gamma_radio_box.clicked.connect(lambda : self.update_curve("gamma"))
        self.degamme_radio_box.clicked.connect(lambda: self.update_curve("degamma"))
        self.TRC_layout.addWidget(self.gamma_radio_box, 0, 0)
        self.TRC_layout.addWidget(self.degamme_radio_box, 0, 1)

        self.canvas = MplCanvas(self, dpi=100)
        self.TRC_layout.addWidget(self.canvas, 1, 0, 1, 2)  # 将画布添加到布局中
        self.main_layout.addWidget(self.TRC_group)

        self.setLayout(self.main_layout)
    def update_curve(self,gamma_type="degamma"):
        if gamma_type not in ["degamma", "gamma"]: return
        if not self.gamut_TRC_info:return
        if gamma_type=="degamma":
            if "TRC-degamma" not in self.gamut_TRC_info:
                print("没有TRC-degamma数据")
                return
            self.canvas.plot_curve(*self.gamut_TRC_info["TRC-degamma"], label="TRC-degamma")
        elif gamma_type=="gamma":
            if "TRC-gamma" not in self.gamut_TRC_info:
                print("没有TRC-gamma数据")
                return
            self.canvas.plot_curve(*self.gamut_TRC_info["TRC-gamma"], label="TRC-gamma")
    def clear_layout(self, layout):
        """安全清除布局中的所有子控件"""
        if layout is None:
            return
        # 从布局中移除并删除所有控件
        while layout.count():
            item = layout.takeAt(0)  # 取出布局中的第一个项目
            widget = item.widget()
            if widget:
                widget.deleteLater()  # 彻底删除控件
            # 如果有嵌套布局，递归清除
            child_layout = item.layout()
            if child_layout:
                self.clear_layout(child_layout)
    def update_profile(self, nameorpath,type="icc"):
        self.clear_layout(self.header_layout)

        if type=="icc":
            self.icc_path = nameorpath
        elif type=="gamut":
            self.profile_info,self.gamut_TRC_info = self.parse_gamut_profile(nameorpath)

        row = 0
        for key, value in self.profile_info.items():
            label_key = QLabel(key + ":")
            label_key.setObjectName("RowLabel")
            label_value = QLabel(str(value))
            label_value.setObjectName("RowLabel")

            self.header_layout.addWidget(label_key, row, 0)
            self.header_layout.addWidget(label_value, row, 1)
            row += 1
        self.header_group.setLayout(self.header_layout)
        # plot TRC
        self.canvas.plot_curve(*self.gamut_TRC_info["TRC-degamma"], label="TRC-degamma")


    def parse_gamut_profile(self, gamut="P3-D65"):
        print(gamut)

        illuminant = Gmaut_Illuminant[gamut]
        xy_value = White_ILLUMINANTS_xy[illuminant]
        XYZ_Y1_value = get_white_point_XYZ(illuminant)

        RGB2XYZ_matix = np.round(get_RGB2XYZ_M(gamut), 4)
        RGB2XYZ_matix = str(RGB2XYZ_matix)
        XYZ2RGB_matix = np.round(get_XYZ2RGB_M(gamut), 4)
        XYZ2RGB_matix = str(XYZ2RGB_matix)

        RGB=np.arange(0,1.01,0.01)
        linearRGB=color_RGB_to_linearRGB(RGB, gamut=gamut)

        # CA:http://www.brucelindbloom.com/index.html?Eqn_ChromAdapt.html
        # source and target illuminant:https://color.org/whyd50.xalter
        # https://discuss.pixls.us/t/iccs-d50-vs-srgb-d65-problems/11134
        # https://color-image.com/2011/10/the-reference-white-in-adobe-photoshop-lab-mode/

        


        # profile_info
        gamut_TRC_info={
            "TRC-degamma": (RGB, linearRGB),
            "TRC-gamma": (linearRGB, RGB)
        }
        gamut_profile_info={
            "illuminant": illuminant,
            "xy_value": xy_value,
            "XYZ_Y1_value": XYZ_Y1_value,
            "RGB2XYZ_matrix": RGB2XYZ_matix,
            "XYZ2RGB_matrix": XYZ2RGB_matix
        }

        return gamut_profile_info,gamut_TRC_info
    def parse_icc_profile(self):
        """
        解析 ICC Profile 关键信息，这里简单模拟解析出类似你给的 Header Info 内容
        实际可结合 ImageCms 更细致解析字段，比如版本、设备类别等
        """
        try:
            # 读取 ICC Profile
            with open(self.icc_path, 'rb') as f:
                icc_data = f.read()
            f = io.BytesIO(icc_data)
            prf = ImageCms.ImageCmsProfile(f)

            # 这里手动模拟解析出你示例里的字段，实际可基于 prf 更多 API 精细解析
            # 以下字段需根据真实解析逻辑完善，当前是演示写法
            info = {
                "Size": "676 bytes",
                "CMM Type": "ADBE",
                "Version": "0x420000",
                "Device Class": "display",
                "Color Space": "RGB",
                "PCS": "XYZ",
                "Date": "2016/9/7, 20:28:18",
                "Magic": "acsp",
                "Platform": "",  # 需真实解析补充
                "Flags": "not embedded, independently",
                "Manufacturer": "ADBE",
                "Model": "0x0",
                "Attribute": "reflective, glossy, positive, color",
                "Intent": "X=0.96420, Y=1.00000, Z=0.82491",  # 示例值
                "Illuminant": "",  # 需真实解析补充
                "Creator": "ADBE",
                "Profile ID": "231859a4-3eac-754e-9821-98d472a5b292"
            }

            # 也可结合 prf 提供的属性进一步填充，比如：
            # info["Version"] = prf.profile.version  # 需看实际可用属性

            return info
        except Exception as e:
            print(f"解析 ICC 失败: {e}")
            return {}



class SettingDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SettingDialog, self).__init__(parent)
        self.setupUi()

    def add_tab(self, tabname, wid=None):
        if wid:
            tab = wid
        else:
            tab = QtWidgets.QWidget()
            tab.setObjectName(tabname)
        self.tabWidget.addTab(tab, "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(tab), tabname)
        return tab

    def setupUi(self):
        self.setObjectName("Setting Dialog")
        self.resize(400, 800)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)

        self.tabWidget = QtWidgets.QTabWidget(self)
        self.tabWidget.setObjectName("tabWidget")
        self.verticalLayout.addWidget(self.tabWidget)
        self.verticalLayout.addWidget(self.buttonBox)
        self.setLayout(self.verticalLayout)

        self.wid_hotkey = self.Hotkey_Setting()  # 快捷键
        self.wid_colorspace = self.ColorSapce_Setting()  # 颜色空间
        self.tab_colorspace = self.add_tab("ColorSpace", self.wid_colorspace)
        self.tab_hotkey = self.add_tab("HotKey", self.wid_hotkey)

    def ColorSapce_Setting(self, standard_colorspaces_wids=[], device_colorspaces_wids=[]):
        wid = QtWidgets.QWidget(self.tabWidget)
        verticalLayout = QtWidgets.QVBoxLayout(self)
        std_colorspaces_lab = QtWidgets.QLabel(self)
        std_colorspaces_lab.setText("<b> Standard ColorSpaces</b>:")
        dev_colorspaces_lab = QtWidgets.QLabel(self)
        dev_colorspaces_lab.setText("<b> Device ColorSpaces:</b>")
        verticalLayout.addWidget(std_colorspaces_lab)

        # std panel
        standard_colorspacess = ["XYZ", "Lab"]
        std_color_lab = QtWidgets.QLabel(self, text="ColorSpace:")
        standard_grids = QtWidgets.QGridLayout(self)
        standard_grids.addWidget(std_color_lab, 0, 0)
        for nnol in range(6):
            standard_grids.setColumnStretch(nnol, 1)

        for n, colorsp_name in enumerate(standard_colorspacess):
            standard_colorspaces_box = QtWidgets.QCheckBox(self, text=colorsp_name)
            standard_grids.addWidget(standard_colorspaces_box, n // 3, n % 3 + 1)
            # standard_colorspaces_wids.append(standard_colorspaces_box)
            standard_colorspaces_box.setChecked(True)

        verticalLayout.addLayout(standard_grids)

        # Gamut
        gamuts = ["P3-D65", "sRGB", "P3-DCI", "Rec.709", "Rec.2020", "AdobeRGB"]
        gamut_ncol = 4
        gamut_nrow = (len(gamuts) + gamut_ncol - 1) // gamut_ncol
        gamut_label = QtWidgets.QLabel(self, text="Gamut:")

        gamut_grids = QtWidgets.QGridLayout(self)
        gamut_grids.addWidget(gamut_label, 0, 0)
        self.gamut_radios = []
        for n, gamut in enumerate(gamuts):
            gamut_radio = QtWidgets.QRadioButton(wid)
            gamut_radio.setText(gamut)
            gamut_radio.clicked.connect(self.on_radio_clicked)
            radio_row = n // gamut_ncol
            radio_col = n % gamut_ncol
            gamut_grids.addWidget(gamut_radio, radio_row, radio_col + 1)
            self.gamut_radios.append(gamut_radio)
        self.gamut_radios[0].setChecked(True)
        verticalLayout.addLayout(gamut_grids)
        self.gamut_info = ICCProfile(self)
        verticalLayout.addWidget(self.gamut_info)

        # dev panel
        verticalLayout.addWidget(dev_colorspaces_lab)
        device_colorspacess = ["RGB", "YUV", "HSV"]
        std_color_lab = QtWidgets.QLabel(self, text="ColorSpace:")
        device_grids = QtWidgets.QGridLayout(self)
        for nnol in range(6):
            device_grids.setColumnStretch(nnol, 1)
        device_grids.addWidget(std_color_lab, 0, 0)
        for n, colorsp_name in enumerate(device_colorspacess):
            device_colorspaces_box = QtWidgets.QCheckBox(self, text=colorsp_name)
            device_grids.addWidget(device_colorspaces_box, n // 3, n % 3 + 1)
            # device_colorspaces_wids.append(device_colorspaces_box)
            device_colorspaces_box.setChecked(True)

        verticalLayout.addLayout(device_grids)

        wid.setLayout(verticalLayout)
        return wid

    def on_radio_clicked(self, gamut):
        for radio in self.gamut_radios:
            if radio.isChecked():
                gamut = radio.text()
                break
        print(gamut)

        self.gamut_info.update_profile(gamut, type="gamut")

    def Hotkey_Setting(self):
        self.inhotkey = True
        self.func_hotkeys = {}
        loop = QEventLoop()
        hotkey_wid = HotKeyWindow()
        for funcname, (func, qtkeys) in self.func_hotkeys.items():
            hotkey_wid.register(funcname, qtkeys)
        self.inhotkey = False

        return hotkey_wid


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    dialog = SettingDialog()
    dialog.show()
    sys.exit(app.exec_())
