#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: Epichide
# @Email: no email
# @Time: 2025/8/6 19:56
# @File: setting.py
# @Software: PyCharm
import os


# !/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5.QtCore import QSize, Qt

from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import (
    QDialog, QRadioButton, QTableWidgetItem, QGroupBox, QGridLayout, QFileDialog,
    QHBoxLayout,
    QMessageBox, QTabWidget
)

from PyQt5.QtWidgets import (QWidget, QVBoxLayout)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from .color_utils.iccinspector import iccProfile
from .record import RecordForm
from .color_utils.color_utils import *
from .wid_utils.hotkeys_utils.hotkey_wid import HotKeyWindow
from .utils.file_utils import _get_file

# 设置 matplotlib 支持中文显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
class ScrollSubTab(QtWidgets.QScrollArea):
    def __init__(self,parent=None):
        super(ScrollSubTab,self).__init__(parent)
        # css profile all information
        self.setWidgetResizable(True)
        self.setMinimumHeight(300)
        self.setMinimumWidth(100)
        self.info_scroll_wid = QtWidgets.QWidget(self)
        # self.info_scroll_wid 居中
        self.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter|QtCore.Qt.AlignTop )  # 设置滚动区域的对齐方式

        self.setWidget(self.info_scroll_wid)
        self.info_scroll_wid.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,  # 水平方向保持默认
            QtWidgets.QSizePolicy.MinimumExpanding  # 垂直方向根据内容调整
        )
        # 创建布局并设置对齐方式（布局才有 setAlignment 方法）
        layout = QVBoxLayout(self.info_scroll_wid)  # 布局直接关联到 info_scroll_wid
        # layout.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)  # 布局内控件的对齐方式
        layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        self.widget().setLayout(layout)

    def layout(self):
        return self.widget().layout()
    def resizeEvent(self, event):
        """重写尺寸变化事件，动态调整列宽"""
        # 忽略初始加载时的尺寸事件（避免覆盖手动设置）
        self.info_scroll_wid.setFixedWidth(self.width()*0.95)
        super().resizeEvent(event)
class ScrollTab(QtWidgets.QTabWidget):
    def __init__(self,parent=None):
        super(ScrollTab,self).__init__(parent)



    def add_tab(self, tabname, wid=None):
        if wid:
            tab = wid
        else:
            tab = ScrollSubTab(self)
            tab.setObjectName(tabname)
        self.addTab(tab, "")
        self.setTabText(self.indexOf(tab), tabname)
        return tab





class MplCanvas(FigureCanvas):
    """Matplotlib 画布，嵌入 PyQt 窗口"""

    def __init__(self, parent=None, dpi=100):
        # 创建图形和坐标轴
        self.fig = Figure(constrained_layout=True)
        self.axes = self.fig.add_subplot(111)  # 1行1列第1个子图
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.axes.set_title("TRC（Tone Response Curve，色调响应曲线）")  # 图表标题
        self.axes.set_xlabel("X 轴")  # X轴名称
        self.axes.set_ylabel("Y 轴")  # Y轴名称
        # 存储当前绘制的点
        self.point = None
        self.x_data = None
        self.y_data = None
        self.axes.grid(True)  # 显示网格

        # 初始化坐标显示文本（鼠标悬停时显示）
        self.coord_text = self.axes.text(0.55, 0.15, "", transform=self.axes.transAxes,
                                         bbox=dict(facecolor='white', alpha=0.8))

        # 绑定鼠标移动事件，用于显示坐标
        # self.mpl_connect('motion_notify_event', self.on_mouse_move)

    def resizeEvent(self, event):
        """重写 resizeEvent，确保画布大小变化时图形自动调整"""
        super().resizeEvent(event)
        # 手动触发布局调整（可选，增强自适应效果）
        self.axes.set_aspect('equal', adjustable='box')
        self.draw()
    def clear(self):
        # only clear curve and point
        self.x_data = None
        self.y_data = None
        # clear axes
        if hasattr(self.axes, 'lines') and len(self.axes.lines) > 0:
            # 清除所有线条（plot绘制的曲线）
            for line in self.axes.lines:
                line.remove()
        self.draw()

    def plot_curve(self, x, y, label="曲线"):
        """绘制曲线"""
        self.clear()
        self.x_data = x
        self.y_data = y
        self.axes.plot(x, y, label=label, color="gray")
        self.axes.set_title(label)  # 更新标题
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
            self.coord_text.set_text(f"")

            # 5. 清除旧点，绘制新点（曲线对应位置）
            if self.point is not None:
                self.point.remove()
            self.point = self.axes.scatter(x_mouse, y_curve, color='red', s=80,
                                           alpha=0.8, marker='o', edgecolor='black')

            # 刷新画布

            self.draw_idle()


