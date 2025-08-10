#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/14 20:47
# @File: record.py
# @Software: PyCharm
import os
from collections import defaultdict, deque
from typing import List

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import  Qt,pyqtSlot,QPoint,pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QCloseEvent, QColor, QFont, QIcon, QMouseEvent, QCursor
from PyQt5.QtWidgets import (QAbstractItemView, QGridLayout, QVBoxLayout, QWidget, QHBoxLayout, QFrame, QLabel,
                             QTableWidget,
                             QApplication, QMenu, QAction, QMessageBox)

from src.basepanel import BaseWidget
def _get_file(relative_path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__),relative_path))

class ColorSpaceGroup(QtWidgets.QGroupBox):
    metric_choose_signal = pyqtSignal(list) # colorspce, metric
    def __init__(self, parent=None,wid:BaseWidget=None):
        super(ColorSpaceGroup, self).__init__(parent)

        self.setTitle(wid.colorspace)
        self.button_group = QtWidgets.QButtonGroup(self)
        # 可选：设置duoxuan模式（默认就是互斥）
        self.button_group.setExclusive(False)
        self.option_layout=QVBoxLayout(self)
        self.option_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.setLayout(self.option_layout)
        idx=0
        for metric,value in wid.metrics.items():
            ckb=QtWidgets.QCheckBox(metric,self)
            ckb.setObjectName(metric)

            ckb.stateChanged.connect(
                lambda state, m=metric:
                self.metric_choose_signal.emit([wid.colorspace, m, Qt.Checked])
                if state == Qt.Checked
                else self.metric_choose_signal.emit([wid.colorspace, m, Qt.Unchecked])
            )
            self.button_group.addButton(ckb,idx)
            self.option_layout.addWidget(ckb)
            idx+=1
    def triget_metric(self,metric):
        for i in range(self.option_layout.count()):
            ckb = self.option_layout.itemAt(i).widget()
            if ckb.objectName() == metric:
                ckb.setChecked(True)


