#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyQt5 显示器配置信息窗口
================================================================================
功能：创建一个PyQt5窗口，显示该窗口所在显示器的完整配置情况
包括：显示器基本信息、用户/系统级ICC配置、最终生效配置等
================================================================================
"""

import sys
import ctypes
import ctypes.wintypes
from pathlib import Path
from typing import Optional, Dict

# 添加当前目录到Python路径，确保可以导入windows_usr_sys_icc_reg模块

# 导入现有的ICC配置库
from . import windows_usr_sys_icc_reg as icc_utils
from .windows_usr_sys_icc_reg import HKLM, winreg,analyze

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QLabel, QTextEdit, QFrame, QScrollArea,
                                QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem,
                                QListWidget, QPushButton, QSizePolicy, QHeaderView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor
PYQT_AVAILABLE = True


class ConfigTableWidget(QTableWidget):
    """
    自定义表格类，封装了配置信息表格的通用功能
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 基础配置
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["属性", "值"])
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setFont(QFont("Arial", 10))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 自动调整设置
        # 设置n-1列自动适应内容（即除了最后一列之外的所有列）
        column_count = self.columnCount()
        if column_count > 0:
            # 前n-1列自动适应内容
            for i in range(column_count - 1):
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
            # 最后一列拉伸以填充剩余空间（保持表格美观）
            self.horizontalHeader().setStretchLastSection(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
    
    def set_table_data(self, rows):
        """
        设置表格数据
        :param rows: 行数据列表，每个元素为(属性名, 属性值)
        """
        # 设置行数
        self.setRowCount(len(rows))
        
        # 设置单元格内容
        for row_idx, (attr, value) in enumerate(rows):
            # 属性列
            attr_item = QTableWidgetItem(attr)
            attr_item.setFont(QFont("Arial", 10, QFont.Bold))
            attr_item.setFlags(attr_item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row_idx, 0, attr_item)
            
            # 值列
            value_item = QTableWidgetItem(value)
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
            value_item.setToolTip(value)  # 添加tooltip以便查看完整内容
            self.setItem(row_idx, 1, value_item)
    
    def adjust_table_size(self):
        """
        自动调整表格大小以适应内容
        """
        # 调整行高以适应内容
        self.resizeRowsToContents()
        
        # 调整列宽以适应内容
        self.resizeColumnsToContents()
        
        # 计算并设置表格高度以适应所有行
        total_height = self.horizontalHeader().height()*1.3  # 表头高度
        for i in range(self.rowCount()):
            total_height += self.rowHeight(i)*1.1  # 加上每行的高度
        total_height += self.verticalHeader().width()  # 加上垂直表头的宽度（如果显示）
        self.setFixedHeight(int(total_height + 2))  # +2 是为了避免边框被截断
        
        # 计算表格宽度
        total_width = 0
        for i in range(self.columnCount()):
            total_width += self.columnWidth(i)
        total_width += self.verticalHeader().width()  # 加上垂直表头的宽度
        total_width += self.frameWidth() * 2  # 加上边框宽度
        
        # 设置表格最小宽度
        self.setMinimumWidth(total_width)


# =============================
# 扩展功能：窗口和显示器识别
# =============================
if PYQT_AVAILABLE:
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    # Win32 API 类型定义
    HWND = ctypes.wintypes.HWND
    HMONITOR = ctypes.wintypes.HANDLE
    DWORD = icc_utils.DWORD
    RECT = icc_utils.RECT

    # Win32 API 函数声明
    user32.MonitorFromWindow.restype = HMONITOR
    user32.MonitorFromWindow.argtypes = [HWND, DWORD]
    user32.GetMonitorInfoW.restype = ctypes.wintypes.BOOL
    user32.GetMonitorInfoW.argtypes = [HMONITOR, ctypes.POINTER(icc_utils.MONITORINFOEX)]

    # 常量
    MONITOR_DEFAULTTONEAREST = 2


class MonitorConfigWindow(QMainWindow):
    """
    PyQt5主窗口类，显示窗口所在显示器的配置信息
    """
    def __init__(self):
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("显示器配置信息")
        self.setGeometry(100, 100, 800, 600)
        
        # 初始化当前显示器
        self.cur_monitor = self.get_window_monitor()
        
        # 初始化UI
        self.init_ui()
        
        # 延迟更新显示器信息（确保窗口已经创建并定位）
        QTimer.singleShot(100, self.update_monitor_info)
    
    def init_ui(self):
        """
        初始化用户界面
        """
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建标题和刷新按钮的水平布局
        header_layout = QHBoxLayout()
        
        # 添加左侧伸缩空间
        header_layout.addStretch()
        
        # 创建标题
        self.title_label = QLabel("显示器配置信息")
        self.title_label.setObjectName("title_label")  # 设置对象名称，用于CSS选择
        self.title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.title_label)
        
        # 添加中间伸缩空间
        header_layout.addStretch()
        
        # 创建刷新按钮并设置最小宽度
        refresh_button = QPushButton("🔄️ 刷新")
        refresh_button.setFont(QFont("Arial", 10))
        refresh_button.clicked.connect(self.refresh_monitor_info)
        refresh_button.setMinimumSize(refresh_button.sizeHint())  # 设置为显示文字所需的最小宽度
        refresh_button.setMaximumSize(refresh_button.sizeHint())  # 限制最大宽度
        header_layout.addWidget(refresh_button)
        
        # 将布局添加到主布局
        main_layout.addLayout(header_layout)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_layout.addWidget(scroll_area)
        
        # 创建滚动区域内的内容组件
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # 显示器基本信息组
        self.monitor_info_group = QGroupBox("显示器基本信息")
        self.monitor_info_layout = QGridLayout()
        self.monitor_info_group.setLayout(self.monitor_info_layout)
        scroll_layout.addWidget(self.monitor_info_group)
        
        # 最终生效配置组
        self.final_config_group = QGroupBox("最终生效配置")
        self.final_config_layout = QVBoxLayout()
        self.final_config_group.setLayout(self.final_config_layout)
        scroll_layout.addWidget(self.final_config_group)
        
        # 用户级配置组
        self.user_config_group = QGroupBox("显示器用户级配置")
        self.user_config_layout = QVBoxLayout()
        self.user_config_group.setLayout(self.user_config_layout)
        scroll_layout.addWidget(self.user_config_group)
        
        # 系统级配置组
        self.system_config_group = QGroupBox("显示器系统级配置")
        self.system_config_layout = QVBoxLayout()
        self.system_config_group.setLayout(self.system_config_layout)
        scroll_layout.addWidget(self.system_config_group)
        
        # Windows 用户级配置情况组
        self.windows_user_config_group = QGroupBox("Windows 用户级配置情况")
        self.windows_user_config_layout = QVBoxLayout()
        self.windows_user_config_group.setLayout(self.windows_user_config_layout)
        scroll_layout.addWidget(self.windows_user_config_group)
        
        # Windows 系统级配置情况组
        self.windows_system_config_group = QGroupBox("Windows 系统级配置情况")
        self.windows_system_config_layout = QVBoxLayout()
        self.windows_system_config_group.setLayout(self.windows_system_config_layout)
        scroll_layout.addWidget(self.windows_system_config_group)
        
        # 设置滚动区域内容
        scroll_area.setWidget(scroll_content)
    
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
        r"""
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
            
            with winreg.OpenKey(HKLM, class_path) as class_key:
                for i in range(winreg.QueryInfoKey(class_key)[0]):
                    subkey_name = winreg.EnumKey(class_key, i)
                    if subkey_name.isdigit() and len(subkey_name) == 4:
                        return subkey_name
        except:
            pass
        
        return None
    
    def update_monitor_info(self):
        """
        更新显示器配置信息
        """
        # 获取当前窗口所在显示器
        monitor = self.get_window_monitor()
        

        
        # 更新当前显示器
        self.cur_monitor = monitor
        
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
        
        # 加载显示器配置
        try:
            
            monitors = analyze()
            
            if not monitors:
                self.show_error("无法获取显示器配置信息")
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
            
            # 更新显示器基本信息
            self.update_monitor_basic_info(instance_id, current_monitor)
            
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
            
        except Exception as e:
            self.show_error(f"加载配置失败: {str(e)}")
    
    def get_rendering_device(self) -> str:
        """
        获取渲染设备信息
        """
        try:
            import wmi
            w = wmi.WMI()
            for gpu in w.Win32_VideoController():
                memory = f"({gpu.AdapterRAM / (1024**3):.0f}GB)" if gpu.AdapterRAM else ""
                return f"{gpu.Name} {memory}"
        except:
            return "未知"
    

    def get_monitor_hardware_id(self, instance_id: str) -> str:
        """
        获取显示器硬件ID
        """
        try:
            from windows_usr_sys_icc_reg import HKLM, winreg
            
            monitor_guid = icc_utils.MONITOR_CLASS_GUID
            class_path = rf"SYSTEM\CurrentControlSet\Control\Class\{monitor_guid}\{instance_id}"
            
            with winreg.OpenKey(HKLM, class_path) as device_key:
                hardware_id = winreg.QueryValueEx(device_key, "HardwareID")[0]
                return hardware_id[0] if hardware_id else "未知"
        except:
            return "未知"
    
    def get_acm_status(self, instance_id: str) -> str:
        """
        获取自动颜色管理(ACM)状态
        """
        try:
            from windows_usr_sys_icc_reg import HKLM, winreg
            
            monitor_guid = icc_utils.MONITOR_CLASS_GUID
            class_path = rf"SYSTEM\CurrentControlSet\Control\Class\{monitor_guid}\{instance_id}\ColorManagement"
            
            with winreg.OpenKey(HKLM, class_path) as cm_key:
                acm_enabled = winreg.QueryValueEx(cm_key, "ColorManagementEnabled")[0]
                return "✅ 已启用" if acm_enabled else "❌ 未配置"
        except:
            return "❌ 未配置"
    
    def update_monitor_basic_info(self, instance_id: str,  current_monitor: Dict):
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
            raise FileNotFoundError(f"无法获取实例ID为 {instance_id} 的显示器信息")
            
            # # 使用默认值
            # friendly_name = icc_utils.get_monitor_friendly_name_by_instance_id(instance_id)
            # rendering_device = self.get_rendering_device()
            # hardware_id = self.get_monitor_hardware_id(instance_id)
            # edid_info = self.get_monitor_edid_info(instance_id)
            # acm_status = self.get_acm_status(instance_id)
        
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
    
    def update_user_config(self, current_monitor: Dict):
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
    
    def update_system_config(self, current_monitor: Dict):
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
    
    def update_final_config(self, current_monitor: Dict):
        """
        更新最终生效配置
        """
        # 清空现有内容
        self.clear_layout(self.final_config_layout)
        
        # 设置表格内容
        rows = []
        
        # 添加当前生效的ICC配置（GDI）
        if current_monitor.get("current_icc_gdi"):
            current_icc_filename = Path(current_monitor["current_icc_gdi"]).name
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
    
    def add_icc_list(self, layout, title: str, icc_list: list, default_path: Optional[str]):
        """
        添加ICC配置列表
        """
        # 创建标题标签
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 9, QFont.Bold))
        layout.addWidget(title_label)
        
        # 创建列表显示区域
        list_widget = QTextEdit()
        list_widget.setReadOnly(True)
        list_widget.setMaximumHeight(100)
        
        if icc_list:
            # 构建列表内容
            content = ""
            for i, (path, source) in enumerate(icc_list, 1):
                filename = Path(path).name
                is_default = " (默认值)" if path == default_path else ""
                content += f"{i}. {filename}{is_default}\n"
            list_widget.setText(content)
        else:
            list_widget.setText("无")
            
        layout.addWidget(list_widget)
    
    def add_label_pair(self, layout, label_text: str, value_text: str, row: int, column: int):
        """
        添加标签对到网格布局
        """
        label = QLabel(f"{label_text}")
        label.setFont(QFont("Arial", 9, QFont.Bold))
        layout.addWidget(label, row, column)
        
        value_label = QLabel(value_text)
        value_label.setWordWrap(True)
        layout.addWidget(value_label, row, column + 1)
    
    def clear_layout(self, layout):
        """
        清空布局内容
        """
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def update_windows_user_config(self, current_monitor: Dict):
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
    
    def update_windows_system_config(self, current_monitor: Dict):
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
    
    def show_error(self, message: str):
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
    
    def moveEvent(self, event):
        """
        窗口移动事件处理函数
        当窗口移动到另一个显示器时，更新配置信息
        """
        # 调用父类的moveEvent
        super().moveEvent(event)
        
        # 检查显示器是否改变
        new_monitor = self.get_window_monitor()
        if new_monitor != self.cur_monitor:
            self.cur_monitor = new_monitor
            # 延迟一段时间后更新配置（确保窗口已经稳定在新位置）
            QTimer.singleShot(500, self.update_monitor_info)
    
    def resizeEvent(self, event):
        """
        窗口大小改变事件处理函数
        当窗口被拉伸到跨越多个显示器时，更新配置信息
        """
        # 调用父类的resizeEvent
        super().resizeEvent(event)
        
        # 检查显示器是否改变
        new_monitor = self.get_window_monitor()
        if new_monitor != self.cur_monitor:
            self.cur_monitor = new_monitor
            # 延迟一段时间后更新配置
            QTimer.singleShot(500, self.update_monitor_info)
    
    def refresh_monitor_info(self):
        """
        刷新显示器配置信息
        """
        # 清除所有当前显示的信息
        self.clear_layout(self.monitor_info_layout)
        self.clear_layout(self.final_config_layout)
        self.clear_layout(self.user_config_layout)
        self.clear_layout(self.system_config_layout)
        self.clear_layout(self.windows_user_config_layout)
        self.clear_layout(self.windows_system_config_layout)
        
        # 重新加载配置
        self.update_monitor_info()


def main():
    """
    主函数
    """
    if not PYQT_AVAILABLE:
        return
    
    # 创建PyQt应用程序
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建主窗口
    window = MonitorConfigWindow()
    
    # 显示窗口
    window.show()
    
    # 进入应用程序主循环
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
