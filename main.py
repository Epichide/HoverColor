import  sys,os

import numpy as np
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QEventLoop, Qt, pyqtSlot, QPoint, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QCloseEvent, QColor, QIcon, QMouseEvent, QCursor, QPixmap
from PyQt5.QtWidgets import QCheckBox, QDialog, QGridLayout, QLabel, QSpinBox, QVBoxLayout, QWidget, QHBoxLayout, \
    QApplication, \
    QMenu, \
    QAction, \
    QMessageBox, \
    QWidgetAction
#from src.color_platte import get_average_clor
from src.RGB import RGBBar
from src.Lab import LabChart
# from src.Jch import JchChart
from src.XYZ import XYZChart
from src.color_utils.iccinspector import update_custom_icc
from src.hue import HueChart
from src.record import RecordForm
from src.screenshoot import Screenshoot
from src.hotkeys_utils.hotkey_wid import HotKeyWindow, HotkeyPicker
from src.setting import SettingDialog
from src.wid_utils.basewid_utils import DynamicGridLayout


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
    def set_font_size(self,value):
        self.record.set_font_size(value)
        # self.set_zoom_size(self.zoom_ratio)




    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                             |Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.get_suggetst_size()
        # variable:
        self.ncol_wid = 3
        self.custom_gamut={}
        self.cur_gamut=""
        self.hotkey_funcs={}
        self.func_hotkeys={}
        self.hotkey_workeds={}
        self.gamuts = ["P3-D65", "sRGB", "P3-DCI", "Rec.709", "Rec.2020", "AdobeRGB","CUSTOM"]
        # square screenshot widget
        # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        # qtApp = QApplication(sys.argv)
        window_icon = QIcon('src/icon/icon.png')  # 替换为你的图标文件路径
        self.setWindowIcon(window_icon)
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

        self.shot1=Screenshoot()

        self.rgb_bar=RGBBar(self)
        self.lab_bar=LabChart(self)
        # self.jch_bar=JchChart(self)
        self.hsv_bar=HueChart(self,"hsv")
        self.XYZ_bar=XYZChart(self,"XYZ")

        self.record=RecordForm(self)

        self.Glayout=DynamicGridLayout(self)
        self.bar_widgets=[self.rgb_bar,self.hsv_bar,
                          self.lab_bar,self.XYZ_bar]#self.jch_bar,
        self.setLayout(self.Glayout)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.contextMenuPolicy()
        self.init_menu()
        for n,wid in enumerate(self.bar_widgets):
            self.Glayout.add_component(wid)
        self.Glayout.add_record(self.record)


    def init_menu(self):
        self.action_keys={}
        self.widget_keys={}
        self.record_keys={}
        self.gamut_keys={}
        self.loss_hover_opacity=0.2
        self.menu=QMenu(self)
        self.submenu_palette=QMenu("ColorSpace",self.menu)
        self.submenu_gamut=QMenu("Gamut",self.menu)
        self.submenu_size=QMenu("Size",self.menu)
        for bar_wid in self.bar_widgets:
            if bar_wid.__class__.__name__=="RecordForm": continue
            self.register_action(bar_wid,self.submenu_palette,bar_wid.colorspace)
            self.record.connect_wid(bar_wid)

        for gamut in self.gamuts:
            self.register_gamut_action(self.submenu_gamut,gamut)
        self.menu.addMenu(self.submenu_palette)
        self.menu.addMenu(self.submenu_gamut)
        self.menu.addMenu(self.submenu_size)

        self.zoom_box,self.font_box,self.lock_box=self.register_scale_action(self.submenu_size)
        self.font_box.valueChanged.connect(lambda value: self.set_font_size(value))
        self.zoom_box.valueChanged.connect(lambda value:self.set_zoom_size(value/100))
        self.lock_box.valueChanged.connect(lambda value: setattr(self, 'loss_hover_opacity', value/100))
        self.action_setting = QAction("设置", self)
        self.menu.addAction(self.action_setting)
        self.action_setting.triggered.connect(self.set_Setting)


        self.action_quit=QAction("退出",self)
        self.menu.addAction(self.action_quit)
        self.action_quit.triggered.connect(self.close)
        self.action_quit.triggered.connect(self.shot1.close)

        self.action_quit.triggered.connect(self.log_profile)

    def update_width(self):

        self.setFixedSize(self.Glayout.update_layout())
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
        self.record.set_show_metrics(["RGB","XYZ","Lab"])
        self.update_width()
        self.set_gamut(gamut="P3-D65")
        self.inhotkey=False
        # register hotkey
        self.register_hotkey([Qt.Key_Alt,Qt.Key_QuoteLeft],
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
        self.cur_gamut=gamut
        for wid in self.widget_keys.values():
            if hasattr(wid,"set_gamut"):
                wid.set_gamut(gamut)
    def set_enable_gamut(self,gamut="P3-D65",enabled=True):
        act = self.gamut_keys[gamut]
        if not enabled:
            act.setChecked(False)

        act.setEnabled(enabled)

    #####--------- RECORD----------------




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
        # action_i.triggered.connect(lambda :self.change_picker_widget(key))
    def create_spin_action(self,name,vmin,vmax,step=1,submenu=None):
        act = QWidgetAction(self)
        act.setText(name)
        qwid = QWidget(self)
        hbox = QHBoxLayout(qwid)
        qlabel=QLabel(self)
        qlabel.setText(name)
        # 添加伸缩项，将SpinBox推到右侧
        # hbox.addStretch(5)  # 这会占据左侧所有可用空间，将SpinBox挤到右边
        # 清除布局边距
        hbox.setContentsMargins(0, 0, 0, 0)
        qwid.setContentsMargins(0, 0, 0, 0)

        # 将SpinBox添加到布局
        spin_box = QSpinBox(qwid)
        spin_box.setMinimum(vmin)
        spin_box.setMaximum(vmax)
        spin_box.setSingleStep(step)
        spin_box.setFixedWidth(70)
        hbox.addWidget(qlabel)
        hbox.addWidget(spin_box)
        # hbox.addStretch(5)
        act.setDefaultWidget(qwid)
        if submenu is None:
            self.menu.addAction(act)
        else:
            submenu.addAction(act)
        return spin_box
    def register_scale_action(self,submenu=None):
        zoom_box=self.create_spin_action("zoom",vmin=25,vmax=225,step=10,submenu=submenu)
        font_box=self.create_spin_action("font",vmin=2,vmax=70,step=1,submenu=submenu)
        lock_btn=self.create_spin_action("lock",vmin=0,vmax=100,step=1,submenu=submenu)

        return zoom_box,font_box,lock_btn


    def check_dispay_widget_num(self):
        nums=[1 if act.isChecked() else 0 for act in self.action_keys.values()]
        num=sum(nums)
        return num
    def change_picker_widget(self,key):
        print("showed colorspace widget num",self.check_dispay_widget_num())
        # if  self.check_dispay_widget_num():
        act=self.action_keys[key]
        status=act.isChecked()
        print(key,"shown",status)
        #act.setChecked(~status)
        if not status:
            self.widget_keys[act].hide()
        else:
            self.widget_keys[act].show()

        # self.record.show()
        self.update_width()
    #####--------- PROFILE----------------
    def log_profile(self):
        self.profile={"colorspace":{},
                      "hotkeys":{},
                      "gamut":"",
                      "zoom":100,
                      "metrics":["RGB"],
                      "custom_gamut":{}}
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

        # save profile as json
        self.profile["zoom"]=self.zoom_ratio*100
        self.profile["fontsize"]=self.record.font_size1
        # save metrics
        self.profile["metrics"]=self.record.metrics
        #save custom gamut
        if self.custom_gamut :
            for k,v in self.custom_gamut.items():
                if isinstance(v,np.ndarray):
                    self.custom_gamut[k]=v.tolist()
        self.profile["custom_gamut"]=self.custom_gamut
        # save opacity
        self.profile["loss_hover_opacity"]=self.loss_hover_opacity
        import json
        fileName= "src/resource/profile/profile"
        if not os.path.exists("src/resource/profile"):
            os.makedirs("src/resource/profile")
        with open(fileName, 'w', encoding='utf-8') as file:
            json.dump(self.profile, file, ensure_ascii=False, indent=4)

    def load_profile(self):
        import json
        fileName= "src/resource/profile/profile"
        self.zoom_box.setValue(100)
        self.font_box.setValue(8)
        self.lock_box.setValue(int(self.loss_hover_opacity*100))
        if not os.path.exists(fileName):return


        with open(fileName, 'r', encoding='utf-8') as file:
            self.profile=json.load(file)
        # load custom gamut
        self.custom_gamut=self.profile.get("custom_gamut",{})
        if self.custom_gamut :
            for k,v in self.custom_gamut.items():
                if isinstance(v,list):
                    self.custom_gamut[k]=np.array(v)
        update_custom_icc(self.custom_gamut,skip_lab_proj=True)

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
        #load metrics
        metrics=self.profile["metrics"]
        self.record.set_show_metrics(metrics)
        self.update_width()
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
        fontsize=self.profile["fontsize"]
        self.font_box.setValue(fontsize)
        self.loss_hover_opacity=self.profile.get("loss_hover_opacity",0.2)
        self.lock_box.setValue(int(self.loss_hover_opacity*100))


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

    def set_Setting(self):
        self.inhotkey=True
        loop = QEventLoop()

        setting_diag=SettingDialog(self)
        setting_diag.ColorSapce_Setting(self.gamuts,self.custom_gamut,self.cur_gamut)
        setting_diag.Record_Setting(self.record)
        setting_diag.Hotkey_Setting(self.func_hotkeys)
        res=setting_diag.exec_()

        if res==QDialog.Accepted:
            self.record.set_show_metrics(setting_diag.metrics)
            self.update_width()
            hot_keys=setting_diag.hot_keys
            gamutinfo=setting_diag.seleted_gamut_info
            custom_gamut=setting_diag.custom_gamut
            if (custom_gamut and
                    custom_gamut["icc_file"]!=self.custom_gamut.get("icc_file",None)):# load new icc
                update_custom_icc(self.custom_gamut)
                icc_file = custom_gamut.get("icc_file", None)

                # copy to resource
                def _get_file(relative_path):
                    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))

                icc_file_copy = _get_file("src/resource/profile/custom_icc.icc")
                if icc_file is not None and os.path.exists(icc_file):
                    import shutil
                    shutil.copyfile(icc_file, icc_file_copy)
                else:
                    icc_file = None
                custom_gamut["icc_file"] = icc_file_copy
                self.set_enable_gamut("CUSTOM",True)
            elif custom_gamut:
                self.set_enable_gamut("CUSTOM", True)
            else:
                self.set_enable_gamut("CUSTOM",False)

            self.custom_gamut=custom_gamut if custom_gamut else None
            print("yes")
            if gamutinfo is not None:
                if gamutinfo["Gamut Type"]=="icc":
                    self.set_gamut("CUSTOM")
                else:
                    self.set_gamut(gamutinfo["Gamut"])

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
        self.record.freeze_cursor()
        return message

    ## ------- mouse move cursor
    def handleCursorMove(self,pos):
        (r,g,b),screenshoot=self.shot1.getAverageColor(pos.x(),pos.y())
        for wid  in self.widget_keys.values():
            wid.pick_color(r,g,b)

    def pullCursor(self): # timer timeout
        import win32api,win32con
        if not self.inhotkey:# 正在设置热键时不响应热键

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


    def enterEvent(self, event):
        # 鼠标进入时完全不透明
        self.setWindowOpacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        # 鼠标离开时恢复半透明
        self.setWindowOpacity(self.loss_hover_opacity)
        super().leaveEvent(event)


from src.hotkeys_utils.response_key import GLOBAL_PRESS, listener
if __name__ == '__main__':
    app=QApplication(sys.argv)
    listener.start()
    # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    ex=App()
    r=app.exec_()
    sys.exit(r)
    listener.join()

