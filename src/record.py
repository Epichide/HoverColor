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
        self.func=None
        self.connected_wid=None
        self.setFixedSize(100,175)
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
                item=self.item(row,0)
                item.setText("")
            self.connected_wid=None
            self.func=None
        item=self.horizontalHeaderItem(0)
        item.setText("")

    def connect_wid(self,wid,head):
        self.dis_connect_wid()
        self.func=lambda x,y,z:self.update_value(x,y,z)
        wid.pos_value_signal.connect(self.func)
        self.connected_wid=wid
        item=self.horizontalHeaderItem(0)
        item.setText(head)
        print(head)
    def update_value(self,x,y,z):
        x,y,z=round(x),round(y),round(z)
        item=self.item(0,0)
        item.setText(",".join([str(x),str(y),str(z)]))
    def init_ui(self):
        item=QtWidgets.QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        self.insertColumn(0)
        self.setHorizontalHeaderItem(0,item)
        item=self.horizontalHeaderItem(0)
        item.setText("Value")
        for i in range(self.nrow):
            item=QtWidgets.QTableWidgetItem()
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            item.setText("")
            item.setBackground(QColor(220,220,220))
            self.setItem(i-1,1,item)
        item=self.item(0,0)
        font=item.font()
        font.setBold(True)
        item.setFont(font)
        item.setBackground(QColor(255,255,255))
    def freeze_cursor(self):
        for row in range(self.nrow-1,0,-1):
            item=self.item(row,0)
            itemold=self.item(row-1,0)
            item.setText(itemold.text())




