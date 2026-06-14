import winreg
import ctypes
import ctypes.wintypes
import platform
import sys
from typing import List, Dict, Optional, Tuple

# ======================== 1. ACM 注册表读取相关常量 ========================
BASE_KEY = r"SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers\\MonitorDataStore"
VALUE_NAME = "AutoColorManagementEnabled"

# ======================== 2. Windows API 相关定义（获取显示器友好名称） ========================
if platform.system().lower() != "windows":
    raise RuntimeError("本脚本仅支持 Windows 系统")

# 基础类型定义
is_64bit = sys.maxsize > 2**32
LPARAM = ctypes.c_longlong if is_64bit else ctypes.c_long
HMONITOR = ctypes.wintypes.HANDLE
HDC = ctypes.wintypes.HDC if hasattr(ctypes.wintypes, "HDC") else ctypes.wintypes.HANDLE
BOOL = ctypes.wintypes.BOOL
DWORD = ctypes.wintypes.DWORD
RECT = ctypes.wintypes.RECT
LPRECT = ctypes.POINTER(RECT)

# 结构体定义
class MONITORINFOEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", DWORD),
        ("szDevice", ctypes.c_wchar * 32),
    ]

class DISPLAY_DEVICE(ctypes.Structure):
    _fields_ = [
        ("cb", DWORD),
        ("DeviceName", ctypes.c_wchar * 32),
        ("DeviceString", ctypes.c_wchar * 128),
        ("StateFlags", DWORD),
        ("DeviceID", ctypes.c_wchar * 128),
        ("DeviceKey", ctypes.c_wchar * 128),
    ]

class PHYSICAL_MONITOR(ctypes.Structure):
    _fields_ = [
        ("hPhysicalMonitor", ctypes.wintypes.HANDLE),
        ("szPhysicalMonitorDescription", ctypes.c_wchar * 128),
    ]

# 加载 DLL 并声明函数
user32 = ctypes.WinDLL("user32", use_last_error=True)
try:
    dxva2 = ctypes.WinDLL("dxva2", use_last_error=True)
except OSError:
    dxva2 = None

# 函数原型
MONITORENUMPROC = ctypes.WINFUNCTYPE(BOOL, HMONITOR, HDC, LPRECT, LPARAM)
user32.EnumDisplayMonitors.argtypes = [HDC, LPRECT, MONITORENUMPROC, LPARAM]
user32.EnumDisplayMonitors.restype = BOOL
user32.GetMonitorInfoW.argtypes = [HMONITOR, ctypes.POINTER(MONITORINFOEX)]
user32.GetMonitorInfoW.restype = BOOL
user32.EnumDisplayDevicesW.argtypes = [ctypes.c_wchar_p, DWORD, ctypes.POINTER(DISPLAY_DEVICE), DWORD]
user32.EnumDisplayDevicesW.restype = BOOL

if dxva2 is not None:
    dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR.argtypes = [HMONITOR, ctypes.POINTER(DWORD)]
    dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR.restype = BOOL
    dxva2.GetPhysicalMonitorsFromHMONITOR.argtypes = [HMONITOR, DWORD, ctypes.POINTER(PHYSICAL_MONITOR)]
    dxva2.GetPhysicalMonitorsFromHMONITOR.restype = BOOL
    dxva2.DestroyPhysicalMonitors.argtypes = [DWORD, ctypes.POINTER(PHYSICAL_MONITOR)]
    dxva2.DestroyPhysicalMonitors.restype = BOOL

# ======================== 3. 核心工具函数 ========================
def get_monitor_friendly_name(hmonitor: HMONITOR) -> Optional[str]:
    """通过 DXVA2 + EnumDisplayDevices 获取显示器友好名称"""
    # 优先用 DXVA2 获取物理显示器名称
    if dxva2 is not None:
        count = DWORD(0)
        if dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(hmonitor, ctypes.byref(count)):
            n = count.value
            if n > 0:
                arr_type = PHYSICAL_MONITOR * n
                arr = arr_type()
                try:
                    if dxva2.GetPhysicalMonitorsFromHMONITOR(hmonitor, n, arr):
                        names = [arr[i].szPhysicalMonitorDescription.rstrip("\x00").strip() for i in range(n)]
                        names = [name for name in names if name]
                        if names:
                            return " | ".join(names)
                finally:
                    dxva2.DestroyPhysicalMonitors(n, arr)

    # 回退：通过 GetMonitorInfo + EnumDisplayDevices 获取
    mi = MONITORINFOEX()
    mi.cbSize = ctypes.sizeof(MONITORINFOEX)
    if user32.GetMonitorInfoW(hmonitor, ctypes.byref(mi)):
        device_name = mi.szDevice.rstrip("\x00").strip()
        i = 0
        while True:
            dd = DISPLAY_DEVICE()
            dd.cb = ctypes.sizeof(DISPLAY_DEVICE)
            if not user32.EnumDisplayDevicesW(device_name, i, ctypes.byref(dd), 0):
                break
            name = dd.DeviceString.rstrip("\x00").strip()
            if name:
                return name
            i += 1
    return None

