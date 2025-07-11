#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/14 20:47
# @File: record.py
# @Software: PyCharm
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import  Qt,pyqtSlot,QPoint,pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QCloseEvent,QColor,QIcon,QMouseEvent,QCursor
from PyQt5.QtWidgets import  (QWidget,QHBoxLayout,QFrame,QLabel,QTableWidget,
                              QApplication,QMenu,QAction,QMessageBox)


class RecordForm(QTableWidget):
    def __init__(self,parent=None):
        super(RecordForm,self).__init__(parent)
        self.nrow=5
        self.ncol=2
        self.func=None
        self.connected_wid=None
        self.setFixedSize(160,175)
        self.setColumnCount(0)
        self.setRowCount(5)
        self.horizontalHeader().setVisible(True)
        self.horizontalHeader().setCascadingSectionResizes(True)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setCascadingSectionResizes(False)
        self.setShowGrid(False)
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
        print(head)
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
    def init_ui(self):
        item=QtWidgets.QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        self.setColumnCount(2)
        self.setColumnWidth(0,100)
        self.setColumnWidth(1,60)
        # self.insertColumn(0)
        self.setHorizontalHeaderLabels(["Value", "deltaE"])

        for i in range(1,self.nrow+1):
            for j in range(self.ncol):
                item=QtWidgets.QTableWidgetItem()
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter)
                item.setText("")
                item.setBackground(QColor(220,220,220))
                self.setItem(i-1,j,item)
        for col in range(self.ncol):
            item=self.item(0,col)
            font=item.font()
            font.setBold(True)
            item.setFont(font)
            item.setBackground(QColor(255,255,255))
    def freeze_cursor(self):
        for row in range(self.nrow-1,0,-1):
            for col in range(self.ncol):
                item=self.item(row,col)
                itemold=self.item(row-1,col)
                item.setText(itemold.text())





