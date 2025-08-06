#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/14 20:47
# @File: record.py
# @Software: PyCharm
from collections import defaultdict, deque

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import  Qt,pyqtSlot,QPoint,pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QCloseEvent, QColor, QFont, QIcon, QMouseEvent, QCursor
from PyQt5.QtWidgets import  (QWidget,QHBoxLayout,QFrame,QLabel,QTableWidget,
                              QApplication,QMenu,QAction,QMessageBox)


class RecordForm(QTableWidget):
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
        self.horizontalHeader().setFixedHeight(defaultHeight / (self.nrow + 1))
        font.setBold(True)
        self.horizontalHeader().setFont(font)
        self.horizontalHeader().setMinimumSectionSize(1)
        self.verticalHeader().setDefaultSectionSize(defaultHeight/ (self.nrow + 1))
        self.verticalHeader().setMinimumSectionSize(defaultHeight*0.2 / (self.nrow + 1))
        self.adjust_column_width()

        
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
        self.redords=defaultdict(dict)

        self.showed_wid=None
        self.max_records_num=10

        self.setMinimumSize(1,1)
        
        self.setColumnCount(self.ncol)
        self.setRowCount(self.nrow)
        self.horizontalHeader().setVisible(True)
        self.horizontalHeader().setCascadingSectionResizes(True)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setCascadingSectionResizes(True)
        # self.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        # self.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        # self.verticalScrollBar().setDisabled(True)
        self.setAutoScroll(False)
        self.setShowGrid(False)
        # self.setAttribute(Qt.AA_EnableHighDpiScaling)
        # self.verticalHeader().setDefaultSectionSize(self.defaultHeight / (self.nrow + 1))
        # heads = self.horizontalHeader()
        # heads.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

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
        self.get_suggest_size(parent)
        self.set_zoom_size(1)
    def adjust_column_width(self):
        if not self.showed_wid or self.showed_wid.colorspace!="XYZ":
            firstratio = 100 / 160
        else:
            firstratio=(150 / 160)
        self.setColumnWidth(0,(firstratio*self.width()))
        self.setColumnWidth(1,(1-firstratio)*self.width())
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

    def connect_wid(self,wid):
        colorspace=wid.colorspace
        metric=wid.metric
        self.redords[colorspace].clear()
        self.redords[colorspace]["values"]=deque()# r,g,b,metrics
        self.redords[colorspace]["cur_values"]=[]# r,g,b,metrics
        self.redords[colorspace]["colnames"]=[colorspace,metric]
        func=lambda values:self.update_value(colorspace,values)
        wid.pos_value_signal.connect(func)
        self.connected_wid.add(wid)

    def set_show_wid(self,wid):
        colorspace=wid.colorspace
        metric=wid.metric
        self.showed_wid=wid
        self.setHorizontalHeaderLabels([colorspace,metric])
        self.adjust_column_width()

        # update item value
        values=self.redords[colorspace]["values"]
        values=list(values)
        for row,values in enumerate(values[::-1],1):
            if row> self.nrow-1:break
            self.set_item(row,values)


    def set_item(self,row,values):
        if len(values) == 3:
            x, y, z = values
            deltae = 0
        else:
            x, y, z = values[:3]
            deltae = values[3]
        deltaE = round(deltae, 3)
        item = self.item(row, 1) # metric
        item.setText(str(deltaE))

        if self.showed_wid.colorspace == "XYZ":
            x, y, z = round(x, 3), round(y, 3), round(z, 3)
        else:
            x, y, z = round(x), round(y), round(z)
        item = self.item(row, 0) # value
        item.setText(",".join([str(x), str(y), str(z)]))


        cur_record_cnt = len(self.redords[self.showed_wid.colorspace]["values"])
        if row==0:
            r, g, b, gray = self.redords["RGB"]["cur_values"]
        elif row<=cur_record_cnt:
            r,g,b,gray=self.redords["RGB"]["values"][-row]
        else:
            return
        item.setBackground(QtGui.QColor(r, g, b))
        if gray>128:
            item.setForeground(QtGui.QColor(0, 0, 0))
        else:
            item.setForeground(QtGui.QColor(255,255,255))



    def update_value(self,colorspace,values):
        self.redords[colorspace]["cur_values"]=values
        if self.showed_wid and self.showed_wid.colorspace==colorspace:
            self.set_item(0,values)
            # print(self.verticalHeader().minimumSectionSize())
            # self.setRowHeight(1, 5)
            # print(self.rowHeight(1))
            # # self.verticalHeader().setDefaultSectionSize(self.defaultHeight/10.0 / (self.nrow + 1)/1.0)
            # # self.verticalHeader().setMinimumSectionSize(self.defaultHeight/10.0 / (self.nrow + 1)/1.0)
            # for i in range(0,self.nrow):
            #     self.setRowHeight(i,self.defaultHeight / (self.nrow + 1))
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
        if not self.showed_wid: return
        cur_record_cnt=len(self.redords[self.showed_wid.colorspace]["values"])
        while cur_record_cnt>=self.max_records_num:
            for record in self.redords.values():
                record["values"].popleft()
                cur_record_cnt = len(self.redords[self.showed_wid.colorspace]["values"])
        for record in self.redords.values():
            record["values"].append(record["cur_values"])
        cur_record_cnt = len(self.redords[self.showed_wid.colorspace]["values"])
        for row in range(0,min(self.nrow-1,cur_record_cnt)):
            value=self.redords[self.showed_wid.colorspace]["values"][-row-1]
            self.set_item(row+1,value)