class MetricsGroup(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super(MetricsGroup,self).__init__(parent)
        self.colorspace_dicts={}
        self.device_grids = QGridLayout(self)
        self.setLayout(self.device_grids)
        self.choose_layout=QHBoxLayout(self)
        self.info_lab=QLabel("Choose Heads:",self)
        self.device_grids.addWidget(self.info_lab,0,0,1,1)

        self.device_grids.addLayout(self.choose_layout,0,1,1,2)
        self.choose_layout.setAlignment(QtCore.Qt.AlignLeft)

        self.clear_btn= QtWidgets.QPushButton("Clear",self)
        self.clear_btn.clicked.connect(lambda :self.clear())
        self.device_grids.addWidget(self.clear_btn,0,3,1,1)
        for col in range(4):
            self.device_grids.setColumnStretch(col, 1)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred,  # 水平方向保持默认
            QtWidgets.QSizePolicy.MinimumExpanding    # 垂直方向根据内容调整
        )
        self.device_grids.setRowStretch(2, 1)  # 第1行（空行）拉伸占满剩余空间
    def init_ui(self,colorspace_wids:List[BaseWidget]):
        self.colorspace_dicts.clear()
        for n, colorsp in enumerate(colorspace_wids):
            colorsp_chooses = ColorSpaceGroup(self, colorsp)
            for metric in colorsp.metrics.keys():
                self.colorspace_dicts[metric]=colorsp_chooses
            self.device_grids.addWidget(colorsp_chooses, n // 4+1, n % 4)
            colorsp_chooses.metric_choose_signal.connect(self.change_metric)
    def set_metrics(self,metrics:List[str]):

        self.clear()
        for metric in metrics:
            if metric not in self.colorspace_dicts:
                continue
            colorsp_chooses= self.colorspace_dicts[metric]
            colorsp_chooses.triget_metric(metric)

    def get_metrics(self):
        metrics=[]
        for i in range(self.choose_layout.count()):
            wid = self.choose_layout.itemAt(i).widget()
            metrics.append(wid.objectName())
        return metrics
    def clear(self):
        for i in range(self.choose_layout.count()):
            wid = self.choose_layout.itemAt(i).widget()
            wid.deleteLater()

        self.update()
        self.repaint()
    def change_metric(self,signals):
        colorspace, metric, IsChecked=signals
        if IsChecked:
            for i in range(self.choose_layout.count()):
                wid = self.choose_layout.itemAt(i).widget()
                if wid.objectName() == metric:
                    return # already exists
            wid= QLabel(f"{colorspace}:{metric}", self)
            wid.setStyleSheet("border: 1px solid #bce0f9; "
                              "padding: 2px;")
            wid.setObjectName(metric)

            self.choose_layout.addWidget(wid)
        else:
            for i in range(self.choose_layout.count()):
                wid = self.choose_layout.itemAt(i).widget()
                if wid.objectName() == metric:
                    wid.deleteLater()
                    break

class RecordForm(QTableWidget):
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
    def get_metric_choose(self):
        metric_gp=MetricsGroup(self)
        metric_gp.init_ui(list(self.connected_wid))
        metric_gp.set_metrics(self.metrics)
        return metric_gp
    def set_font_size(self,fontsize):
        self.font_size1=fontsize
        font_size = self.font_size1 * self.ratio
        font= self.horizontalHeader().font()
        font.setPixelSize(font_size)
        self.horizontalHeader().setFont(font)
        font = self.font()
        font.setPixelSize(font_size)
        self.setFont(font)
    def set_zoom_size(self, ratio=1):
        self.ratio=ratio
        defaultHeight=self.defaultHeight*self.ratio
        defaultWidth=self.defaultWidth*self.ratio
        font_size =self.font_size1 *self.ratio
        
        font=self.font()
        font.setPixelSize(font_size)
        # self.setFont(font)
        self.setGeometry(QtCore.QRect(0, 0, defaultWidth, defaultHeight))
        self.setFixedSize(defaultWidth, defaultHeight)
        self.setFixedWidth(defaultWidth)
        self.setFixedHeight(defaultHeight)
        self.horizontalHeader().setFixedHeight(defaultHeight / (self.nrow + 1))
        font.setBold(True)
        self.horizontalHeader().setFont(font)
        self.horizontalHeader().setMinimumSectionSize(1)
        self.verticalHeader().setDefaultSectionSize(defaultHeight/ (self.nrow + 1))
        self.verticalHeader().setMinimumSectionSize(defaultHeight*0.2 / (self.nrow + 1))


        
    def get_suggest_size(self,parent):
        if parent is None:
            self.defaultHeight = 175
            self.defaultWidth = 160
            self.font_size1=8
        else:
            #0.02 + 0.850 + 0.01 + 0.06 +0.02
            self.defaultHeight = parent.single_wid_width*0.95
            self.defaultWidth = parent.single_wid_width*0.9
            self.font_size1 = 10

    def __init__(self,parent=None):
        super(RecordForm,self).__init__(parent)

        self.nrow=5
        self.ncol=2
        self.func=None

        self.connected_wid=set()
        self.metrics=[]
        self.redords=defaultdict(dict) # {metric:[],metric:[]}

        self.max_records_num=10

        self.setMinimumSize(1,1)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # self.setFocusPolicy(Qt.NoFocus)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setColumnCount(self.ncol)
        self.setRowCount(self.nrow)
        self.horizontalHeader().setVisible(True)
        self.horizontalHeader().setCascadingSectionResizes(True)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setCascadingSectionResizes(True)
        style_file = _get_file("resource/css/RecordForm.css")
        self.load_style_from_file(style_file)  # 加载外部CSS
        # self.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        # self.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        # self.verticalScrollBar().setDisabled(True)
        # self.setAutoScroll(False)
        # self.setShowGrid(False)
        # self.setAttribute(Qt.AA_EnableHighDpiScaling)
        # self.verticalHeader().setDefaultSectionSize(self.defaultHeight / (self.nrow + 1))
        # heads = self.horizontalHeader()
        # heads.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        self.init_ui()

        self.get_suggest_size(parent)
        self.set_zoom_size(1)

    def adjust_column_width(self, refwidth=0):
        self.ncol=max(len(self.metrics),1)
        # height=self.nrow*self.rowHeight(0)*self.ratio
        self.setColumnCount(self.ncol)
        # self.setFixedHeight(height)
        width=max(self.ncol* self.defaultWidth*self.ratio*0.7,refwidth)
        self.setFixedWidth(width)
    def get_width_hint(self):
        self.ncol = max(len(self.metrics), 1)
        width = max(self.ncol * self.defaultWidth*self.ratio*0.7 , 0)
        return width



    def dis_connect_wid(self,wid):
        if wid not in self.connected_wid: return
        self.connected_wid.remove(wid)
        metrics = wid.metrics
        for metric in metrics:
            self.redords.pop(metric)
            if metric in self.metrics:
                self.metrics.remove(metric)

        item=self.horizontalHeaderItem(0)
        item.setText("")

    def connect_wid(self,wid):
        colorspace=wid.colorspace
        metrics=wid.metrics

        for metric in metrics:
            self.redords[metric] = {}
        for metric in self.redords.keys():
            self.redords[metric]={
                "values":deque(),
                "cur_value":None
            }

        func=lambda values_dict:self.update_value(values_dict)
        wid.pos_value_signal.connect(func)
        self.connected_wid.add(wid)

    def set_show_metrics(self,metrics):
        self.metrics= metrics
        self.clear()
        self.ncol = len(self.metrics)
        self.setColumnCount(len(self.metrics))
        self.setRowCount(self.nrow)
        self.setHorizontalHeaderLabels(metrics)

        for metric in metrics:
            if metric in self.metrics:
                col_idx= self.metrics.index(metric)
                values=list(self.redords[metric]["values"])
                for row, val in enumerate(values[::-1], 1):
                    if row > self.nrow - 1: break
                    self.set_item(row, col_idx, val)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        # 调用主窗口的鼠标按下处理（假设主窗口有此方法）
        if hasattr(self.parent(), 'mousePressEvent'):
            self.parent().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        # 调用主窗口的鼠标移动处理
        if hasattr(self.parent(), 'mouseMoveEvent'):
            self.parent().mouseMoveEvent(event)


    def set_item(self,row,col,value):
        rowcnt=self.rowCount()
        colcnt=self.columnCount()

        if rowcnt-1<row:
            # self.insertRow(rowcnt)
            self.setRowCount(row+1) # 不会重置所有内容
        if colcnt-1<col:
            # self.insertColumn(colcnt)
            self.setColumnCount(col+1)
        item = self.item(row, col) # metric
        if  not item:
            self.setItem(row, col, QtWidgets.QTableWidgetItem(''))
            item = self.item(row, col)
        item.setTextAlignment(Qt.AlignCenter)
        if row==0:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        # iterable
        if isinstance(value, (list, tuple)):
            item.setText(", ".join([str(x) for x in value]))
        else:
            item.setText(str(value))

        # cur_record_cnt = len(self.redords[self.showed_wid.colorspace]["values"])
        if row==0:
            r, g, b = self.redords["RGB"]["cur_value"]
            gray = max(r, g , b)
        elif row<=len(self.redords["RGB"]["values"]):
            r,g,b=self.redords["RGB"]["values"][-row]
            gray = max(r , g , b)
        else:
            return
        item.setBackground(QtGui.QColor(r, g, b))
        if gray>128:
            item.setForeground(QtGui.QColor(0, 0, 0))
        else:
            item.setForeground(QtGui.QColor(255,255,255))



    def update_value(self,values_dict):
        for metric,value in values_dict.items():
            if metric in self.redords:
                self.redords[metric]["cur_value"] = value
            if metric in self.metrics:
                col_idx = self.metrics.index(metric)
                self.set_item(0,col_idx,value)


    def init_ui(self):


        item=QtWidgets.QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)

        self.setHorizontalHeaderLabels(["Value", "deltaE"])
        # self.setRowHeight(0, 1)

        for i in range(0,self.nrow):
            for j in range(self.ncol):
                item=QtWidgets.QTableWidgetItem()
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter)
                item.setText("")
                item.setBackground(QColor(220,220,220))
                self.setItem(i,j,item)
        for col in range(self.ncol):
            item=self.item(0,col)
            font=item.font()
            font.setBold(True)
            item.setFont(font)
            item.setBackground(QColor(255,255,255))

    def freeze_cursor(self):
        for metric in self.redords.keys():
            metric_record=self.redords[metric]
            if len(metric_record["values"])>= self.max_records_num:
                metric_record["values"].popleft()
            metric_record["values"].append(metric_record["cur_value"])
        for ncol,metric in enumerate(self.metrics):
            metric_record=self.redords[metric]
            for row in range(0, min(self.nrow - 1, len(metric_record["values"]))):
                value = metric_record["values"][-row - 1]
                self.set_item(row + 1, ncol, value)


    def resizeEvent(self, event):
        """重写尺寸变化事件，使所有列等宽分布"""
        # 确保有列可分配
        if self.columnCount() == 0:
            super().resizeEvent(event)
            return

        # 计算可用总宽度（减去表格内边距和滚动条宽度）
        total_width = self.viewport().width()

        # 计算每列的宽度（总宽度平均分配给所有列）
        column_count = self.columnCount()
        if column_count > 0:
            column_width = total_width // column_count

            # 为每列设置相同宽度
            for col in range(column_count):
                # 设置为固定宽度模式
                self.horizontalHeader().setSectionResizeMode(
                    col, QtWidgets.QHeaderView.Fixed
                )
                # 分配宽度（最后一列处理可能的余数，确保填满）
                if col == column_count - 1:
                    self.setColumnWidth(col, total_width - (column_width * (column_count - 1))-2)
                else:
                    self.setColumnWidth(col, column_width)
            # 关键：等宽分配后，将所有列改回交互式模式，允许手动调整
            for col in range(column_count):
                self.horizontalHeader().setSectionResizeMode(
                    col, QtWidgets.QHeaderView.Interactive
                )
        # 确保有行可调整
        if self.rowCount() == 0:
            return
        # 计算每行高度（表格可视高度平均分配给所有行）
        total_height = self.viewport().height()
        row_height = total_height // self.rowCount()
        # 设置所有行高度
        for row in range(self.rowCount()):
            self.setRowHeight(row, row_height)
        super().resizeEvent(event)