class MplGamutCanvas(FigureCanvas):
    """Matplotlib 画布，嵌入 PyQt 窗口（支持多个独立基色点交互）"""

    def __init__(self, parent=None, dpi=100):
        # 保持原有初始化逻辑
        self.fig = Figure(constrained_layout=True, dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.rectangle = None


        self.rectangle_points = []  # 存储基色点的独立散点对象
        self.wp_point = None
        self.illum_points = []  # 存储所有独立色温点散点
        self.hover_point = None  # 当前悬停的点（散点对象）
        self.old_hover_point = None  # 当前悬停的点（散点对象）
        self.original_size = None  # 存储每个独立散点的原始大小

        self.wp_text = None
        self.point_texts = []
        self.default_size = 50
        self.hover_size = 100
        super(MplGamutCanvas, self).__init__(self.fig)

        self.setParent(parent)
        self.axes.set_title("xy chromaticity diagram")
        self.axes.set_xlabel("x axis")
        self.axes.set_ylabel("y axis")
        self.axes.grid(True)

        self.plot_wavelength_curve()
        self.plot_cct()
        self.coord_text = self.axes.text(
            0.6, 0.1, "",
            transform=self.axes.transAxes,
            bbox=dict(facecolor='white', alpha=0.8)
        )
        # self.mpl_connect('motion_notify_event', self.on_mouse_move)

    def clear(self):
        """清除所有元素并重置状态"""
        # 清除图形元素
        for p in [self.rectangle] :
            if p:
                p.remove()
        for p in  [self.wp_point]+ self.rectangle_points:
            if p:
                p[0].remove()
        for p in self.point_texts:
            p.remove()

        # 重置状态变量
        self.rectangle=None
        self.wp_point=None
        self.rectangle_points.clear()  # 清空基色点列表
        self.original_size=None
        self.hover_point = None
        self.point_texts = []
        self.coord_text.set_text("")

    def plot_primary(self, rgb_primarysT: np.ndarray, wp_xy, wpname=""):
        """绘制基色点（拆分为独立散点对象）"""
        self.clear()
        # 转换坐标
        rgb_primarys = [color_XYZ_to_xyY(XYZ)[:2] for XYZ in rgb_primarysT.T]
        rgb_primarys.append(rgb_primarys[0])  # 闭合矩形
        xs, ys = list(zip(*rgb_primarys))
        xs, ys = list(xs), list(ys)

        # 绘制矩形边框
        self.rectangle = self.axes.plot(xs, ys, color="gray", linestyle="-.")[0]

        # 基色点颜色列表
        colors = ["#ff0000", "#00ff00", "#0000ff"]

        # 逐个绘制基色点（每个点作为独立散点对象）
        self.rectangle_points = []  # 存储基色点散点对象
        for i,name in enumerate(["Red","Green","Blue"]):  # 前3个点为基色点
            x, y = xs[i], ys[i]
            # 创建独立散点对象（只包含当前点）
            scatter = self.axes.scatter(
                [x], [y],  # 用列表包裹单个点坐标
                marker="o",
                color=colors[i],
                s=self.default_size
            )
            self.rectangle_points.append([scatter,name])



            # 添加点坐标文本
            tex = self.axes.text(
                x, y + 0.02,
                f"({x:.2f}, {y:.2f})",
                color=colors[i],
                fontsize=12,
                ha="center", va="center"
            )
            self.point_texts.append(tex)

        # 绘制白点（作为独立散点）
        self.wp_point = [self.axes.scatter(
            [wp_xy[0]], [wp_xy[1]],  # 单个点
            marker="o",
            edgecolors="gray",
            color="white",
            s=self.default_size
        ),wpname]


        # 白点文本
        tex = self.axes.text(
            wp_xy[0], wp_xy[1] + 0.05,
                      wpname + f"({wp_xy[0]:.2f}, {wp_xy[1]:.2f})",
            color="black",
            fontsize=12,
            ha="center",
            va="center"
        )
        self.point_texts.append(tex)

        self.draw()

    def on_mouse_move(self, event):
        """处理鼠标移动，支持单个点的悬停检测"""
        if not event.inaxes == self.axes:
            self.coord_text.set_text("")
            self.draw_idle()
            return

        # 显示鼠标坐标
        x, y = event.xdata, event.ydata


        # 查找最近的点（遍历所有独立散点对象）
        min_dist = 0.02  # 触发距离阈值
        closest_point = None
        closest_name = None
        closest_dist = float('inf')

        all_points=[]
        all_points.extend(self.rectangle_points)
        if self.wp_point:
            all_points.append(self.wp_point)
        for scatter in all_points:
            scatter, typeName = scatter
            # 每个散点对象只包含一个点，直接取坐标
            if scatter.get_offsets().size == 0:
                continue
            px, py = scatter.get_offsets()[0]  # 取第一个（也是唯一一个）点

            # 计算距离
            dist = np.hypot(px - x, py - y)
            if dist < closest_dist and dist < min_dist:
                closest_dist = dist
                closest_name=typeName
                closest_point = scatter  # 记录整个散点对象（因为每个对象只含一个点）

        if not closest_point:
            for scatter in self.illum_points:
                # 每个散点对象只包含一个点，直接取坐标
                scatter,typeName=scatter
                if scatter.get_offsets().size == 0:
                    continue
                px, py = scatter.get_offsets()[0]  # 取第一个（也是唯一一个）点

                # 计算距离
                dist = np.hypot(px - x, py - y)
                if dist < closest_dist and dist < min_dist:
                    closest_name=typeName
                    closest_dist = dist
                    closest_point = scatter  # 记录整个散点对象（因为每个对象只含一个点）
        # 更新悬停状态
        if self.hover_point is None and closest_point: # None to Point
            self.hover_point = closest_point
            self.original_size = self.hover_point.get_sizes()[0]
            self._enlarge_point(self.hover_point,typeName)
        elif closest_point and closest_point != self.hover_point: # point to point

            self.hover_point.set_sizes([self.original_size])
            self.hover_point = closest_point
            self.original_size=self.hover_point.get_sizes()[0]
            self._enlarge_point(self.hover_point,typeName)
        elif not closest_point and self.hover_point is not None: # point to None
            self.hover_point.set_sizes([self.original_size])
            self.hover_point = None
            self.original_size=None
            
        elif not closest_point :
            self.coord_text.set_text(f"")

        self.draw_idle()

    def _enlarge_point(self, scatter,typename):
        """放大单个散点（因每个散点只含一个点，直接调整大小）"""
        scatter.set_sizes([self.hover_size])  # 单个点的大小
        # 显示该点坐标
        x, y = scatter.get_offsets()[0]
        self.coord_text.set_text(f"{typename} : ({x:.3f}, {y:.3f})")



    # 其他方法（plot_cct, plot_wavelength_curve, resizeEvent）保持不变
    def plot_cct(self):
        illums = []
        xs = []
        ys = []
        for k, v in White_ILLUMINANTS_xy.items():
            xs.append(v[0])
            ys.append(v[1])
            illums.append(k)

        sorted_data = sorted(zip(xs, ys, illums), key=lambda item: item[0])
        xs, ys, illums = zip(*sorted_data)

        # 每个色温点作为独立散点（可选，根据需求调整）
        for x, y,illum in zip(xs, ys,illums):
            scatter = self.axes.scatter(
                [x], [y],
                color="gray",
                marker=".",
                alpha=0.5,
                s=self.default_size
            )
            self.illum_points.append([scatter,illum])


    def plot_wavelength_curve(self):
        """绘制曲线"""

        data = np.genfromtxt(
            _get_file('./resource/CIEdata/cie_1931_2deg_xyz_cc.csv'),
            delimiter=',',  # 分隔符为逗号
            # skip_header=1,  # 跳过表头行
            dtype=None,  # 自动推断数据类型
            encoding='utf-8',  # 指定编码
            names=True  # 使用第一行作为字段名
        )

        r, c = data['x'], data['y']
        r = np.append(r, r[0])
        c = np.append(c, c[0])
        # r = np.int16(np.round(r * x_max))
        # c = np.int16(np.round(c * y_max))
        # 存储当前绘制的点
        self.x_data = r
        self.y_data = c
        if hasattr(self.axes, 'lines') and len(self.axes.lines) > 0:
            # 清除所有线条（plot绘制的曲线）
            for line in self.axes.lines:
                line.remove()
        self.axes.plot(r, c, label="", color="gray")
        # self.axes.legend()  # 显示图例
        self.draw()  # 刷新画布

    def resizeEvent(self, event):
        """重写 resizeEvent，确保画布大小变化时图形自动调整"""
        # 计算新的尺寸，保持1:1比例
        # new_size = min(event.size().width(), event.size().height())
        # event_size = QSize(new_size, new_size)
        #
        # # 应用新尺寸
        # self.setFixedSize(event_size)

        # 调用父类方法处理布局
        super().resizeEvent(event)

        # 调整坐标轴比例为1:1
        self.axes.set_aspect('equal', adjustable='box')

        # 刷新画布
        self.draw()

class ICCTable(QtWidgets.QTableWidget):
    def __init__(self,parent=None,headers=[]):
        super().__init__(parent)
        self.first_load=True
        self.init_ui(headers)

    def init_ui(self,headers=[]):

        self.setColumnCount(len(headers))
        self.setMinimumHeight(25)
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setCascadingSectionResizes(True)
        # -------------------- 核心设置：隐藏行索引 + 允许手动调整列宽 --------------------
        # 1. 隐藏垂直表头（行索引）
        self.horizontalHeader().setVisible(True)
        self.horizontalHeader().setCascadingSectionResizes(True)
        self.verticalHeader().setVisible(False)
        # self.tag_table.verticalHeader().setCascadingSectionResizes(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalScrollBar().setDisabled(False)
        self.setAutoScroll(False)
        # -------------------- 核心设置：不可编辑但可框选文本 --------------------
        # 1. 设置单元格不可编辑
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # 2. 允许选择单元格（支持框选）
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)  # 选中单元格
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)  # 支持按住Ctrl/Shift框选多个
        # 3. 允许文本被选中（确保可以复制）
        self.setTextElideMode(QtCore.Qt.ElideNone)  # 不省略文本，完整显示
        # 4. 可选：设置右键菜单支持复制（增强实用性）
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        # --------------------  自动调整列宽 --------------------
        # 初始状态：列宽自动适应内容（优先保证内容完整）
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )

        # 延迟切换为"交互式调整"（允许用户手动修改列宽）
        # 确保初始列宽已根据内容调整完成

        # 表格样式优化（可选）
        style_file= _get_file("resource/css/setting_ICCTable.css")
        self.load_style_from_file(style_file)  # 加载外部CSS

        # 延迟切换为手动调整模式（确保初始列宽计算完成）
        QtCore.QTimer.singleShot(100, self._enable_manual_resize)
    def load_style_from_file(self, style_file):
        """从CSS文件加载样式表"""
        try:
            # 检查文件是否存在
            if not os.path.exists(style_file):
                print(f"警告：样式文件 {style_file} 不存在，使用默认样式")
                return

            # 读取CSS文件内容
            with open(style_file, "r", encoding="utf-8") as f:
                style_content = f.read()

            # 应用样式表
            self.setStyleSheet(style_content)
            print(f"成功加载样式文件：{style_file}")

        except Exception as e:
            print(f"加载样式文件失败：{str(e)}")
    def _enable_manual_resize(self):
        """切换为允许手动调整列宽，同时记录初始列宽比例"""
        if self.columnCount() == 0:
            return
        # 最后一列设置为拉伸模式（填充空白），其他列允许手动调整
        for col in range(self.columnCount() - 1):
            self.horizontalHeader().setSectionResizeMode(
                col, QtWidgets.QHeaderView.Interactive
            )
        # 最后一列自适应剩余空间
        self.horizontalHeader().setSectionResizeMode(
            self.columnCount() - 1, QtWidgets.QHeaderView.Stretch
        )
        self.first_load = False  # 标记初始设置完成

    def show_context_menu(self, position):
        """右键菜单：添加复制功能"""
        menu = QtWidgets.QMenu()
        copy_action = menu.addAction("复制")
        copy_action.triggered.connect(self.copy_selected_text)
        menu.exec_(self.viewport().mapToGlobal(position))

    def copy_selected_text(self):
        """复制选中单元格的文本到剪贴板"""
        selected_items = self.selectedItems()
        if not selected_items:
            return
        # 按行拼接选中的文本（用制表符分隔列，换行分隔行）
        text = []
        current_row = -1
        for item in selected_items:
            if item.row() != current_row:
                if current_row != -1:
                    text.append("\n")
                current_row = item.row()
            else:
                text.append("\t")
            text.append(item.text())
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText("".join(text))
    def resizeEvent(self, event):
        """重写尺寸变化事件，动态调整列宽"""
        # 忽略初始加载时的尺寸事件（避免覆盖手动设置）
        if self.first_load:
            super().resizeEvent(event)
            return

        # 保存用户手动调整的列宽（最后一列除外，它是拉伸模式）
        user_sizes = []
        for col in range(self.columnCount() - 1):
            user_sizes.append(self.columnWidth(col))

        # 临时切换为"适应内容"模式，计算内容所需最小宽度
        for col in range(self.columnCount() - 1):
            self.horizontalHeader().setSectionResizeMode(
                col, QtWidgets.QHeaderView.ResizeToContents
            )

        # 计算内容所需最小宽度与用户设置宽度的最大值（保证内容不被截断）
        for col in range(self.columnCount() - 1):
            min_width = self.columnWidth(col)  # 内容所需最小宽度
            # 取用户设置宽度和内容最小宽度的最大值
            # target_width = max(user_sizes[col], min_width)
            # self.setColumnWidth(col, target_width)
            # 恢复手动调整模式
            self.horizontalHeader().setSectionResizeMode(
                col, QtWidgets.QHeaderView.Interactive
            )

        # 最后一列保持拉伸模式，填充剩余空间
        self.horizontalHeader().setSectionResizeMode(
            self.columnCount() - 1, QtWidgets.QHeaderView.Stretch
        )

        super().resizeEvent(event)
    def update_size(self,min_height=None):
        # 存储每行的默认高度（用于后续计算总高度）
        row_height = self.rowHeight(0)  # 获取默认行高
        if row_height == 0:  # 首次初始化时可能为0，手动设置默认值
            row_height = 25  # 像素
        # 1. 计算总高度：表头高度 + 所有行高度（行高 × 行数）
        header_height = self.horizontalHeader().height()  # 表头高度
        total_height = header_height + (row_height * self.rowCount())+5
        print(total_height)

        # 2. 给表格设置最小高度（确保能显示所有内容）
        if min_height:
            total_height=max(total_height,min_height)
        self.setMinimumHeight(total_height)

        self.horizontalHeader().setCascadingSectionResizes(True)
        return total_height+5

    def setItem(self,row, col, text):
        rowcnt=self.rowCount()
        colcnt=self.columnCount()

        if rowcnt-1<row:
            # self.insertRow(rowcnt)
            self.setRowCount(row+1) # 不会重置所有内容
        if colcnt-1<col:
            # self.insertColumn(colcnt)
            self.setColumnCount(col+1)
        super().setItem(row, col, QTableWidgetItem(text))


    def clear(self):
        """清空表格并将行数设置为1"""
        # super().clear()
        # 1. 获取当前列数
        col_count = self.columnCount()
        # 2. 清除所有行（设置行数为0）
        self.setRowCount(0)
        # 3. 设置行数为1
        self.setRowCount(1)
        # 4. 清空这一行的所有单元格（可选，确保没有残留数据）
        for col in range(col_count):
            # 如果单元格有内容则清空，没有则创建空item
            item = self.item(0, col)
            if item:
                item.setText('')
            else:
                self.setItem(0, col, QtWidgets.QTableWidgetItem(''))

