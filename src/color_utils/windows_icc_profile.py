#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows 每个显示器 ICC 配置读取脚本（DXVA2 物理显示器友好名称版）

说明（为什么之前看到的是显卡名称而不是显示器名称）：
- 许多示例代码只对适配器层调用 EnumDisplayDevicesW(None, i, ...)，
  取到的是显示适配器的 DeviceString，例如 "Intel(R) Arc(TM) Pro Graphics"、
  "NVIDIA GeForce RTX 4070 Laptop GPU"，自然就误以为是“显示器友好名称”。
- 真实的物理显示器名称（例如 "EIZO CG2700X"）需要：
  1）通过 DXVA2 Monitor Configuration API，从 HMONITOR 映射到物理显示器
      (GetPhysicalMonitorsFromHMONITOR)，读取 PHYSICAL_MONITOR.szPhysicalMonitorDescription；
  2）或者使用 EnumDisplayDevicesW("\\.\\DISPLAYn", i, ...) 的“监视器枚举”
      （lpDevice 传入显示设备名，而不是 None），取到监视器的 DeviceString。

本脚本的工作流程：
- 使用 EnumDisplayMonitors + GetMonitorInfoW(MONITORINFOEX) 枚举每个显示器：
  得到 HMONITOR 与设备名 "\\.\\DISPLAYn"（注意：n 不一定连续，例如 DISPLAY1 / DISPLAY5 属于正常情况）。
- 对每个 HMONITOR 优先调用 DXVA2 的 GetPhysicalMonitorsFromHMONITOR，
  读取 szPhysicalMonitorDescription 作为物理显示器友好名称；若失败，再回退到
  EnumDisplayDevicesW("\\.\\DISPLAYn", i, ...) 的监视器枚举，取 DeviceString 作为友好名称。
- 为每个 "\\.\\DISPLAYn" 调用 gdi32.CreateDCW("DISPLAY", device_name, None, None) 创建对应 HDC，
  先 SetICMMode(hdc, 1) 启用 ICM，再用 GetICMProfileW 执行“两段式”调用读取当前活动 ICC 路径，
  规范化为绝对路径并检查文件存在性；最终为每个显示器返回结构化结果，绝不做任何目录兜底扫描。

