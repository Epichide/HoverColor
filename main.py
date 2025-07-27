import  sys,os

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QEventLoop, Qt, pyqtSlot, QPoint, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QCloseEvent, QColor, QIcon, QMouseEvent, QCursor, QPixmap
from PyQt5.QtWidgets import QCheckBox, QLabel, QSpinBox, QVBoxLayout, QWidget, QHBoxLayout, QApplication, QMenu, \
    QAction, \
    QMessageBox, \
    QWidgetAction
#from src.color_platte import get_average_clor
from src.RGB import RGBBar
from src.Lab import LabChart
# from src.Jch import JchChart
from src.XYZ import XYZChart
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
    def get_suggetst_size(self):
        screenshoot = QApplication.primaryScreen()
        geometry=screenshoot.geometry()
        screen_width=geometry.width()
        screen_height=geometry.height()
        self.single_wid_height=screen_height*0.15
        self.single_wid_width=screen_height*0.15
        print(self.single_wid_height,self.single_wid_width)
        return self.single_wid_width,self.single_wid_height
    def set_zoom_size(self,ratio):
        self.zoom_ratio=ratio
        for wid in self.bar_widgets:
            if hasattr(wid,"set_zoom_size"):
                wid.set_zoom_size(ratio)
        self.update_width()


    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                             |Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.get_suggetst_size()
        # variable:
        self.hotkey_funcs={}
        self.func_hotkeys={}
        self.hotkey_workeds={}

        self._initUI()
        self._initSignals()
        self.customContextMenuRequested.connect(self.rightmenu)
        self.load_profile()

        self.show()
        self.shot1.show()
    def rightmenu(self):
        self.menu.popup(QCursor.pos())

    def right_menu(self):
        num=0
        for act in self.action_keys.values():
            if act.isChecked():num+=1
        return num
    def _initUI(self):
        # square screenshot widget
        # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        # qtApp = QApplication(sys.argv)
        window_icon = QIcon('src/icon/icon.png')  # 替换为你的图标文件路径
        self.setWindowIcon(window_icon)

        # qtApp.exec()
        self.shot1=Screenshoot()
        self.rgb_bar=RGBBar(self)
        self.lab_bar=LabChart(self)
        # self.jch_bar=JchChart(self)
        self.hsv_bar=HueChart(self,"hsv")
        self.XYZ_bar=XYZChart(self,"XYZ")
        # self.lab_bar=HueChart(self,"lab")
        self.record=RecordForm(self)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.contextMenuPolicy()
        self.Hlayout=QHBoxLayout(self)
        self.bar_widgets=[self.rgb_bar,self.hsv_bar,
                          self.lab_bar,self.XYZ_bar,self.record]#self.jch_bar,
        self.init_menu()
        for wid in self.bar_widgets:
            self.Hlayout.addWidget(wid)
        # self.Hlayout.addWidget(self.record)

    def init_menu(self):
        self.action_keys={}
        self.widget_keys={}
        self.record_keys={}
        self.gamut_keys={}
        self.menu=QMenu(self)
        self.submenu_record=QMenu("Record",self.menu)
        self.submenu_palette=QMenu("ColorSpace",self.menu)
        self.submenu_gamut=QMenu("Gamut",self.menu)
        self.register_action(self.rgb_bar,self.submenu_palette,"RGB")
        self.register_action(self.hsv_bar,self.submenu_palette, "HSV")
        # self.register_action(self.jch_bar,self.submenu_palette, "JCh")
        self.register_action(self.lab_bar,self.submenu_palette, "Lab")
        self.register_action(self.XYZ_bar,self.submenu_palette, "XYZ")
        gamuts=["P3-D65","sRGB","P3-DCI","Rec.709","Rec.2020","AdobeRGB"]
        for gamut in gamuts:
            self.register_gamut_action(self.submenu_gamut,gamut)
        self.menu.addMenu(self.submenu_record)
        self.menu.addMenu(self.submenu_palette)
        self.menu.addMenu(self.submenu_gamut)
        self.zoom_box=self.register_zoom_action()
        self.zoom_box.valueChanged.connect(lambda value:self.set_zoom_size(value/100))
        self.action_hotkey = QAction("快捷键设置", self)
        self.menu.addAction(self.action_hotkey)
        self.action_hotkey.triggered.connect(self.Hotkey_Setting)


        self.action_quit=QAction("退出",self)
        self.menu.addAction(self.action_quit)
        self.action_quit.triggered.connect(self.close)
        self.action_quit.triggered.connect(self.shot1.close)

        self.action_quit.triggered.connect(self.log_profile)

    def update_width(self):
        w=0
        for wid in self.bar_widgets:
            if wid.isVisible():
                w+=wid.width()*1.2
        self.setFixedSize(QSize(int(w),int(self.single_wid_height*self.zoom_ratio)+1))
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
        self.connect_show_record("HSV")
        self.set_gamut(gamut="P3-D65")
        self.inhotkey=False
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

    #####--------- GAMUT----------------
    def register_gamut_action(self,submenu,gamut="P3-D65"):
        act = QAction(gamut, self)
        act.setCheckable(True)
        submenu.addAction(act)
        self.gamut_keys[gamut] = act
        act.triggered.connect(lambda: self.set_gamut(gamut))

    def set_gamut(self,gamut="P3-D65"):
        for tgamut, act in self.gamut_keys.items():
            act.setChecked(False)
        act = self.gamut_keys[gamut]
        act.setChecked(True)
        for wid in self.widget_keys.values():
            if hasattr(wid,"set_gamut"):
                wid.set_gamut(gamut)

    #####--------- RECORD----------------
    def register_record_action(self,submenu,wid,tex="RGB"):
        act=QAction(tex,self)
        act.setCheckable(True)
        submenu.addAction(act)
        self.record_keys[tex]=[wid,act]
        self.record.connect_wid(wid)
        act.triggered.connect(lambda :self.connect_show_record(tex))
    def connect_show_record(self,key):
        for wid,act in self.record_keys.values():
            act.setChecked(False)
        wid,act=self.record_keys[key]
        act.setChecked(True)
        self.record.set_show_wid(wid)

    #####--------- COLORSPACE----------------
    def create_checkale_action(self,name,submenu=None,icon=None):
        act=QWidgetAction(self)
        act.setText(name)
        # act.setCheckable(True)
        submenu_palette_checkbox=QCheckBox(self.submenu_palette)
        submenu_palette_checkbox.setText(name)
        act.setDefaultWidget(submenu_palette_checkbox)
        if submenu is None:
            self.menu.addAction(act)
        else:
            submenu.addAction(act)
        return submenu_palette_checkbox
    def register_action(self,widget,submenu=None,key=""):

        action_i=self.create_checkale_action(key,submenu=submenu)
        action_i.setChecked(True)
        self.action_keys[key]=action_i
        self.widget_keys[action_i]=widget
        action_i.clicked.connect(lambda status :self.change_picker_widget(key))
        self.register_record_action(self.submenu_record, widget, key)
        # action_i.triggered.connect(lambda :self.change_picker_widget(key))

    def register_zoom_action(self,submenu=None):
        act = QWidgetAction(self)
        act.setText("zoom")

        # 创建一个容器部件来放置QSpinBox
        qwid = QWidget(self.menu)
        # 使用QHBoxLayout控制水平方向的对齐
        hbox = QHBoxLayout(qwid)

        # 添加伸缩项，将SpinBox推到右侧
        hbox.addStretch(10)  # 这会占据左侧所有可用空间，将SpinBox挤到右边

        # 配置缩放SpinBox
        zoom_box = QSpinBox(qwid)
        zoom_box.setMinimum(25)
        zoom_box.setMaximum(175)
        zoom_box.setSingleStep(10)
        zoom_box.setValue(100)
        zoom_box.setFixedWidth(70)

        # 清除布局边距
        hbox.setContentsMargins(0, 0, 0, 0)
        qwid.setContentsMargins(0, 0, 0, 0)

        # 将SpinBox添加到布局
        hbox.addWidget(zoom_box)
        hbox.addStretch(10)

        # 设置容器部件的大小策略，确保它能扩展到可用空间
        # qwid.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # 将容器部件设置为动作的默认部件
        act.setDefaultWidget(qwid)

        # 将动作添加到菜单或子菜单
        if submenu is None:
            self.menu.addAction(act)
        else:
            submenu.addAction(act)

        return zoom_box


    def check_dispay_widget_num(self):
        nums=[1 if act.isChecked() else 0 for act in self.action_keys.values()]
        num=sum(nums)
        return num
    def change_picker_widget(self,key):
        print("showed colorspace widget num",self.check_dispay_widget_num())
        if  self.check_dispay_widget_num():
            act=self.action_keys[key]
            status=act.isChecked()
            print(key,"shown",status)
            #act.setChecked(~status)
            if not status:
                self.widget_keys[act].hide()
            else:
                self.widget_keys[act].show()
        else:
            self.action_keys[key].setChecked(True)
        self.update_width()
    #####--------- PROFILE----------------
    def log_profile(self):
        self.profile={"colorspace":{},"hotkeys":{},"gamut":"","zoom":100}
        # SAVE GAMUT shown
        for gamut,act in self.gamut_keys.items():
            if act.isChecked():
                self.profile["gamut"]=gamut
                break
        # save colorspace shown
        for colorspace,act in self.action_keys.items():
            if act.isChecked():
                self.profile["colorspace"][colorspace]=True
            else:
                self.profile["colorspace"][colorspace]=False
        # save hotkeys
        for funcname,(func,qtkeys) in self.func_hotkeys.items():
            self.profile["hotkeys"][funcname]=qtkeys
        # save record wid
        self.profile["record"]=""
        for record,(wid,act) in self.record_keys.items():
            if act.isChecked():
                self.profile["record"]=record
        # save profile as json
        self.profile["zoom"]=self.zoom_ratio*100
        import json
        fileName="src/profile/profile"
        if not os.path.exists(fileName):
            os.makedirs(fileName)
        with open(fileName, 'w', encoding='utf-8') as file:
            json.dump(self.profile, file, ensure_ascii=False, indent=4)

    def load_profile(self):
        import json
        fileName="src/profile/profile"
        self.set_zoom_size(1)
        if not os.path.exists(fileName):return

        with open(fileName, 'r', encoding='utf-8') as file:
            self.profile=json.load(file)
        # load gamut
        self.set_gamut(gamut=self.profile["gamut"])
        # load colorspace
        for colorspce,checked in self.profile["colorspace"].items():
            act = self.action_keys[colorspce]
            if checked:
                act.setChecked(True)
                self.widget_keys[act].show()
            else:
                act.setChecked(False)
                self.widget_keys[act].hide()
        self.update_width()
        #load record
        record=self.profile["record"]
        self.connect_show_record(record)
        #load hotkeys
        hot_keys=self.profile["hotkeys"]
        self.hotkey_workeds = {}
        self.hotkey_funcs={}
        for funcname, qtkeys in hot_keys.items():
            self.func_hotkeys[funcname][1] = qtkeys
            func = self.func_hotkeys[funcname][0]
            qtkeys_str = ",".join([str(vk) for vk in qtkeys])
            if qtkeys:
                self.hotkey_funcs[qtkeys_str] = [func, funcname, qtkeys]
                self.hotkey_workeds[qtkeys_str] = False
        zoom=self.profile["zoom"]
        self.zoom_box.setValue(int(zoom))


    #####--------- HOTKEY----------------
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
        self.inhotkey=True
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
        self.inhotkey=False

        return

    def getCustomColor(self):
        res = self.shot1.getCustomColor()
        if res is not None:
            (r, g, b), screenshoot = res
            for wid in self.widget_keys.values():
                wid.pick_color(r, g, b)
            self.hot_key_event("")
    def hot_key_event(self,message=""):
        for wid in self.bar_widgets:
            wid.freeze_cursor()
        return message

    ## ------- mouse move cursor
    def handleCursorMove(self,pos):
        (r,g,b),screenshoot=self.shot1.getAverageColor(pos.x(),pos.y())
        for wid  in self.widget_keys.values():
            wid.pick_color(r,g,b)

    def pullCursor(self):
        import win32api,win32con
        if not self.inhotkey:

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

