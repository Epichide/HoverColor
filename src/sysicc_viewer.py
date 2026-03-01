#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ICC配置查看器组件
用于在HoverColor应用中查看Windows系统的ICC配置信息
"""
from PyQt5.QtWidgets import QApplication
import sys
import os
import ctypes
import ctypes.wintypes
from pathlib import Path
from typing import Optional, Dict

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
                             QFrame, QScrollArea, QGroupBox, QGridLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QMainWindow, QTabWidget, 
                             QApplication)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

# 导入工具函数
from .utils.file_utils import _get_file

# 导入ICC分析工具
from .color_utils import windows_usr_sys_icc_reg as icc_utils
from .color_utils.monitor_config_qt import ConfigTableWidget

# 导入GamutsViewer组件
from .wid_utils.gamutsviewer_wid import GamutsViewer
from .wid_utils.basewid_utils import ScrollSubTab

# Win32 API 类型定义和函数声明
user32 = ctypes.WinDLL("user32", use_last_error=True)
HWND = ctypes.wintypes.HWND
HMONITOR = ctypes.wintypes.HANDLE
DWORD = icc_utils.DWORD
RECT = icc_utils.RECT

user32.MonitorFromWindow.restype = HMONITOR
user32.MonitorFromWindow.argtypes = [HWND, DWORD]
user32.GetMonitorInfoW.restype = ctypes.wintypes.BOOL
user32.GetMonitorInfoW.argtypes = [HMONITOR, ctypes.POINTER(icc_utils.MONITORINFOEX)]

# 常量
MONITOR_DEFAULTTONEAREST = 2




class ICCViewerWidget(QMainWindow):
    """
    ICC配置查看器组件
    显示Windows系统的ICC配置信息
    使用QTabWidget管理多个标签页，MonitorConfigWindow作为其中一个标签页
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 修改窗口属性
        self.setWindowTitle("ICC配置查看器")
        self.setMinimumSize(300, 400)
        # 设置初始窗口大小（更适合的尺寸）
        self.setGeometry(100, 100, 600, 500)
        
        # 加载外部CSS样式
        style_file = _get_file("resource/css/sysicc_viewer.css")
        self.load_style_from_file(style_file)
    
        self.gamut_iccs = []
        self.cur_gamut_icc = None
        self.gamuts_viewer = None
        self.gamuts_tab_index = -1
        self.current_monitor_handle = None
        # 初始化UI
        self.init_ui()
    
    def get_window_hwnd(self) -> Optional[int]:
        """
        获取当前PyQt窗口的句柄
        :return: 窗口句柄，如果失败返回None
        """
        return int(self.winId())
    
    def get_window_monitor(self) -> Optional[HMONITOR]:
        """
        获取当前窗口所在的显示器
        :return: 显示器句柄，如果失败返回None
        """
        hwnd = self.get_window_hwnd()
        if not hwnd:
            return None
        
        monitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
        return monitor if monitor else None
    
    def get_display_name(self, monitor: HMONITOR) -> Optional[str]:
        """
        根据显示器句柄获取显示器名称
        :param monitor: 显示器句柄
        :return: 显示器名称，如果失败返回None
        """
        monitor_info = icc_utils.MONITORINFOEX()
        monitor_info.cbSize = ctypes.sizeof(monitor_info)
        
        if user32.GetMonitorInfoW(monitor, ctypes.byref(monitor_info)):
            return monitor_info.szDevice.rstrip('\x00')
        return None
    
    def get_monitor_instance_id(self, display_name: str) -> Optional[str]:
        """
        根据显示器名称查找对应的实例ID
        :param display_name: 显示器名称（如\\.\DISPLAY1）
        :return: 显示器实例ID（如0002），如果失败返回None
        """
        # 方法与之前的find_monitor_instance_id相同
        i = 0
        while True:
            dd = icc_utils.DISPLAY_DEVICE()
            dd.cb = ctypes.sizeof(dd)
            
            # 枚举显示器设备
            success = user32.EnumDisplayDevicesW(display_name, i, ctypes.byref(dd), 0)
            if not success:
                break
            
            # 提取实例ID
            instance_id = icc_utils.extract_instance_id_from_device_key(dd.DeviceKey)
            if instance_id:
                return instance_id
            
            i += 1
        
        # 如果直接查找失败，尝试遍历所有显示器实例
        try:
            monitor_guid = icc_utils.MONITOR_CLASS_GUID
            class_path = f"SYSTEM\\CurrentControlSet\\Control\\Class\\{monitor_guid}"
            
            with icc_utils.winreg.OpenKey(icc_utils.HKLM, class_path) as class_key:
                for i in range(icc_utils.winreg.QueryInfoKey(class_key)[0]):
                    subkey_name = icc_utils.winreg.EnumKey(class_key, i)
                    if subkey_name.isdigit() and len(subkey_name) == 4:
                        return subkey_name
        except:
            pass
        
        return None
    
    def moveEvent(self, event):
        """
        窗口移动事件，当窗口移动到新的显示器时更新显示器信息
        """
        super().moveEvent(event)
        self.handle_window_move()
    
    def resizeEvent(self, event):
        """
        窗口调整大小事件，当窗口大小改变时可能需要更新显示器信息
        """
        super().resizeEvent(event)
        self.handle_window_move()
    
    def handle_window_move(self):
        """
        处理窗口移动事件，检查是否移动到了新的显示器
        """
        current_monitor = self.get_window_monitor()
        if current_monitor and current_monitor != self.current_monitor_handle:
            # 窗口移动到了新的显示器
            self.current_monitor_handle = current_monitor
            # 延迟更新显示器信息（确保窗口已经稳定）
            QTimer.singleShot(300, self.update_monitor_info)
    
    def init_ui(self):
        """
        初始化用户界面，创建QTabWidget并添加显示器配置信息作为标签页
        """
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建顶部布局，用于放置刷新按钮
        top_layout = QHBoxLayout()
        top_layout.addStretch()  # 添加伸缩项，将按钮推到右侧
        
        # 创建刷新按钮
        self.refresh_button = QPushButton("🔄️ 刷新")
        self.refresh_button.setFont(QFont("Arial", 10))
        self.refresh_button.clicked.connect(self.update_monitor_info)
        top_layout.addWidget(self.refresh_button)
        
        # 将顶部布局添加到主布局
        main_layout.addLayout(top_layout)
        
        # 创建QTabWidget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建一个新的widget来包含显示器配置信息
        self.monitor_config_widget = QWidget()
        self.monitor_config_layout = QVBoxLayout(self.monitor_config_widget)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.monitor_config_layout.addWidget(scroll_area)
        
        # 创建滚动区域内的内容组件
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(15)
        scroll_area.setWidget(self.scroll_content)
        
        # 创建各个信息组
        self.create_info_groups()
        
        # 将widget添加为标签页
        self.tab_widget.addTab(self.monitor_config_widget, "显示器配置")
        
        self.gamuts_scroll_tab = ScrollSubTab()
        # self, gamuts, custom_gamut, cur_gamut
        
        # 可以在这里添加更多标签页
        # self.tab_widget.addTab(AnotherWidget(), "其他功能")
        
        # 设置窗口标题
        self.setWindowTitle("ICC配置查看器")
        
        # 手动触发显示器信息更新
        self.update_monitor_info()

    
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
            print(f"加载样式文件出错：{e}")
    
    def create_info_groups(self):
        """
        创建显示器信息的各个分组
        """
        # 显示器基本信息组
        self.monitor_info_group = QGroupBox("显示器基本信息")
        self.monitor_info_layout = QGridLayout()
        self.monitor_info_group.setLayout(self.monitor_info_layout)
        self.scroll_layout.addWidget(self.monitor_info_group)
        
        # 最终生效配置组
        self.final_config_group = QGroupBox("最终生效配置")
        self.final_config_layout = QVBoxLayout()
        self.final_config_group.setLayout(self.final_config_layout)
        self.scroll_layout.addWidget(self.final_config_group)
        
        # 用户级配置组
        self.user_config_group = QGroupBox("显示器用户级配置")
        self.user_config_layout = QVBoxLayout()
        self.user_config_group.setLayout(self.user_config_layout)
        self.scroll_layout.addWidget(self.user_config_group)
        
        # 系统级配置组
        self.system_config_group = QGroupBox("显示器系统级配置")
        self.system_config_layout = QVBoxLayout()
        self.system_config_group.setLayout(self.system_config_layout)
        self.scroll_layout.addWidget(self.system_config_group)
        
        # Windows 用户级配置情况组
        self.windows_user_config_group = QGroupBox("Windows 用户级配置情况")
        self.windows_user_config_layout = QVBoxLayout()
        self.windows_user_config_group.setLayout(self.windows_user_config_layout)
        self.scroll_layout.addWidget(self.windows_user_config_group)
        
        # Windows 系统级配置情况组
        self.windows_system_config_group = QGroupBox("Windows 系统级配置情况")
        self.windows_system_config_layout = QVBoxLayout()
        self.windows_system_config_group.setLayout(self.windows_system_config_layout)
        self.scroll_layout.addWidget(self.windows_system_config_group)
    
    def update_monitor_info(self):
        """
        更新显示器配置信息
        """
        try:
            # 使用MonitorConfigWindow获取显示器信息
            monitors = icc_utils.analyze()
            
            if not monitors:
                self.show_error("无法获取显示器配置信息")
                return
            
            # 获取当前窗口所在的显示器
            monitor = self.get_window_monitor()
            if not monitor:
                self.show_error("无法确定窗口所在的显示器")
                return
            
            # 获取显示器名称
            display_name = self.get_display_name(monitor)
            if not display_name:
                self.show_error("无法获取显示器名称")
                return
            
            # 获取显示器实例ID
            instance_id = self.get_monitor_instance_id(display_name)
            if not instance_id:
                self.show_error("无法确定显示器实例ID")
                return
            
            # 查找当前实例ID对应的显示器信息
            current_monitor = None
            for monitor_info in monitors:
                if monitor_info.get("instance_id") == instance_id:
                    current_monitor = monitor_info
                    break
            
            # 如果没有找到，使用第一个显示器的信息
            if not current_monitor and monitors:
                current_monitor = monitors[0]
            
            if not current_monitor:
                self.show_error("无法获取当前显示器配置信息")
                return
            
            # 更新当前显示器句柄
            self.current_monitor_handle = monitor
            
            # reset gamuts
            self.gamut_iccs = []
            self.cur_gamut_icc = None
            
            # 更新显示器基本信息
            self.update_monitor_basic_info(current_monitor)
            
            # 更新最终生效配置
            self.update_final_config(current_monitor)
            
            # 更新用户级配置
            self.update_user_config(current_monitor)
            
            # 更新系统级配置
            self.update_system_config(current_monitor)
            
            # 更新Windows用户级配置情况
            self.update_windows_user_config(current_monitor)
            
            # 更新Windows系统级配置情况
            self.update_windows_system_config(current_monitor)
            
            # 添加GamutsViewer作为新的标签页
            if "CUSTOM" not in self.gamut_iccs:
                self.gamut_iccs.append("CUSTOM")
            
            # 更新或创建GamutsViewer
            if self.gamuts_viewer:
                # 移除旧的GamutsViewer
                self.gamuts_scroll_tab.layout().removeWidget(self.gamuts_viewer)
                self.gamuts_viewer.deleteLater()
                self.gamuts_viewer = None
            
            # 创建新的GamutsViewer
            self.gamuts_viewer = GamutsViewer(self, self.gamut_iccs, self.cur_gamut_icc)
            self.gamuts_scroll_tab.layout().addWidget(self.gamuts_viewer)
            
            # 如果标签页还没有添加，则添加它
            if self.gamuts_tab_index == -1:
                self.gamuts_tab_index = self.tab_widget.addTab(self.gamuts_scroll_tab, "色域查看器")
            
        except Exception as e:
            self.show_error(f"加载配置失败: {str(e)}")
    
    def update_monitor_basic_info(self, current_monitor):
        """
        更新显示器基本信息
        """
        # 清空现有内容
        self.clear_layout(self.monitor_info_layout)
        
        try:
            # 提取信息
            friendly_name = current_monitor.get("friendly_name", "未知")
            rendering_device = current_monitor.get("rendering_device", "未知")
            hardware_id = current_monitor.get("device_id", "未知")
            instance_id = current_monitor.get("instance_id", "未知")
            
            # 获取EDID信息
            edid_info = {
                "manufacturer": "未知",
                "product_code": "未知",
                "serial_number": "未知"
            }
            
            if "edid" in current_monitor and current_monitor["edid"]:
                edid_data = current_monitor["edid"]
                edid_info["manufacturer"] = edid_data["manufacturer"]
                edid_info["product_code"] = f"{edid_data['product_code']:04X}"
                edid_info["serial_number"] = f"{edid_data['serial']:08X}"
            
            # 获取ACM状态
            acm_status = "未知"
            if "acm_state" in current_monitor:
                if current_monitor["acm_state"] == 1:
                    acm_status = "✅ 开启"
                elif current_monitor["acm_state"] == 0:
                    acm_status = "❌ 关闭"
                else:
                    acm_status = "未配置"
            
        except Exception as e:
            print(f"获取显示器信息时出错: {e}")
            self.show_error(f"无法获取显示器信息")
            return
        
        # 创建表格数据
        rows = [
            ["显示器名称", friendly_name],
            ["渲染设备", rendering_device],
            ["实例ID", instance_id],
            ["硬件ID", hardware_id],
            ["EDID厂商", edid_info['manufacturer']],
            ["产品代码", edid_info['product_code']],
            ["序列号", edid_info['serial_number']],
            ["自动颜色管理(ACM)", acm_status]
        ]
        
        # 使用自定义表格类
        table_widget = ConfigTableWidget()
        table_widget.set_table_data(rows)
        table_widget.adjust_table_size()
        
        # 添加到布局
        self.monitor_info_layout.addWidget(table_widget, 0, 0, 1, 2)
    
    def update_user_config(self, current_monitor):
        """
        更新用户级配置
        """
        # 清空现有内容
        self.clear_layout(self.user_config_layout)
        
        # 获取icc_config中的用户配置
        icc_config = current_monitor.get("icc_config", {})
        user_config = icc_config.get("user", {})
        
        # 设置表格内容
        rows = []
        
        # 添加启用状态
        use_user = user_config.get("use_user_profile", False)
        status_text = "✅ 启用" if use_user else "❌ 禁用"
        rows.append(["启用用户配置", status_text])
        
        # 添加用户SDR配置
        sdr_content = ""
        if user_config.get("sdr_icc"):
            for i, (path, source) in enumerate(user_config["sdr_icc"], 1):
                filename = Path(path).name
                if path not in self.gamut_iccs:
                    self.gamut_iccs.append(path)
                is_default = " (默认值)" if path == user_config.get("sdr_default") else ""
                sdr_content += f"{i}. {filename}{is_default}\n"
        else:
            sdr_content = "无"
        rows.append(["用户SDR ICC配置", sdr_content.strip()])
        
        # 添加用户HDR配置
        hdr_content = ""
        if user_config.get("hdr_icc"):
            for i, (path, source) in enumerate(user_config["hdr_icc"], 1):
                filename = Path(path).name
                is_default = " (默认值)" if path == user_config.get("hdr_default") else ""
                hdr_content += f"{i}. {filename}{is_default}\n"
        else:
            hdr_content = "无"
        rows.append(["用户HDR ICC配置", hdr_content.strip()])
        
        # 使用自定义表格类
        table_widget = ConfigTableWidget()
        table_widget.set_table_data(rows)
        table_widget.adjust_table_size()
        
        # 添加到布局
        self.user_config_layout.addWidget(table_widget)
    
    def update_system_config(self, current_monitor):
        """
        更新系统级配置
        """
        # 清空现有内容
        self.clear_layout(self.system_config_layout)
        
        # 获取icc_config中的系统配置
        icc_config = current_monitor.get("icc_config", {})
        system_config = icc_config.get("system", {})
        
        # 设置表格内容
        rows = []
        
        # 添加系统SDR配置
        sdr_content = ""
        if system_config.get("sdr_icc"):
            for i, (path, source) in enumerate(system_config["sdr_icc"], 1):
                filename = Path(path).name
                if path and path not in self.gamut_iccs:
                    self.gamut_iccs.append(path)
                is_default = " (默认值)" if path == system_config.get("sdr_default") else ""
                sdr_content += f"{i}. {filename}{is_default}\n"
        else:
            sdr_content = "无"
        rows.append(["系统SDR ICC配置", sdr_content.strip()])
        
        # 添加系统HDR配置
        hdr_content = ""
        if system_config.get("hdr_icc"):
            for i, (path, source) in enumerate(system_config["hdr_icc"], 1):
                filename = Path(path).name
                is_default = " (默认值)" if path == system_config.get("hdr_default") else ""
                hdr_content += f"{i}. {filename}{is_default}\n"
        else:
            hdr_content = "无"
        rows.append(["系统HDR ICC配置", hdr_content.strip()])
        
        # 使用自定义表格类
        table_widget = ConfigTableWidget()
        table_widget.set_table_data(rows)
        table_widget.adjust_table_size()
        
        # 添加到布局
        self.system_config_layout.addWidget(table_widget)
    
    def update_final_config(self, current_monitor):
        """
        更新最终生效配置
        """
        # 清空现有内容
        self.clear_layout(self.final_config_layout)
        
        # 设置表格内容
        rows = []
        
        # 添加当前生效的ICC配置（GDI）
        if current_monitor.get("current_icc_gdi"):
            icc_abs_path=current_monitor["current_icc_gdi"]
            current_icc_filename = Path(icc_abs_path).name
            if current_icc_filename and current_icc_filename not in self.gamut_iccs:
                self.gamut_iccs.append(icc_abs_path)
                self.cur_gamut_icc = icc_abs_path
            rows.append(["当前生效的ICC（GDI）", current_icc_filename])
        else:
            rows.append(["当前生效的ICC（GDI）", "无"])
        
        # 添加ACM状态
        acm_state = current_monitor.get("acm_state")
        acm_status = "✅ 开启" if acm_state == 1 else "❌ 关闭" if acm_state == 0 else "未配置"
        rows.append(["自动颜色管理(ACM)", acm_status])
        
        # 使用自定义表格类
        table_widget = ConfigTableWidget()
        table_widget.set_table_data(rows)
        table_widget.adjust_table_size()
        
        # 添加到布局
        self.final_config_layout.addWidget(table_widget)
    
    def update_windows_user_config(self, current_monitor):
        """
        更新Windows用户级配置情况
        """
        # 清空现有内容
        self.clear_layout(self.windows_user_config_layout)
        
        # 使用current_monitor中的windows_profiles信息
        windows_profiles = current_monitor.get("windows_profiles", {})
        user_win_profiles = windows_profiles.get("user", {})
        
        # 设置表格内容
        rows = []
        if user_win_profiles:
            for k, v in user_win_profiles.items():
                rows.append([f"{k}", Path(v).name if v else "无"])
        else:
            rows.append(["Windows用户级默认配置", "无"])
        
        # 使用自定义表格类
        table_widget = ConfigTableWidget()
        table_widget.set_table_data(rows)
        table_widget.adjust_table_size()
        
        # 添加到布局
        self.windows_user_config_layout.addWidget(table_widget)
    
    def update_windows_system_config(self, current_monitor):
        """
        更新Windows系统级配置情况
        """
        # 清空现有内容
        self.clear_layout(self.windows_system_config_layout)
        
        # 使用current_monitor中的windows_profiles信息
        windows_profiles = current_monitor.get("windows_profiles", {})
        sys_win_profiles = windows_profiles.get("system", {})
        
        # 设置表格内容
        rows = []
        if sys_win_profiles:
            for k, v in sys_win_profiles.items():
                rows.append([f"{k}", Path(v).name if v else "无"])
        else:
            rows.append(["Windows系统级默认配置", "无"])
        
        # 使用自定义表格类
        table_widget = ConfigTableWidget()
        table_widget.set_table_data(rows)
        table_widget.adjust_table_size()
        
        # 添加到布局
        self.windows_system_config_layout.addWidget(table_widget)
    
    def clear_layout(self, layout):
        """
        清空布局内容
        """
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def show_error(self, message):
        """
        显示错误信息
        """
        error_label = QLabel(f"❌ {message}")
        error_label.setStyleSheet("color: red; font-weight: bold;")
        error_label.setAlignment(Qt.AlignCenter)
        
        # 清空所有布局
        self.clear_layout(self.monitor_info_layout)
        self.clear_layout(self.user_config_layout)
        self.clear_layout(self.system_config_layout)
        self.clear_layout(self.final_config_layout)
        self.clear_layout(self.windows_user_config_layout)
        self.clear_layout(self.windows_system_config_layout)
        
        # 在基本信息组显示错误
        self.monitor_info_layout.addWidget(error_label, 0, 0, 1, 2)
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 调用父类的closeEvent
        super().closeEvent(event)
        # 确保窗口被正确销毁
        self.deleteLater()
    



if __name__ == '__main__':
    """
    测试代码
    """
    
    
    app = QApplication(sys.argv)
    viewer = ICCViewerWidget()
    viewer.show()
    sys.exit(app.exec_())
