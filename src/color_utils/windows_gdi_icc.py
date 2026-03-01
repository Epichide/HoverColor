import ctypes
import ctypes.wintypes as wintypes
from pathlib import Path
from typing import Optional, Tuple
import winreg

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

DWORD = wintypes.DWORD

# =============================
# GDI 当前生效 ICC
# =============================
def get_current_icc_gdi(device_name: str) -> Tuple[Optional[str], bool]:
    hdc = gdi32.CreateDCW("DISPLAY", device_name, None, None)
    if not hdc:
        return None, False
    try:
        gdi32.SetICMMode(hdc, 2)  # ICM_ON
        size = DWORD(0)
        gdi32.GetICMProfileW(hdc, ctypes.byref(size), None)
        if size.value == 0:
            return None, False

        buf = ctypes.create_unicode_buffer(size.value)
        if not gdi32.GetICMProfileW(hdc, ctypes.byref(size), buf):
            return None, False

        p = Path(buf.value).resolve(strict=False)
        return str(p), p.exists()
    finally:
        gdi32.DeleteDC(hdc)


# =============================
# 枚举显示器
# =============================
class DISPLAY_DEVICE(ctypes.Structure):
    _fields_ = [
        ("cb", DWORD),
        ("DeviceName", ctypes.c_wchar * 32),
        ("DeviceString", ctypes.c_wchar * 128),
        ("StateFlags", DWORD),
        ("DeviceID", ctypes.c_wchar * 128),
        ("DeviceKey", ctypes.c_wchar * 128),
    ]


def enum_display_monitors():
    monitors = []
    i = 0
    while True:
        display = DISPLAY_DEVICE()
        display.cb = ctypes.sizeof(DISPLAY_DEVICE)

        if not user32.EnumDisplayDevicesW(None, i, ctypes.byref(display), 0):
            break

        DISPLAY_DEVICE_ACTIVE = 0x1
        if display.StateFlags & DISPLAY_DEVICE_ACTIVE:
            monitors.append({
                "DeviceName": display.DeviceName,
                "DeviceString": display.DeviceString,
                "DeviceKey": display.DeviceKey
            })

        i += 1

    return monitors


# =============================
# EDID 解析
# =============================
def parse_edid_name(edid: bytes) -> str:
    if len(edid) < 128:
        return "Unknown"

    for i in range(4):
        base = 54 + i * 18
        block = edid[base:base + 18]

        if block[:5] == b"\x00\x00\x00\xFC\x00":
            name = block[5:].rstrip(b"\x0a\x20\x00")
            return name.decode(errors="ignore")

    return "Unknown"


def normalize_device_key(device_key: str) -> str:
    prefix = r"\Registry\Machine\\"
    if device_key.startswith(prefix):
        return device_key[len(prefix):]
    return device_key


def get_friendly_name_from_registry(device_key: str) -> str:
    try:
        path = normalize_device_key(device_key)
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            path + r"\Device Parameters"
        ) as key:
            edid, _ = winreg.QueryValueEx(key, "EDID")
            return parse_edid_name(edid)
    except Exception:
        return "Unknown"


# =============================
# 主程序
# =============================
if __name__ == "__main__":
    monitors = enum_display_monitors()

    if not monitors:
        print("未检测到显示器")
        exit()

    print(f"检测到 {len(monitors)} 个显示器\n")

    for idx, m in enumerate(monitors, 1):
        name = m["DeviceName"]
        desc = m["DeviceString"]
        key = m["DeviceKey"]

        friendly = get_friendly_name_from_registry(key)
        icc_path, exists = get_current_icc_gdi(name)

        print(f"显示器 {idx}")
        print(f"  GDI 名称      : {name}")
        print(f"  显卡报告名    : {desc}")
        print(f"  EDID友好名    : {friendly}")
        print(f"  GDI ICC       : {icc_path}")
        print(f"  ICC文件存在   : {exists}")
        print("-" * 50)