class ICCRadio(QtWidgets.QRadioButton):
    def __init__(self,parent=None,text="",itype="icc"):
        """

        :param parent:
        :param text:
        :param itype:  built-in / icc
        """
        super(ICCRadio,self).__init__(parent)
        self.itype=itype
        self.setObjectName(text)
        self.setText(text)
        self.profile_info={}
        self.icc_file = None
        self.gamut_TRC_info={}
        self.icc_dict={}
        self.name_or_file=""
        if itype=="built-in":
            self.update_profile(text)
        else:
            self.setText("CUSTOM: None")
            self.setToolTip("double clike to select a custom icc profile")

    def update_profile(self,name_or_file):
        if name_or_file==self.name_or_file:
            return
        try:

            if self.itype == "icc":
                self.profile_info, self.gamut_TRC_info, self.icc_dict = self.parse_icc_profile(name_or_file)
                if not self.icc_dict["ProfileDeviceClass"][0] in ["mntr"]:
                    self.name_or_file=""
                    self.setText("CUSTOM: " + "ERROR")
                    raise TypeError("不支持非RGB类.icc文件\n"
                                    "只支持  'mntr' \n"
                                    f"该文件为 \'{self.icc_dict['ProfileDeviceClass'][0]}\' ")
                else:
                    self.name_or_file = name_or_file
                    self.setText("CUSTOM: " + get_basename(name_or_file, sufix_keep=True))
            elif self.itype == "built-in":
                self.profile_info, self.gamut_TRC_info, self.icc_dict = self.parse_gamut_profile(name_or_file)
                self.name_or_file = name_or_file
                self.setText(name_or_file)
        except Exception as e:
            qmsg = QMessageBox.information(
                self,  # 父窗口，None表示无父窗口
                "提示",  # 标题
                f"{type(e)}:\n{str(e)}"  # 内容
            )


    def parse_icc_profile(self, iccfile):
        """
        解析 ICC Profile 关键信息，这里简单模拟解析出类似你给的 Header Info 内容
        实际可结合 ImageCms 更细致解析字段，比如版本、设备类别等
        """
        # 打开并读取文件
        self.icc_file=_get_file(iccfile)
        try:
            with open(iccfile, 'rb') as f:
                # 读取文件内容到内存视图
                s = memoryview(f.read())
            testField = iccProfile()
            testField.read(s)
            ddict = testField.get_info()
        except Exception as e:
            print(f"解析 ICC 失败: {e}")
            raise Exception(f"解析 ICC 失败: {e}")

        gamut_TRC_info = {}
        gamut_profile_info = {}
        if ddict["ProfileDeviceClass"][0] in [ "mntr"]:
            RGB, linearRGB = ddict["TRC"]["xy"]
            function_str= ddict["TRC"]["function"]
            parameters = ddict["TRC"]["parameters"]
            curvetype= ddict["TRC"]["curvetype"]
            funcid = ddict["TRC"]["funcid"]


            # profile_info
            gamut_TRC_info = {
                "TRC-degamma": (RGB, linearRGB),
                "TRC-gamma": (linearRGB, RGB)
            }

            gamut_profile_info = {
                "Gamut" : get_basename(iccfile, sufix_keep=True),
                "Gamut Type" : "icc",
                "WP illuminant": ddict["WP_Illuminant"],  # White point
                "WP xy": ddict["WP_xyY"],
                "WP XYZ_Y1": ddict["WP_XYZ"],
                # the media white point of a Display class profile ;
                # media white point
                # https://www.color.org/whyd50.xalter
                "WP RGB2XYZ_matrix": np.round(ddict["WP_RGB2XYZ_matix"], 4),
                "WP XYZ2RGB_matrix": np.round(ddict["WP_XYZ2RGB_matrix"], 4),
                "TRC Function" : function_str,
                "TRC Parameters": parameters,
                "TRC Type": curvetype,
                "TRC FuncID": funcid,
                # PCS info
                "PCS Illuminant": ddict["PCS_Illuminant"],
                "PCS xy": ddict["PCS_xyY"],
                "PCS XYZ_Y1": ddict["PCS_XYZ"],
            }

        removekeys = ["TRC", "WP_Illuminant",
                      "WP_xyY", "WP_XYZ",
                      "PCS_Illuminant", "PCS_xyY",
                      "PCS_XYZ", "WP_RGB2XYZ_matix",
                      "WP_XYZ2RGB_matrix"]
        remove_keys(ddict, removekeys)
        ddict["ProfileName"] = get_basename(iccfile)
        return gamut_profile_info, gamut_TRC_info, ddict

    def parse_gamut_profile(self, gamut="P3-D65"):
        print(gamut)

        illuminant = Gmaut_Illuminant[gamut]
        xy_value = White_ILLUMINANTS_xy[illuminant]
        XYZ_Y1_value = get_white_point_XYZ(illuminant)

        RGB2XYZ_matix = np.round(get_RGB2XYZ_M(gamut)[0], 4)
        RGB2XYZ_matix = (RGB2XYZ_matix)
        XYZ2RGB_matix = np.round(get_XYZ2RGB_M(gamut)[0], 4)
        XYZ2RGB_matix = (XYZ2RGB_matix)

        RGB = np.arange(0, 1.01, 0.01)
        linearRGB = color_RGB_to_linearRGB(RGB, gamut=gamut)

        # CA:http://www.brucelindbloom.com/index.html?Eqn_ChromAdapt.html
        # source and target illuminant:https://color.org/whyd50.xalter
        # https://discuss.pixls.us/t/iccs-d50-vs-srgb-d65-problems/11134
        # https://color-image.com/2011/10/the-reference-white-in-adobe-photoshop-lab-mode/
        PCS_Illuminant = "D50"
        xy_value_PCS = White_ILLUMINANTS_xy[PCS_Illuminant]
        XYZ_Y1_PCS = get_white_point_XYZ(PCS_Illuminant)

        # profile_info
        gamut_TRC_info = {
            "TRC-degamma": (RGB, linearRGB),
            "TRC-gamma": (linearRGB, RGB)
        }

        gamut_profile_info = {
            "Gamut": self.objectName(),
            "Gamut Type": "built-in",
            "WP illuminant": illuminant,  # White point
            "WP xy": xy_value,
            "WP XYZ_Y1": XYZ_Y1_value,

            # the media white point of a Display class profile ;
            # media white point
            # https://www.color.org/whyd50.xalter
            "PCS Illuminant": PCS_Illuminant,
            "PCS xy": xy_value_PCS,
            "PCS XYZ_Y1": XYZ_Y1_PCS,

            "WP RGB2XYZ_matrix": RGB2XYZ_matix,
            "WP XYZ2RGB_matrix": XYZ2RGB_matix,
        }

        return gamut_profile_info, gamut_TRC_info, {"ProfileName": "built-in-" + gamut}


    def mouseDoubleClickEvent(self, *args, **kwargs):
        if self.itype=="icc":
            filepath = QFileDialog.getOpenFileName(self, 'Select a ICC Profile file', "", '*.icc *.icm')
            if len(filepath[0]) == 0: return
            self.update_profile(filepath[0])
            self.click()

    def get_gamut(self):
        self.profile_info["icc_file"] = self.icc_file
        if self.itype == "icc" and self.name_or_file=="":
            return None
        else:
            return self.profile_info



