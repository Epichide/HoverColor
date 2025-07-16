import  sys,os

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QEventLoop, Qt, pyqtSlot, QPoint, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QCloseEvent, QColor, QIcon, QMouseEvent, QCursor, QPixmap
from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QApplication, QMenu, QAction, QMessageBox
#from src.color_platte import get_average_clor
from src.RGB import RGBBar
from src.Lab import LabChart
from src.Jch import JchChart
from src.hue import HueChart
from src.record import RecordForm
from src.screenshoot import Screenshoot
from src.hotkeys_utils.hotkey_wid import HotKeyWindow, HotkeyPicker

#rom src.color_picker import ScaleWindow



class App(QWidget):
    __version__="v1.2"
    __Appname__="Huepicker"

    colorChanged=pyqtSignal(QColor)
    cursor_moved =pyqtSignal(object)

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                             |Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.hotkey_funcs={}
        self.func_hotkeys={}
        self.hotkey_workeds={}
        self._initUI()
        self._initSignals()
        self.customContextMenuRequested.connect(self.rightmenu)
        self.show()
        self.shot1.show()
    def rightmenu(self):
        self.menu.popup(QCursor.pos())


    def _initUI(self):
        # square screenshot widget
        # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        # qtApp = QApplication(sys.argv)

        # qtApp.exec()
        self.shot1=Screenshoot()
        self.rgb_bar=RGBBar(self)
        self.lab_bar=LabChart(self)
        self.jch_bar=JchChart(self)
        self.hsv_bar=HueChart(self,"hsv")
        # self.lab_bar=HueChart(self,"lab")
        self.record=RecordForm(self)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.contextMenuPolicy()
        self.Hlayout=QHBoxLayout(self)
        self.bar_widgets=[self.rgb_bar,self.hsv_bar,self.lab_bar,self.jch_bar,self.record]
        self.init_menu()
        for wid in self.bar_widgets:
            self.Hlayout.addWidget(wid)
        # self.Hlayout.addWidget(self.record)
        self.update_width()
    def init_menu(self):
        self.action_keys={}
        self.widget_keys={}
        self.record_keys={}
        self.menu=QMenu(self)
        self.submenu=QMenu("Record",self.menu)
        self.submenu_palette=QMenu("ColorSpace",self.menu)
        self.register_action(self.rgb_bar,self.submenu_palette,"RGB")
        self.register_action(self.hsv_bar,self.submenu_palette, "HSV")
        self.register_action(self.jch_bar,self.submenu_palette, "JCh")
        self.register_action(self.lab_bar,self.submenu_palette, "Lab")
        self.register_record_action(self.submenu,self.hsv_bar,"HSV")
        self.register_record_action(self.submenu,self.jch_bar,"Jch")
        self.register_record_action(self.submenu,self.rgb_bar,"RGB")
        self.register_record_action(self.submenu,self.lab_bar,"Lab")
        self.menu.addMenu(self.submenu)
        self.menu.addMenu(self.submenu_palette)

        self.action_hotkey = QAction("快捷键设置", self)
        self.menu.addAction(self.action_hotkey)
        self.action_hotkey.triggered.connect(self.Hotkey_Setting)


        self.action_quit=QAction("退出",self)
        self.menu.addAction(self.action_quit)
        self.action_quit.triggered.connect(self.close)
        self.action_quit.triggered.connect(self.shot1.close)

    def register_record_action(self,submenu,wid,tex="RGB"):
        act=QAction(tex,self)
        act.setCheckable(True)
        submenu.addAction(act)
        self.record_keys[tex]=[wid,act]
        act.triggered.connect(lambda :self.connect_record(tex))
    def connect_record(self,key):
        self.record.dis_connect_wid()
        for wid,act in self.record_keys.values():
            act.setChecked(False)
        wid,act=self.record_keys[key]
        act.setChecked(True)
        self.record.connect_wid(wid,key)

    def right_menu(self):
        num=0
        for act in self.action_keys.values():
            if act.isChecked():num+=1
        return num
    def create_checkale_action(self,name,submenu=None,icon=None):
        act=QAction(name,self)
        act.setCheckable(True)
        if submenu is None:
            self.menu.addAction(act)
        else:
            submenu.addAction(act)
        return act
    def register_action(self,widget,submenu=None,key=""):

        action_i=self.create_checkale_action(key,submenu=submenu)
        action_i.setChecked(True)
        self.action_keys[key]=action_i
        self.widget_keys[action_i]=widget
        action_i.triggered.connect(lambda :self.change_picker_widget(key))
    def check_dispay_widget_num(self):
        nums=[1 if act.isChecked() else 0 for act in self.action_keys.values()]
        num=sum(nums)
        return num
    def change_picker_widget(self,key):
        print(self.check_dispay_widget_num())
        if  self.check_dispay_widget_num():
            act=self.action_keys[key]
            status=act.isChecked()
            print(status)
            #act.setChecked(~status)
            if not status:
                self.widget_keys[act].hide()
            else:
                self.widget_keys[act].show()
        else:
            self.action_keys[key].setChecked(True)
        self.update_width()
    def update_width(self):
        w=0
        for wid in self.bar_widgets:
            if wid.isVisible():
                w+=wid.width()*1.2
        self.setFixedSize(QSize(int(w),200))
    def _initSignals(self):
        self.ctrled=0
        self.shifted=0
        self.cur=None
        self.m_flag=False

        self.cursor_moved.connect(self.handleCursorMove)
        self.timer=QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.pullCursor)
        self.timer.start()
        self.press_pos=self.pos()
        self.connect_record("HSV")
        # register hotkey
        self.register_hotkey([Qt.Key_Shift,Qt.Key_QuoteLeft],
                             self.getCustomColor,"Screen Pick")
        self.register_hotkey([Qt.Key_Control,Qt.Key_QuoteLeft],
                             self.hot_key_event,"Pixel Pick")
        self.register_hotkey([Qt.Key_Control,Qt.Key_0],
                             self.shot1.reset_range,"Reset Range")
        self.register_hotkey([Qt.Key_Control,Qt.Key_1],
                             self.shot1.expand_range,"expand Range")
        self.register_hotkey([Qt.Key_Control,Qt.Key_2],
                             self.shot1.shrink_range,"Shrink Range")



    def register_hotkey(self,qtkeys,func,funcname):
        qtkeys_str=",".join([str(vk) for vk in qtkeys])
        self.func_hotkeys[funcname]=[func,qtkeys]
        if qtkeys:
            self.hotkey_funcs[qtkeys_str]=[func,funcname,qtkeys]
            self.hotkey_workeds[qtkeys_str]=False
    def unset_hotkey_funcworked(self):
        for k in self.hotkey_workeds.keys():
            self.hotkey_workeds[k]=False


    def Hotkey_Setting(self):
        loop = QEventLoop()
        hotkey_wid = HotKeyWindow()
        for funcname,(func,qtkeys) in self.func_hotkeys.items():
            hotkey_wid.register(funcname, qtkeys)

        hotkey_wid.show()
        hotkey_wid.widget_closed.connect(loop.quit)
        loop.exec()
        res,hot_keys = hotkey_wid.get_hot_keys() #  funcname: qtkeys
        # hotkey_wid.close()
        if not res:
            return
        self.hotkey_workeds={}
        self.hotkey_funcs={}
        for funcname,qtkeys in hot_keys.items():
            self.func_hotkeys[funcname][1]=qtkeys
            func=self.func_hotkeys[funcname][0]
            qtkeys_str = ",".join([str(vk) for vk in qtkeys])
            if qtkeys:
                self.hotkey_funcs[qtkeys_str] = [func, funcname, qtkeys]
                self.hotkey_workeds[qtkeys_str] = False
        return

    def getCustomColor(self):
        res = self.shot1.getCustomColor()
        if res is not None:
            (r, g, b), screenshoot = res
            for wid in self.widget_keys.values():
                wid.pick_color(r, g, b)
            self.hot_key_event("")


    ## ------- mouse move cursor
    def handleCursorMove(self,pos):
        (r,g,b),screenshoot=self.shot1.getAverageColor(pos.x(),pos.y())
        for wid  in self.widget_keys.values():
            wid.pick_color(r,g,b)

    def pullCursor(self):
        import win32api,win32con
        GLOBAL_PRESS_str=",".join([str(vk) for  vk in GLOBAL_PRESS])
        if GLOBAL_PRESS_str in self.hotkey_funcs :
            if self.hotkey_workeds[GLOBAL_PRESS_str] is False:
                self.unset_hotkey_funcworked()
                self.hotkey_workeds[GLOBAL_PRESS_str]=True
                self.hotkey_funcs[GLOBAL_PRESS_str][0]()
        else:
            self.unset_hotkey_funcworked()

        pos=QCursor.pos()
        if pos!=self.cur:
            self.cur=pos
            self.cursor_moved.emit(pos)
        (r, g, b), screenshoot = self.shot1.getAverageColor(pos.x(), pos.y())
        for wid in self.widget_keys.values():
            wid.pick_color(r, g, b)
    def hot_key_event(self,message=""):
        for wid in self.bar_widgets:
            wid.freeze_cursor()
        return message

    ##------- move whole widget
    def mouseReleaseEvent(self,event=None):
        self.m_flag=False
        self.setCursor(Qt.ArrowCursor)
    def mousePressEvent(self, event=None):
        if event.button() ==Qt.LeftButton:
            self.m_flag=True
            self.press_pos=event.pos()
            event.accept()
            self.setCursor(Qt.OpenHandCursor)
    def mouseMoveEvent(self, event=None):
        if self.m_flag and Qt.LeftButton:
            cur=event.pos()-self.press_pos
            self.move(self.mapToParent(cur))
            event.accept()
from src.hotkeys_utils.response_key import GLOBAL_PRESS, listener
if __name__ == '__main__':
    app=QApplication(sys.argv)
    listener.start()
    # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    ex=App()
    r=app.exec_()
    sys.exit(r)
    listener.join()

