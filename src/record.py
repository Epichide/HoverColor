#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/14 20:47
# @File: record.py
# @Software: PyCharm
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import  Qt,pyqtSlot,QPoint,pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QCloseEvent, QColor, QFont, QIcon, QMouseEvent, QCursor
from PyQt5.QtWidgets import  (QWidget,QHBoxLayout,QFrame,QLabel,QTableWidget,
                              QApplication,QMenu,QAction,QMessageBox)


class RecordForm(QTableWidget):
    def __init__(self,parent=None):
        super(RecordForm,self).__init__(parent)
        self.nrow=5
        self.ncol=2
        self.func=None
        self.connected_wid=None
        self.defaultHeight=175
        self.setMinimumSize(1,1)
        self.setGeometry(QtCore.QRect(0, 0, 160, self.defaultHeight))
        # self.setFixedSize(160,self.defaultHeight)
        self.setFixedWidth(160)
        self.setColumnCount(self.ncol)
        self.setRowCount(self.nrow)
        self.horizontalHeader().setVisible(True)
        self.horizontalHeader().setCascadingSectionResizes(True)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setCascadingSectionResizes(True)
        self.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        self.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        self.verticalScrollBar().setDisabled(True)
        self.setAutoScroll(False)
        self.setShowGrid(False)
        # self.setAttribute(Qt.AA_EnableHighDpiScaling)
        # self.verticalHeader().setDefaultSectionSize(self.defaultHeight / (self.nrow + 1))
        # heads = self.horizontalHeader()
        # heads.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.setColumnWidth(0,100)
        self.setColumnWidth(1,60)
        self.init_ui()
        self.setStyleSheet(
            "QTableView::item::selected"
            "{"
            "background-color: #eeeeee;"
            "selection-color :#000000;"
            "}"
            
            "QTableView"
            "{"
            "border: none"
            "}"
        )

    def dis_connect_wid(self):
        if self.connected_wid:
            self.connected_wid.pos_value_signal.disconnect(self.func)
            for row in range(self.nrow-1,0,-1):
                for col in range(self.ncol):
                    item=self.item(row,col)
                    item.setText("")
            self.connected_wid=None
            self.func=None
        item=self.horizontalHeaderItem(0)
        item.setText("")

    def connect_wid(self,wid,head):
        colorspace=wid.colorspace
        metric=wid.metric
        self.dis_connect_wid()
        self.func=lambda values:self.update_value(values)
        wid.pos_value_signal.connect(self.func)
        self.connected_wid=wid
        self.setHorizontalHeaderLabels([colorspace,metric])
        print("Record Connect : ",head)
    def update_value(self,values):
        if len(values)==3:
            x,y,z=values
            deltae=0
        else:
            x,y,z=values[:3]
            deltae=values[3]
        item=self.item(0,1)
        deltaE=round(deltae,3)
        item.setText(str(deltaE))
        x,y,z=round(x),round(y),round(z)
        item=self.item(0,0)
        item.setText(",".join([str(x),str(y),str(z)]))
        self.horizontalHeader().setFixedHeight(self.defaultHeight / (self.nrow + 1))
        self.verticalHeader().setDefaultSectionSize(self.defaultHeight / (self.nrow + 1))
        self.verticalHeader().setMinimumSectionSize(self.defaultHeight / (self.nrow + 1))
        # print(self.verticalHeader().minimumSectionSize())
        # self.setRowHeight(1, 5)
        # print(self.rowHeight(1))
        # # self.verticalHeader().setDefaultSectionSize(self.defaultHeight/10.0 / (self.nrow + 1)/1.0)
        # # self.verticalHeader().setMinimumSectionSize(self.defaultHeight/10.0 / (self.nrow + 1)/1.0)
        # for i in range(0,self.nrow):
        #     self.setRowHeight(i,self.defaultHeight / (self.nrow + 1))
    def init_ui(self):

        font=self.font()
        font.setPixelSize(self.defaultHeight/(self.nrow+1)/2)
        self.setFont(font)
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
                font=item.font()
                item.setFont(font)
                item.setBackground(QColor(220,220,220))
                self.setItem(i,j,item)
        for col in range(self.ncol):
            item=self.item(0,col)
            font=item.font()
            font.setBold(True)
            # font.setPointSize(self.defaultHeight / (self.nrow + 1)/8)
            item.setFont(font)
            item.setBackground(QColor(255,255,255))

    def freeze_cursor(self):
        for row in range(self.nrow-1,0,-1):
            for col in range(self.ncol):
                item=self.item(row,col)
                itemold=self.item(row-1,col)
                item.setText(itemold.text())