这一版可以正确区分每个物理显示器的 ICC，同时给出真正的物理显示器友好名称，而不是显卡名字。
"""

import ctypes
import ctypes.wintypes
from pathlib import Path
import platform
import sys
from typing import List, Dict, Optional, Tuple

# ---------------------------------
# 基本 Win32 类型与常量定义
# ---------------------------------

if platform.system().lower() != "windows":
    raise RuntimeError("本脚本仅支持在 Windows 上运行")

is_64bit = sys.maxsize > 2 ** 32
LPARAM = ctypes.c_longlong if is_64bit else ctypes.c_long

BOOL = ctypes.wintypes.BOOL
DWORD = ctypes.wintypes.DWORD
RECT = ctypes.wintypes.RECT
LPRECT = ctypes.POINTER(RECT)

# HMONITOR 在 ctypes.wintypes 中未内置，这里用 HANDLE 表示
HMONITOR = ctypes.wintypes.HANDLE
try:
    HDC = ctypes.wintypes.HDC
except AttributeError:  # 旧版本 Python 可能没有 HDC 类型
    HDC = ctypes.wintypes.HANDLE

# ICM 模式常量
ICM_ON = 1

# Win32 错误码
ERROR_INSUFFICIENT_BUFFER = 122

# DISPLAY_DEVICE 标志位
DISPLAY_DEVICE_ACTIVE = 0x00000001


# ---------------------------------
# 结构体定义
# ---------------------------------

class MONITORINFOEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", DWORD),
        ("szDevice", ctypes.c_wchar * 32),  # CCHDEVICENAME = 32
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


# ---------------------------------
# 加载 Win32 DLL（use_last_error=True）
# ---------------------------------

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
try:
    dxva2 = ctypes.WinDLL("dxva2", use_last_error=True)
except OSError:
    dxva2 = None


# ---------------------------------
# 函数原型声明
# ---------------------------------

MONITORENUMPROC = ctypes.WINFUNCTYPE(
    BOOL,
    HMONITOR,  # hMonitor
    HDC,       # hdcMonitor
    LPRECT,    # lprcMonitor
    LPARAM,    # dwData
)

user32.EnumDisplayMonitors.argtypes = [HDC, LPRECT, MONITORENUMPROC, LPARAM]
user32.EnumDisplayMonitors.restype = BOOL

user32.GetMonitorInfoW.argtypes = [HMONITOR, ctypes.POINTER(MONITORINFOEX)]
user32.GetMonitorInfoW.restype = BOOL

user32.EnumDisplayDevicesW.argtypes = [
    ctypes.c_wchar_p,                 # lpDevice
    DWORD,                            # iDevNum
    ctypes.POINTER(DISPLAY_DEVICE),   # lpDisplayDevice
    DWORD,                            # dwFlags
]
user32.EnumDisplayDevicesW.restype = BOOL

gdi32.CreateDCW.argtypes = [
    ctypes.c_wchar_p,  # pwszDriver
    ctypes.c_wchar_p,  # pwszDevice
    ctypes.c_wchar_p,  # pszPort
    ctypes.c_void_p,   # pdm
]
gdi32.CreateDCW.restype = HDC

gdi32.DeleteDC.argtypes = [HDC]
gdi32.DeleteDC.restype = BOOL

gdi32.SetICMMode.argtypes = [HDC, ctypes.c_int]
gdi32.SetICMMode.restype = ctypes.c_int

gdi32.GetICMProfileW.argtypes = [
    HDC,
    ctypes.POINTER(DWORD),   # lpcbName
    ctypes.c_wchar_p,        # lpszFilename
]
gdi32.GetICMProfileW.restype = BOOL

if dxva2 is not None:
    dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR.argtypes = [
        HMONITOR,
        ctypes.POINTER(DWORD),
    ]
    dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR.restype = BOOL

    dxva2.GetPhysicalMonitorsFromHMONITOR.argtypes = [
        HMONITOR,
        DWORD,
        ctypes.POINTER(PHYSICAL_MONITOR),
    ]
    dxva2.GetPhysicalMonitorsFromHMONITOR.restype = BOOL

    dxva2.DestroyPhysicalMonitors.argtypes = [
        DWORD,
        ctypes.POINTER(PHYSICAL_MONITOR),
    ]
    dxva2.DestroyPhysicalMonitors.restype = BOOL


# ---------------------------------
# 工具函数
# ---------------------------------

def _strip_device_prefix(device_name: str) -> str:
    """将 "\\\\.\\DISPLAY1" 形式转换为 "DISPLAY1"。"""
    if device_name.startswith("\\\\.\\"):
        return device_name[4:]
    return device_name


def _last_error_message(prefix: str) -> str:
    """带 Win32 GetLastError() 错误码的简短文本。"""
    err = ctypes.get_last_error()
    return f"{prefix} (GetLastError={err})" if err else prefix


# ---------------------------------
# 显示器枚举
# ---------------------------------

def enumerate_monitors() -> List[Dict[str, object]]:
    """使用 EnumDisplayMonitors + GetMonitorInfoW 枚举所有显示器。

    返回列表中每项包含：
    - hmonitor: HMONITOR 句柄
    - device_name: 原始设备名 "\\.\\DISPLAYn"
    - display_id: 简化 ID "DISPLAYn"
    """

    monitors: List[Dict[str, object]] = []

    @MONITORENUMPROC
    def _callback(hmonitor: HMONITOR, hdc: HDC, lprc: LPRECT, dwData: LPARAM) -> BOOL:
        mi = MONITORINFOEX()
        mi.cbSize = ctypes.sizeof(MONITORINFOEX)
        if not user32.GetMonitorInfoW(hmonitor, ctypes.byref(mi)):
            # 获取失败则跳过该显示器，但继续枚举
            return True
        device_name = mi.szDevice.rstrip("\x00").strip()
        if not device_name:
            return True
        monitors.append(
            {
                "hmonitor": hmonitor,
                "device_name": device_name,
                "display_id": _strip_device_prefix(device_name),
            }
        )
        return True

    success = user32.EnumDisplayMonitors(None, None, _callback, LPARAM(0))
    if not success:
        raise OSError(ctypes.get_last_error() or -1, "EnumDisplayMonitors 调用失败")

    return monitors


# ---------------------------------
# 物理显示器友好名称：DXVA2 + EnumDisplayDevices 回退
# ---------------------------------

def get_friendly_name_dxva2(hmonitor: HMONITOR) -> Tuple[Optional[str], Optional[str]]:
    """通过 DXVA2 Monitor Configuration API 获取物理显示器友好名称。

    返回 (friendly_name, error)；成功时 error 为 None。
    """

    if dxva2 is None:
        return None, "dxva2.dll 不可用，无法使用物理显示器 API"

    count = DWORD(0)
    if not dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(hmonitor, ctypes.byref(count)):
        return None, _last_error_message("GetNumberOfPhysicalMonitorsFromHMONITOR 失败")

    n = count.value
    if n == 0:
        return None, "GetNumberOfPhysicalMonitorsFromHMONITOR 返回 0 个物理显示器"

    arr_type = PHYSICAL_MONITOR * n
    arr = arr_type()

    try:
        if not dxva2.GetPhysicalMonitorsFromHMONITOR(hmonitor, n, arr):
            return None, _last_error_message("GetPhysicalMonitorsFromHMONITOR 失败")

        names = [
            arr[i].szPhysicalMonitorDescription.rstrip("\x00").strip()
            for i in range(n)
        ]
        names = [name for name in names if name]
        if not names:
            return None, "DXVA2 返回的物理显示器描述为空"

        # 多个物理显示器时，用 " | " 拼接，便于观察
        return " | ".join(names), None

    finally:
        # 必须释放物理显示器句柄
        try:
            if n:
                dxva2.DestroyPhysicalMonitors(n, arr)
        except Exception:
            # 释放失败不视为致命错误
            pass


def get_friendly_name_enumdisplaydevices(device_name: str) -> Tuple[Optional[str], Optional[str]]:
    """通过 EnumDisplayDevicesW 的“监视器枚举”获取友好名称。

    这里 lpDevice 传入的是 "\\.\\DISPLAYn"，而非 None，确保是监视器而不是适配器。
    返回 (friendly_name, error)。
    """

    i = 0
    found_name: Optional[str] = None
    had_any = False

    while True:
        dd = DISPLAY_DEVICE()
        dd.cb = ctypes.sizeof(DISPLAY_DEVICE)
        success = user32.EnumDisplayDevicesW(device_name, i, ctypes.byref(dd), 0)
        if not success:
            break
        had_any = True
        name = dd.DeviceString.rstrip("\x00").strip()
        if name:
            # 优先返回第一个枚举到的监视器名称；若需要也可以根据 StateFlags 做筛选
            found_name = name
            # 如果是激活状态的监视器，直接使用
            if dd.StateFlags & DISPLAY_DEVICE_ACTIVE:
                break
        i += 1

    if found_name:
        return found_name, None

    if not had_any:
        return None, _last_error_message(
            f"EnumDisplayDevicesW 监视器枚举失败 (lpDevice={device_name})"
        )

    return None, f"EnumDisplayDevicesW(lpDevice={device_name}) 未找到有效的监视器 DeviceString"


# ---------------------------------
# ICC 路径读取（基于 HDC 的两段式 GetICMProfileW）
# ---------------------------------

def get_icc_profile_for_device(device_name: str) -> Tuple[Optional[str], bool, Optional[str]]:
    """为给定显示设备名（如 "\\.\\DISPLAY1"）读取当前活动 ICC 路径。

    返回 (icc_path, icc_exists, error)。
    - icc_path: 规范化为绝对路径的字符串；失败时为 None。
    - icc_exists: 文件是否存在；icc_path 为 None 时恒为 False。
    - error: 若过程中有错误，返回拼接后的说明，否则为 None。

    注意：严格依赖 CreateDCW + GetICMProfileW，不做任何目录兜底扫描。
    """

    errors = []  # 收集所有非致命错误信息

    # 1. 创建与特定 DISPLAYn 关联的 HDC
    hdc = gdi32.CreateDCW("DISPLAY", device_name, None, None)
    if not hdc:
        return None, False, _last_error_message(
            f"CreateDCW(\"DISPLAY\", {device_name}, ...) 失败"
        )

    try:
        # 2. 启用 ICM 模式（非致命，如果失败仍尝试 GetICMProfileW）
        prev_mode = gdi32.SetICMMode(hdc, ICM_ON)
        if prev_mode == 0:
            errors.append(_last_error_message("SetICMMode(ICM_ON) 失败"))

        # 3. 两段式调用 GetICMProfileW
        # 第一次：lpszFilename=None，lpcbName=0，期望得到 ERROR_INSUFFICIENT_BUFFER 和所需长度
        size = DWORD(0)
        success = gdi32.GetICMProfileW(hdc, ctypes.byref(size), None)
        if not success:
            err = ctypes.get_last_error()
            if err != ERROR_INSUFFICIENT_BUFFER:
                errors.append(
                    f"GetICMProfileW 首次探测缓冲区失败 (GetLastError={err})"
                )
                return None, False, "; ".join(errors) if errors else None
        required = size.value
        if required == 0:
            errors.append("GetICMProfileW 返回的缓冲区长度为 0")
            return None, False, "; ".join(errors)

        # 第二次：分配缓冲区并再次调用
        buf = ctypes.create_unicode_buffer(required)
        success = gdi32.GetICMProfileW(hdc, ctypes.byref(size), buf)
        if not success:
            errors.append(_last_error_message("GetICMProfileW 二次调用失败"))
            return None, False, "; ".join(errors)

        path_str = buf.value.strip()
        if not path_str:
            errors.append("GetICMProfileW 返回空字符串")
            return None, False, "; ".join(errors)

        # 规范化为绝对路径，并检查存在性
        p = Path(path_str).expanduser()
        try:
            # strict=False：即使文件不存在也能得到绝对路径
            p = p.resolve(strict=False)  # type: ignore[call-arg]
        except TypeError:
            # 兼容旧 Python（无 strict 参数）
            p = p.resolve()

        exists = p.exists()
        return str(p), exists, "; ".join(errors) if errors else None

    finally:
        gdi32.DeleteDC(hdc)


# ---------------------------------
# 顶层组合：每个显示器的完整信息
# ---------------------------------

def enumerate_displays_with_icc() -> List[Dict[str, object]]:
    """逐一枚举显示器并获取：设备名、显示 ID、物理显示器友好名称、ICC 路径等。

    返回 list[dict]，每个 dict 包含：
    - device_name: 原始设备名，例如 "\\.\\DISPLAY1"
    - display_id: 简化 ID，例如 "DISPLAY1"
    - friendly_name: 物理显示器友好名称（优先 DXVA2，回退 EnumDisplayDevicesW）
    - icc_path: 当前活动 ICC 路径（绝对路径）或 None
    - icc_exists: ICC 文件是否存在
    - error: 若过程中有任何错误，记录为字符串，否则为 None
    """

    monitors = enumerate_monitors()
    results: List[Dict[str, object]] = []

    for m in monitors:
        hmonitor = m["hmonitor"]
        device_name = str(m["device_name"])
        display_id = str(m["display_id"])

        errors: List[str] = []

        # 1. 友好名称：优先 DXVA2 物理显示器描述
        friendly_name: Optional[str] = None

        dx_name, dx_err = get_friendly_name_dxva2(hmonitor)
        if dx_name:
            friendly_name = dx_name
        if dx_err:
            errors.append(dx_err)

        # 2. 回退：EnumDisplayDevicesW 监视器枚举
        if not friendly_name:
            dd_name, dd_err = get_friendly_name_enumdisplaydevices(device_name)
            if dd_name:
                friendly_name = dd_name
            if dd_err:
                errors.append(dd_err)

        # 3. ICC 路径读取（严格基于 HDC）
        icc_path, icc_exists, icc_err = get_icc_profile_for_device(device_name)
        if icc_err:
            errors.append(icc_err)

        results.append(
            {
                "device_name": device_name,
                "display_id": display_id,
                "friendly_name": friendly_name,
                "icc_path": icc_path,
                "icc_exists": icc_exists,
                "error": "; ".join(errors) if errors else None,
            }
        )

    return results


# ---------------------------------
# 命令行入口：人类可读输出
# ---------------------------------

def main() -> None:
    print("=" * 80)
    print("Windows 每个显示器当前活动 ICC 配置（DXVA2 物理显示器枚举版）")
    print("=" * 80)

    displays = enumerate_displays_with_icc()
    print(f"\n检测到显示器总数：{len(displays)}\n")

    for info in displays:
        device_name = info.get("device_name") or "未知"
        display_id = info.get("display_id") or "未知"
        friendly_name = info.get("friendly_name") or "未知"

        print(
            f"设备标识：{device_name} | 简化 ID：{display_id} | 友好名称：{friendly_name}"
        )

        icc_path = info.get("icc_path")
        icc_exists = bool(info.get("icc_exists"))
        if icc_path:
            mark = "✅" if icc_exists else "❌"
            print(f"ICC：{icc_path} ({mark})")
        else:
            print("ICC：未能读取当前活动 ICC 配置")

        error = info.get("error")
        if error:
            print(f"备注：{error}")

        print("-" * 80)


if __name__ == "__main__":
    # 尽量保证控制台中文输出为 UTF-8，避免乱码
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    main()