class ICCProfile(QWidget):
    def __init__(self, parent=None):
        super(ICCProfile, self).__init__(parent)
        self.gamut_TRC_info = {}
        self.profile_info = {}
        self.radio=None

        self.init_ui()

    def init_info_ui(self):
        # 分组显示信息： Info 类似分组

        self.info_tabbox = QTabWidget(self)
        self.sp.addWidget(self.info_tabbox)
        # WP info and matix
        self.WP_group = QGroupBox("white point and XYZ-RGB Matrix Info")
        self.WP_layout = QGridLayout(self.WP_group)
        self.WP_table = ICCTable(self,["Name","Value"])
        self.WP_layout.addWidget(self.WP_table)
        self.WP_group.setLayout(self.WP_layout)
        self.info_tabbox.addTab(self.WP_group, "WP Matrix")

        # css profile all information
        self.info_scroll = ScrollSubTab(self)
        self.info_layout = self.info_scroll.layout()
        # self.info_scroll.widget().setFixedSize(400,800)

        self.head_group = QGroupBox("Head Info",self)
        self.head_table = ICCTable(self, ["Head", "Value"])
        self.head_layout = QGridLayout(self.head_group)
        self.head_layout.addWidget(self.head_table)
        self.head_group.setLayout(self.head_layout)
        self.info_layout.addWidget(self.head_group)

        self.tag_group = QGroupBox("Tag Info",self)
        self.tag_table= ICCTable(self,["Signature","Type","Value"])
        self.tag_table.setShowGrid(False)
        self.tag_layout = QVBoxLayout(self.tag_group)
        self.tag_group.setLayout(self.tag_layout)
        self.tag_layout.addWidget(self.tag_table)

        self.info_layout.addWidget(self.tag_group)
        self.info_tabbox.addTab(self.info_scroll, "ICC Info")


    def init_TRC_WP_ui(self):
        # self.fig_tabbox = QTabWidget(self)
        # self.sp.addWidget(self.fig_tabbox)

        # plot TRC 生成示例数据并绘图
        self.TRC_group = QGroupBox("TRC（Tone Response Curve，色调响应曲线）")
        self.TRC_layout = QGridLayout(self.TRC_group)
        self.TRC_group.setLayout(self.TRC_layout)
        self.gamma_radio_box = QRadioButton("gamma")
        self.degamme_radio_box = QRadioButton("degamma")
        self.gamma_radio_box.clicked.connect(lambda: self.update_curve("gamma"))
        self.degamme_radio_box.clicked.connect(lambda: self.update_curve("degamma"))
        self.degamme_radio_box.setChecked(True)
        self.TRC_layout.addWidget(self.gamma_radio_box, 0, 0)
        self.TRC_layout.addWidget(self.degamme_radio_box, 0, 1)
        self.canvas = MplCanvas(self, dpi=100)
        self.TRC_layout.addWidget(self.canvas, 1, 0, 1, 2)  # 将画布添加到布局中
        # plot color space and WP
        self.XYZ_group = QGroupBox("Color Space and White Point",self)
        self.XYZ_layout=QGridLayout(self.XYZ_group)
        self.XYZ_canvas=MplGamutCanvas(dpi=100)
        self.XYZ_layout.addWidget(self.XYZ_canvas,0,0)
        self.XYZ_group.setLayout(self.XYZ_layout)
        self.info_tabbox.addTab(self.TRC_group, "TRC")
        self.info_tabbox.addTab(self.XYZ_group, "Gamut")
        # self.sp.addWidget(self.fig_tabbox)

    def init_ui(self):
        # 主布局
        self.main_layout = QHBoxLayout()
        self.setFixedHeight(450)

        # self.setFixedHeight(450)
        self.sp = QtWidgets.QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.sp)
        self.setLayout(self.main_layout)
        self.init_info_ui()
        self.init_TRC_WP_ui()
        self.sp.setStretchFactor(1, 1)
        self.sp.setStretchFactor(0, 1)

    def update_curve(self, gamma_type="degamma"):
        if gamma_type not in ["degamma", "gamma"]: return
        if not self.gamut_TRC_info: return
        if gamma_type == "degamma":
            if "TRC-degamma" not in self.gamut_TRC_info:
                print("没有TRC-degamma数据")
                return
            self.canvas.plot_curve(*self.gamut_TRC_info["TRC-degamma"], label="TRC-degamma")
        elif gamma_type == "gamma":
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


    def update_profile(self, radio:ICCRadio):
        self.profile_info, self.gamut_TRC_info, self.icc_dict = radio.profile_info,radio.gamut_TRC_info,radio.icc_dict
        self.radio=radio
        # ---update WP & matrix
        if radio.name_or_file=="":
            # clear all
            self.WP_table.clear()
            self.canvas.clear()
            self.XYZ_canvas.clear()
            self.update_icc_info()
            return

        self.WP_table.clear()
        row = 0
        for key, value in self.profile_info.items():

            self.WP_table.setItem(row,0,key)
            if isinstance(value,np.ndarray):
                for val in value:
                    self.WP_table.setItem(row, 1, str(val))
                    row+=1
            elif isinstance(value, dict):
                for k, v in value.items():
                    self.WP_table.setItem(row, 1, f"{k} = {v}")
                    row += 1
            else:
                self.WP_table.setItem(row,1,str(value))
                row += 1


        # ---plot TRC
        for radio in [self.degamme_radio_box,self.gamma_radio_box]:
            if radio.isChecked():
                self.update_curve(radio.text())


        # --plot chromaticity diagram

        self.XYZ_canvas.plot_primary(self.profile_info["WP RGB2XYZ_matrix"],# [Rcol,Gcol,Bcol]
                                     self.profile_info["WP xy"],
                                     self.profile_info["WP illuminant"])




        # ---update icc info
        self.update_icc_info()

    def update_icc_info(self):

        # 清空头部布局和标签表格

        self.head_table.clear()
        self.tag_table.clear()

        # 设置头部标题
        row = 0
        self.head_group.setTitle(f"Head Info : {self.icc_dict.get('ProfileName', '')}")

        tag_row = 0  # 表格行索引
        head_row=0

        for key, value in self.icc_dict.items():
            if "TagTable" in key:
                # 处理标签表格数据
                for tkey, tvalue in value.items():
                    # 1. 处理TRC类型标签（含多行参数）
                    if "TRC" in tkey:
                        # 第一行：Tag和Type
                        # self.tag_table.insertRow(tag_row)
                        self.tag_table.setItem(tag_row, 0, tkey)
                        self.tag_table.setItem(tag_row, 1, str(tvalue[0]))
                        self.tag_table.setItem(tag_row, 2, tvalue[1]["function"])
                        tag_row += 1

                        # 处理参数（字典或列表）
                        parameters = tvalue[1]["parameters"]
                        if isinstance(parameters, dict):
                            for paraname, paraval in parameters.items():
                                # self.tag_table.insertRow(tag_row)
                                # 参数行不显示Tag和Type，只显示参数名和值
                                self.tag_table.setItem(tag_row, 2, f"{paraname} = {paraval}")
                                tag_row += 1
                        elif isinstance(parameters, list) and len(parameters) == 1:
                            self.tag_table.insertRow(tag_row)
                            self.tag_table.setItem(tag_row, 2, f"g = {parameters[0]}")
                            tag_row += 1

                    # 2. 处理chad类型标签（矩阵数据）
                    elif "chad" in tkey:
                        # 第一行：Tag和Type
                        # self.tag_table.insertRow(tag_row)
                        self.tag_table.setItem(tag_row, 0, tkey)
                        self.tag_table.setItem(tag_row, 1, str(tvalue[0]))

                        # 矩阵数据分行显示
                        tvalue_data = tvalue[1].reshape(3, 3)  # 转换为3x3矩阵
                        for val in tvalue_data:
                            # self.tag_table.insertRow(tag_row)
                            self.tag_table.setItem(tag_row, 2, str(val))
                            tag_row += 1

                    # 3. 处理XYZ类型标签（含多行数据）
                    elif tvalue[0].strip() == "XYZ" and isinstance(tvalue[1], list) and isinstance(tvalue[1][0],
                                                                                                   np.ndarray):
                        # 第一行：Tag
                        # self.tag_table.insertRow(tag_row)
                        self.tag_table.setItem(tag_row, 0, tkey)


                        # 分行显示XYZ和xyY数据
                        ttrow = 0
                        for val in tvalue[1]:
                            self.tag_table.setItem(tag_row, 1, "XYZ,Y=1" if ttrow == 0 else "xyY,Y=1")
                            self.tag_table.setItem(tag_row, 2, str(val))
                            # self.tag_table.insertRow(tag_row)
                            ttrow += 1
                            tag_row += 1

                    # 4. 处理其他类型标签
                    else:
                        # self.tag_table.insertRow(tag_row)
                        self.tag_table.setItem(tag_row, 0, tkey)
                        self.tag_table.setItem(tag_row, 1, str(tvalue[0]))
                        self.tag_table.setItem(tag_row, 2, str(tvalue[1]))
                        tag_row += 1

            # 处理头部信息：迁移到self.head_table
            else:
                # 1. 处理列表类型value（含np.ndarray或普通列表）
                if isinstance(value, list) and isinstance(value[0], np.ndarray):
                    # 第一行显示key，后续行空出key列
                    self.head_table.insertRow(head_row)
                    self.head_table.setItem(head_row, 0, QtWidgets.QTableWidgetItem(key + ":"))  # Key列
                    # 第一行Value：XYZ,Y=1
                    label_type = " XYZ,Y=1: "
                    self.head_table.setItem(head_row, 1, QtWidgets.QTableWidgetItem(label_type + str(value[0])))
                    head_row += 1

                    # 后续行：xyY,Y=1（从第二元素开始）
                    for i in range(1, len(value)):
                        self.head_table.insertRow(head_row)
                        label_type = " xyY,Y=1: "
                        self.head_table.setItem(head_row, 1, QtWidgets.QTableWidgetItem(label_type + str(value[i])))
                        head_row += 1

                elif isinstance(value, list):
                    # 普通列表：第一行显示key，后续行空出key列
                    self.head_table.insertRow(head_row)
                    self.head_table.setItem(head_row, 0, QtWidgets.QTableWidgetItem(key + ":"))  # Key列
                    self.head_table.setItem(head_row, 1, QtWidgets.QTableWidgetItem(str(value[0])))  # 第一元素
                    head_row += 1

                    # 后续元素
                    for i in range(1, len(value)):
                        self.head_table.insertRow(head_row)
                        self.head_table.setItem(head_row, 1, QtWidgets.QTableWidgetItem(str(value[i])))
                        head_row += 1

                else:
                    # 非列表类型：一行显示key和value
                    self.head_table.insertRow(head_row)
                    self.head_table.setItem(head_row, 0, QtWidgets.QTableWidgetItem(key + ":"))
                    self.head_table.setItem(head_row, 1, QtWidgets.QTableWidgetItem(str(value)))
                    head_row += 1
        min_height=(self.info_scroll.height()-60)/2
        total_height=self.tag_table.update_size(min_height=min_height)
        total_head_height = self.head_table.update_size(min_height=min_height)
        print(min_height,total_height,total_head_height)
        # self.tag_group.setFixedHeight(total_height + 5)
        # self.head_group.setFixedHeight(total_head_height + 5)  # 头部表格高度自适应






class SettingDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SettingDialog, self).__init__(parent)
        self.profile={}
        self.setWindowTitle("Settings")

        self.setObjectName("Setting Dialog")
        self.resize(450, 650)
        style_file = _get_file("resource/css/SettingDialog.css")
        self.load_style_from_file(style_file)  # 加载外部CSS
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.setObjectName("buttonBox")
        # 绑定按钮事件（使用内置的accept和reject方法）
        self.buttonBox.accepted.connect(self.accept)  # OK按钮触发accept
        self.buttonBox.rejected.connect(self.reject)  # Cancel按钮触发reject
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)

        self.tabWidget = ScrollTab(self)
        self.verticalLayout.addWidget(self.tabWidget)
        self.verticalLayout.addWidget(self.buttonBox)
        self.setLayout(self.verticalLayout)
        # 设置默认字体

    def accept(self):
        self.metrics=self.metric_wid.get_metrics()
        self.hot_keys = self.hotkey_wid.get_hot_keys()[1] #  funcname: qtkeys

        self.seleted_gamut_info = self.gamut_info.radio.get_gamut() if self.gamut_info.radio else None  # 获取选中的gamut信息
        if self.seleted_gamut_info is None:
            QMessageBox.information(self, "Error", "Invalid custom icc profile.\n"
                                                   "Use the default sRGB gamutAutomatically")
            for radio in self.gamut_radios:
                if radio.objectName() == "sRGB":
                    radio.click()

                    self.seleted_gamut_info = self.gamut_info.radio.get_gamut() if self.gamut_info.radio else None  # 获取选中的gamut信息
                    break

        for radio in self.gamut_radios:
            if radio.objectName()=="CUSTOM":
                break
        custom_gamut=radio.get_gamut()
        if custom_gamut and (self.old_icc_file != custom_gamut.get("icc_file","")): # valid and return a profile dict

            gmsg=QMessageBox.information(self, "load icc ?", "Whether to save the custom icc profile ?",
                                QMessageBox.Ok| QMessageBox.Cancel)
            if gmsg!=QMessageBox.Ok:
                custom_gamut=None

        self.custom_gamut=custom_gamut




        super().accept()
    def load_style_from_file(self, style_file):
        """从CSS文件加载样式表"""
        try:
            # 检查文件是否存在
            if not os.path.exists(style_file):
                print(f"警告：样式文件 {style_file} 不存在，使用默认样式")
                return

            # 读取CSS文件内容
            with open(style_file, "r", encoding="utf-8") as f:
                style_content = f.read()

            # 应用样式表
            self.setStyleSheet(style_content)
            print(f"成功加载样式文件：{style_file}")

        except Exception as e:
            print(f"加载样式文件失败：{str(e)}")


    def func(self,ffunc,value):
        print(value)
        ffunc()

    def setupUi(self):

        self.wid_hotkey = self.Hotkey_Setting()  # 快捷键
        self.wid_colorspace = self.ColorSapce_Setting()  # 颜色空间



    def add_headder_title(self, layout, text):
        lab = QtWidgets.QLabel(self)
        # 使用传入的text参数，而不是固定文本
        lab.setText(f"<b> {text}:</b>")
        # 增加内边距让文字不贴边，更美观
        # lab.setStyleSheet("QLabel { "
        #                   "background-color: gray; "
        #                   "color: white; "
        #                   "padding: 2px 8px; }")
        # 设置水平扩展，垂直固定
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        lab.setSizePolicy(size_policy)
        # 文本左对齐
        lab.setAlignment(Qt.AlignLeft | Qt.AlignHCenter)
        # 移除alignment参数，允许标签水平扩展
        layout.addWidget(lab)
        return lab

    def Record_Setting(self, record: RecordForm = None):
        wid = self.tabWidget.add_tab("Record Setting")
        layout = wid.layout()
        if record is None:
            record = RecordForm(self)
        self.metric_wid = record.get_metric_choose()
        layout.addWidget(self.metric_wid)
        return wid
    def ColorSapce_Setting(self, gamuts=[],custom_gamut={},cur_gamut=""):
        wid=self.tabWidget.add_tab("Color Space")
        self.old_icc_file= custom_gamut.get("icc_file","")
        if self.old_icc_file:
            self.old_icc_file=_get_file(self.old_icc_file)
        layout=wid.layout()
        # Gamut
        gamut_ncol = 4
        gamut_nrow = (len(gamuts) + gamut_ncol - 1) // gamut_ncol
        gamut_label = QtWidgets.QLabel(self, text="Gamut:")
        # 创建QButtonGroup来管理单选按钮，确保互斥性
        self.gamut_button_group = QtWidgets.QButtonGroup(self)
        # 可选：设置为互斥模式（默认就是互斥，这里显式设置更清晰）
        self.gamut_button_group.setExclusive(True)
        gamut_grids_wid = QtWidgets.QWidget(self)
        # 设置部件的大小策略，允许垂直方向扩展
        gamut_grids = QtWidgets.QGridLayout(self)
        gamut_grids.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        gamut_grids_wid.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred,  # 水平方向保持默认
            QtWidgets.QSizePolicy.MinimumExpanding    # 垂直方向根据内容调整
        )
        gamut_grids.addWidget(gamut_label, 0, 0)
        gamut_grids_wid.setLayout(gamut_grids)
        gamut_grids_wid.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,  # 水平方向保持默认
            QtWidgets.QSizePolicy.Minimum  # 垂直方向根据内容调整
        )
        layout.addWidget(gamut_grids_wid)
        self.gamut_info = ICCProfile(self)
        layout.addWidget(self.gamut_info)
        self.gamut_radios = []
        if not gamuts:
            gamuts= ["P3-D65", "sRGB", "P3-DCI", "Rec.709", "Rec.2020", "AdobeRGB","CUSTOM"]
        for n, gamut in enumerate(gamuts):
            itype="icc" if gamut=="CUSTOM" else "built-in"
            gamut_radio = ICCRadio(self,gamut,itype)
            if itype=="icc":
                gamut_radio.update_profile(_get_file(custom_gamut.get("icc_file","")))

            gamut_radio.clicked.connect(lambda :self.on_radio_clicked(gamut))

            radio_row = n // gamut_ncol
            radio_col = n % gamut_ncol
            # 将单选按钮添加到按钮组
            # 第二个参数是可选的ID，用于区分不同按钮（这里用索引n作为ID）
            self.gamut_button_group.addButton(gamut_radio, n)
            gamut_grids.addWidget(gamut_radio, radio_row, radio_col + 1)
            self.gamut_radios.append(gamut_radio)
            if gamut == cur_gamut:
                gamut_radio.click()

        return wid


    def on_radio_clicked(self, gamut):
        for radio in self.gamut_radios:
            if radio.isChecked():
                gamut=radio.objectName()
                break
        if gamut is False: return # No choose
        # if radio.name_or_file=="": # No specify icc/gamut
        #     # clear iccprofile
        #     return
        self.gamut_info.update_profile(radio)


    def Hotkey_Setting(self, func_hotkeys={}):
        self.hotkey_wid = HotKeyWindow()
        for funcname,(func,qtkeys) in func_hotkeys.items():
            self.hotkey_wid.register(funcname, qtkeys)

        wid = self.tabWidget.add_tab("Hotkey",self.hotkey_wid)
        return self.hotkey_wid


def get_basename(filepath, sufix_keep=True):
    basename = os.path.basename(filepath)
    if sufix_keep: return basename
    basename = os.path.splitext(basename)[0]
    return basename


def remove_keys(ddict, keys):
    for key in keys:
        if key in ddict:
            ddict.pop(key)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    dialog = SettingDialog()
    result =dialog.exec_()
    if result==QDialog.Accepted:
        print(dialog.profile)

    sys.exit(result!=1)