def get_all_monitors_with_info() -> Dict[str, str]:
    """获取所有显示器：{硬件标识/设备名: 友好名称} 映射"""
    monitor_map = {}
    
    @MONITORENUMPROC
    def callback(hmonitor: HMONITOR, hdc: HDC, lprc: LPRECT, dwData: LPARAM) -> BOOL:
        friendly_name = get_monitor_friendly_name(hmonitor)
        mi = MONITORINFOEX()
        mi.cbSize = ctypes.sizeof(MONITORINFOEX)
        if user32.GetMonitorInfoW(hmonitor, ctypes.byref(mi)):
            device_name = mi.szDevice.rstrip("\x00").strip()
            if friendly_name:
                # 先映射 DISPLAYn 设备名
                monitor_map[device_name] = friendly_name
                
                # 补充映射注册表硬件标识（从 DISPLAY_DEVICE 中提取）
                dd = DISPLAY_DEVICE()
                dd.cb = ctypes.sizeof(DISPLAY_DEVICE)
                if user32.EnumDisplayDevicesW(device_name, 0, ctypes.byref(dd), 0):
                    device_id = dd.DeviceID.rstrip("\x00").strip()
                    if device_id:
                        # 提取 DeviceID 中的硬件标识（和 MonitorDataStore 子键匹配）
                        # 例如 DeviceID: DISPLAY\CMN2700\5&380d758&0&UID24960
                        monitor_map[device_id] = friendly_name
        return True
    
    user32.EnumDisplayMonitors(None, None, callback, LPARAM(0))
    return monitor_map

def list_acm_state_with_friendly_name():
    """读取 ACM 状态 + 关联显示器友好名称"""
    # 1. 获取所有显示器的 硬件标识->友好名称 映射
    monitor_info_map = get_all_monitors_with_info()
    # 2. 读取 ACM 注册表状态
    results = []
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, BASE_KEY) as root:
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(root, i)
            except OSError:
                break
            i += 1

            full_path = f"{BASE_KEY}\\{subkey_name}"
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, full_path) as k:
                    try:
                        value, vtype = winreg.QueryValueEx(k, VALUE_NAME)
                        state = int(value)
                    except FileNotFoundError:
                        state = None
                # 3. 匹配友好名称（优先精确匹配，再模糊匹配）
                friendly_name = monitor_info_map.get(subkey_name)
                if not friendly_name:
                    # 模糊匹配：注册表子键是 DeviceID 的一部分
                    for key in monitor_info_map:
                        if subkey_name in key or key in subkey_name:
                            friendly_name = monitor_info_map[key]
                            break
                if not friendly_name:
                    friendly_name = "未知显示器"

                results.append({
                    "monitor_key": subkey_name,
                    "friendly_name": friendly_name,
                    "acm_state": state,
                })
            except OSError:
                continue
    return results

# ======================== 4. 主函数 ========================
if __name__ == "__main__":
    # 保证控制台中文输出
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    acm_list = list_acm_state_with_friendly_name()
    print("="*80)
    print("显示器自动颜色管理（ACM）状态（含友好名称）")
    print("="*80)
    for item in acm_list:
        key = item["monitor_key"]
        friendly_name = item["friendly_name"]
        state = item["acm_state"]
        
        if state is None:
            status = "未找到 AutoColorManagementEnabled 值 (可能该显示器不支持 ACM)"
        elif state == 1:
            status = "已开启 自动管理应用的颜色"
        elif state == 0:
            status = "已关闭 自动管理应用的颜色"
        else:
            status = f"未知状态: {state}"
        
        print(f"显示器友好名称: {friendly_name}")
        print(f"注册表硬件标识: {key}")
        print(f"ACM 状态: {status}\n")
        print("-"*80)