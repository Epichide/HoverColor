#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Windows 显示器颜色系统法分析工具（修正版）

1. 严格区分HKCU用户级/HKLM系统级配置，完全对齐Windows官方规范
2. 分离读取 SDR/HDR 各自的关联 ICC 列表，匹配颜色管理UI
3. GDI内存读取真实生效ICC，避免注册表配置与实际生效不一致
4. 完整保留EDID/ACM/硬件指纹等法医级信息
5. 精准匹配显示器实例ID，避免配置错位
6. 明确标注缓存快照，避免误导
"""

import ctypes
import ctypes.wintypes
import winreg
import struct
from pathlib import Path
import platform
import sys
from typing import List, Dict, Optional, Tuple, Union

# =============================
# 基础环境检查
# =============================
if platform.system().lower() != "windows":
    raise RuntimeError("仅支持 Windows 系统")

# =============================
# 全局常量定义
# =============================
# ACM相关
BASE_MONITOR_DATASTORE = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers\MonitorDataStore"
ACM_VALUE_NAME = "AutoColorManagementEnabled"

# EDID相关
BASE_ENUM_DISPLAY = r"SYSTEM\CurrentControlSet\Enum\DISPLAY"

# 显示器类GUID（动态获取+官方兜底）
def get_monitor_class_guid() -> str:
    """
    动态获取显示器类GUID，兜底使用Windows官方固定值
    Returns:
        str: 显示器设备类GUID
    """
    default_guid = "{4d36e96e-e325-11ce-bfc1-08002be10318}"
    try:
        classes_path = r"SYSTEM\CurrentControlSet\Control\Class"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, classes_path) as classes_key:
            for i in range(winreg.QueryInfoKey(classes_key)[0]):
                subkey_name = winreg.EnumKey(classes_key, i)
                try:
                    with winreg.OpenKey(classes_key, subkey_name) as subkey:
                        class_name, _ = winreg.QueryValueEx(subkey, "Class")
                        if class_name == "Monitor":
                            return subkey_name
                except FileNotFoundError:
                    continue
    except Exception:
        pass
    return default_guid

MONITOR_CLASS_GUID = get_monitor_class_guid()

# ICC核心路径
PROFILE_ASSOCIATIONS_PATH = r"Software\Microsoft\Windows NT\CurrentVersion\ICM\ProfileAssociations\Display"
SYS_PROFILE_ASSOCIATIONS_PATH = r"SYSTEM\CurrentControlSet\Control\Class"
COLOR_MANAGEMENT_SCENARIOS_PATH = r"Software\Microsoft\Windows\CurrentVersion\ColorManagement\Scenarios"
COLOR_MANAGEMENT_DEVICES_PATH = r"Software\Microsoft\Windows\CurrentVersion\ColorManagement\Devices"
GLOBAL_ICM_PATH = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ICM"
DEFAULT_COLOR_DIR = Path(r"C:\Windows\System32\spool\drivers\color")

# Win32常量
ICM_ON = 1
is_64bit = sys.maxsize > 2 ** 32
LPARAM = ctypes.c_longlong if is_64bit else ctypes.c_long

# 注册表根常量
HKCU = winreg.HKEY_CURRENT_USER
HKLM = winreg.HKEY_LOCAL_MACHINE

# Win32类型
BOOL = ctypes.wintypes.BOOL
DWORD = ctypes.wintypes.DWORD
RECT = ctypes.wintypes.RECT
LPRECT = ctypes.POINTER(RECT)
HMONITOR = ctypes.wintypes.HANDLE
HDC = ctypes.wintypes.HANDLE

# =============================
# 结构体定义
# =============================
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

# =============================
# DLL加载
# =============================
user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

# =============================
# 核心工具函数
# =============================
def get_monitor_friendly_name_by_instance_id(instance_id: str) -> str:
    """通过实例ID获取显示器友好名称"""
    try:
        reg_path = fr"SYSTEM\CurrentControlSet\Control\Class\{MONITOR_CLASS_GUID}\{instance_id}"
        hkey = winreg.OpenKey(
            HKLM,
            reg_path,
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )
        friendly_name = ""
        # 优先读取 DriverDesc
        try:
            friendly_name, _ = winreg.QueryValueEx(hkey, "DriverDesc")
        except FileNotFoundError:
            # 兜底尝试 FriendlyName
            try:
                friendly_name, _ = winreg.QueryValueEx(hkey, "FriendlyName")
            except FileNotFoundError:
                pass
        winreg.CloseKey(hkey)
        return friendly_name.strip() if friendly_name.strip() else f"显示器_{instance_id}"
    except FileNotFoundError:
        return f"无效实例ID_{instance_id}"
    except Exception:
        return f"读取失败_{instance_id}"

def extract_instance_id_from_device_key(device_key: str) -> Optional[str]:
    """从 DeviceKey 中提取实例ID（0002/0003）"""
    if not device_key:
        return None
    try:
        parts = device_key.split("\\")
        if parts:
            last_part = parts[-1]
            if last_part.isdigit() and len(last_part) >= 4:
                return last_part
    except:
        pass
    return None

def get_exists_mark(path: Optional[str]) -> str:
    """返回文件存在性标记"""
    if not path:
        return ""
    return "" if Path(path).exists() else "❌ 不存在"

def normalize_icc_path(filename: Optional[str]) -> Optional[str]:
    """将ICC文件名转换为完整路径"""
    if not filename or filename.strip() == "":
        return None
    filename = filename.strip()
    if Path(filename).is_absolute():
        return str(Path(filename).resolve(strict=False))
    return str(DEFAULT_COLOR_DIR / filename)

def get_icc_friendly_name(icc_path: Optional[str]) -> str:
    """获取ICC文件的友好名称"""
    if not icc_path:
        return "未知"
    return Path(icc_path).name

def open_color_key(root: int, path: str) -> Optional[int]:
    """安全打开颜色管理注册表项"""
    try:
        return winreg.OpenKey(root, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        return None

def get_rendering_device_name(device_name: str) -> Optional[str]:
    """获取渲染设备友好名称"""
    i = 0
    while True:
        dd = DISPLAY_DEVICE()
        dd.cb = ctypes.sizeof(DISPLAY_DEVICE)
        success = user32.EnumDisplayDevicesW(None, i, ctypes.byref(dd), 0)
        if not success:
            break
        current_name = dd.DeviceName.rstrip("\x00")
        if current_name == device_name:
            friendly_name = dd.DeviceString.rstrip("\x00").strip()
            return friendly_name or None
        i += 1
    return None

# =============================
# 核心修正：正确区分用户/系统级ICC配置
# =============================
def load_icc_config_by_instance(instance_id: str) -> Dict:
    """
    正确加载指定实例ID的ICC配置
    严格区分：HKCU用户级 / HKLM系统级 / 缓存快照
    :param instance_id: 显示器实例ID（0000/0001/0002）
    :return: 结构化的ICC配置字典
    """
    config = {
        # 用户级配置（HKCU）
        "user": {
            "use_user_profile": False,
            "sdr_icc": [],
            "hdr_icc": [],
            "sdr_default": None,
            "hdr_default": None
        },
        # 系统级配置（HKLM，真正的系统全局配置）
        "system": {
            "sdr_icc": [],
            "hdr_icc": [],
            "sdr_default": None,
            "hdr_default": None
        },
        # 系统缓存快照（仅展示，非配置源）
        "cache_snapshot": {
            "sdr_snapshot": [],
            "hdr_snapshot": []
        },
        # 最终生效配置
        "final": {
            "source": "system",
            "sdr_default": None,
            "hdr_default": None
        }
    }

    base_path = f"{PROFILE_ASSOCIATIONS_PATH}\\{MONITOR_CLASS_GUID}\\{instance_id}"
    sys_base_path = f"{SYS_PROFILE_ASSOCIATIONS_PATH}\\{MONITOR_CLASS_GUID}\\{instance_id}"
    def get_value_and_type(query_key: int, query_name: str):
        query_res,query_type = winreg.QueryValueEx(query_key, query_name)
        if query_type==7 and not query_res:
            query_res = []
        return query_res,query_type
    def get_full_iccs_path(iccs,role="用户"):
        res=[]
        for icc in iccs:
            if not icc.strip():
                continue
            full_path=normalize_icc_path(icc)
            if full_path and Path(full_path).exists():
                res.append((full_path, role))
        return res
    # =============================
    # 1. 读取用户级配置（HKCU）
    # =============================
    user_key = open_color_key(HKCU, base_path)
    if user_key:
        try:
            # 读取用户配置开关
            try:
                use_user, _ = winreg.QueryValueEx(user_key, "UsePerUserProfiles")
                config["user"]["use_user_profile"] = (use_user == 1)
            except FileNotFoundError:
                pass
            # 读取用户SDR ICC列表 + 默认值
            try:
                sdr_list, _ = get_value_and_type(user_key,"ICMProfile") 
                config["user"]["sdr_icc"]=get_full_iccs_path(sdr_list,role="用户")
                # 默认值取列表最后一个
                if sdr_list and sdr_list[-1].strip():
                    config["user"]["sdr_default"] = normalize_icc_path(sdr_list[-1])
            except FileNotFoundError:
                pass

            # 读取用户HDR ICC列表 + 默认值
            try:
                hdr_list, _ = get_value_and_type(user_key, "ICMProfileAC")
                config["user"]["hdr_icc"] = get_full_iccs_path(hdr_list,role="用户")
                # 默认值取列表最后一个
                if hdr_list and hdr_list[-1].strip():
                    config["user"]["hdr_default"] = normalize_icc_path(hdr_list[-1])
            except FileNotFoundError:
                pass

            # 读取缓存快照（仅展示，非配置源）
            # 读取用户缓存快照 SDR ICC列表 + 默认值
            try:
                snap_sdr_list, _ = get_value_and_type(user_key,"ICMProfileSnapshot") 
                config["cache_snapshot"]["sdr_snapshot"]=get_full_iccs_path(snap_sdr_list,role="缓存")
                # 默认值取列表最后一个
                if snap_sdr_list and snap_sdr_list[-1].strip():
                    config["cache_snapshot"]["sdr_default"] = normalize_icc_path(snap_sdr_list[-1])
            except FileNotFoundError:
                pass

            # 读取系统缓存快照 HDR ICC列表 + 默认值
            try:
                snap_hdr_list, _ = get_value_and_type(user_key, "ICMProfileACSnapshot")
                config["cache_snapshot"]["hdr_snapshot"]= get_full_iccs_path(snap_hdr_list,role="缓存")
                # 默认值取列表最后一个
                if snap_hdr_list and snap_hdr_list[-1].strip():
                    config["cache_snapshot"]["hdr_default"] = normalize_icc_path(snap_hdr_list[-1])
            except FileNotFoundError:
                pass

        finally:
            winreg.CloseKey(user_key)

    # =============================
    # 2. 读取系统级配置（HKLM，真正的系统配置）
    # =============================
    system_key = open_color_key(HKLM, sys_base_path)
    if system_key:
        try:
            # 读取系统SDR ICC列表 + 默认值
            try:
                sdr_list, _ = winreg.QueryValueEx(system_key, "ICMProfile")
                if not sdr_list: 
                    sdr_list = []
                for filename in sdr_list:
                    if filename.strip():
                        full_path = normalize_icc_path(filename)
                        if full_path and Path(full_path).exists():
                            config["system"]["sdr_icc"].append((full_path, "系统"))
                # 默认值取列表最后一个
                if sdr_list and sdr_list[-1].strip():
                    config["system"]["sdr_default"] = normalize_icc_path(sdr_list[-1])
            except FileNotFoundError:
                pass

            # 读取系统HDR ICC列表 + 默认值
            try:
                hdr_list, _ = winreg.QueryValueEx(system_key, "ICMProfileAC")
                if not hdr_list: 
                    hdr_list=[]
                for filename in hdr_list:
                    if filename.strip():
                        full_path = normalize_icc_path(filename)
                        if full_path and Path(full_path).exists():
                            config["system"]["hdr_icc"].append((full_path, "系统"))
                # 默认值取列表最后一个
                if hdr_list and hdr_list[-1].strip():
                    config["system"]["hdr_default"] = normalize_icc_path(hdr_list[-1])
            except FileNotFoundError:
                pass
        finally:
            winreg.CloseKey(system_key)

    # =============================
    # 3. 计算最终生效配置
    # =============================
    if config["user"]["use_user_profile"]:
        config["final"]["source"] = "用户级"
        config["final"]["sdr_default"] = config["user"]["sdr_default"]
        config["final"]["hdr_default"] = config["user"]["hdr_default"]
    else:
        config["final"]["source"] = "系统级"
        config["final"]["sdr_default"] = config["system"]["sdr_default"]
        config["final"]["hdr_default"] = config["system"]["hdr_default"]

    # 全局兜底sRGB
    global_srgb = str(DEFAULT_COLOR_DIR / "sRGB Color Space Profile.icm")
    if not config["final"]["sdr_default"]:
        config["final"]["sdr_default"] = global_srgb
    if not config["final"]["hdr_default"]:
        config["final"]["hdr_default"] = global_srgb

    return config


# =============================
# Windows 颜色系统默认配置读取
# =============================
def load_windows_registered_profiles() -> Dict:
    """
    读取 Windows 颜色系统默认配置
    包含 用户级(HKCU) + 系统级(HKLM)
    """
    result = {
        "user": {},
        "system": {}
    }

    def read_registered(root, container):
        key = open_color_key(root, r"Software\Microsoft\Windows NT\CurrentVersion\ICM\RegisteredProfiles")
        if not key:
            return
        try:
            value, val_type=winreg.QueryValueEx(key, "sRGB")
            if value:
                container["默认配置"] = normalize_icc_path(value)
        except FileNotFoundError:
            container["默认配置"] = None
        finally:
            winreg.CloseKey(key)

    read_registered(HKCU, result["user"])
    read_registered(HKLM, result["system"])

    return result

def get_current_icc_gdi(device_name: str) -> Tuple[Optional[str], bool]:
    """GDI读取真实生效ICC（系统内存中实际使用的配置，最权威）"""
    hdc = gdi32.CreateDCW("DISPLAY", device_name, None, None)
    if not hdc:
        return None, False
    try:
        gdi32.SetICMMode(hdc, ICM_ON)
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
# EDID/ACM读取函数
# =============================
def read_all_edid() -> Dict:
    edid_map = {}
    try:
        with winreg.OpenKey(HKLM, BASE_ENUM_DISPLAY) as root:
            i = 0
            while True:
                try:
                    vendor = winreg.EnumKey(root, i)
                    with winreg.OpenKey(root, vendor) as vk:
                        j = 0
                        while True:
                            try:
                                instance = winreg.EnumKey(vk, j)
                                path = f"{BASE_ENUM_DISPLAY}\\{vendor}\\{instance}\\Device Parameters"
                                with winreg.OpenKey(HKLM, path) as dp:
                                    edid, _ = winreg.QueryValueEx(dp, "EDID")
                                    edid_map[vendor] = {"instance": instance, "edid": edid, "path": path}
                            except OSError:
                                break
                            j += 1
                except OSError:
                    break
                i += 1
    except PermissionError:
        print("⚠ 需要管理员权限读取EDID", file=sys.stderr)
    return edid_map

def parse_edid(edid_bytes: bytes) -> Optional[Dict]:
    if not edid_bytes or len(edid_bytes) < 16:
        return None
    mfg_raw = struct.unpack(">H", edid_bytes[8:10])[0]
    c1 = ((mfg_raw >> 10) & 0x1F) + 64
    c2 = ((mfg_raw >> 5) & 0x1F) + 64
    c3 = (mfg_raw & 0x1F) + 64
    manufacturer = chr(c1) + chr(c2) + chr(c3)
    product_code = struct.unpack("<H", edid_bytes[10:12])[0]
    serial = struct.unpack("<I", edid_bytes[12:16])[0]
    return {"manufacturer": manufacturer, "product_code": product_code, "serial": serial}

def fingerprint_from_edid(parsed: Optional[Dict]) -> Optional[str]:
    if not parsed:
        return None
    return f"{parsed['manufacturer']}_{parsed['product_code']:04X}_{parsed['serial']:08X}"

def read_acm_registry() -> Dict:
    acm_map = {}
    try:
        with winreg.OpenKey(HKLM, BASE_MONITOR_DATASTORE) as root:
            i = 0
            while True:
                try:
                    subkey = winreg.EnumKey(root, i)
                    with winreg.OpenKey(root, subkey) as k:
                        try:
                            value, _ = winreg.QueryValueEx(k, ACM_VALUE_NAME)
                            acm_map[subkey] = int(value)
                        except FileNotFoundError:
                            acm_map[subkey] = None
                except OSError:
                    break
                i += 1
    except PermissionError:
        print("⚠ 需要管理员权限读取ACM状态", file=sys.stderr)
    return acm_map

def match_acm(parsed: Optional[Dict], acm_map: Dict) -> Tuple[Optional[str], Optional[int]]:
    if not parsed:
        return None, None
    prefix = f"{parsed['manufacturer']}{parsed['product_code']:04X}"
    for k in acm_map:
        if k.startswith(prefix):
            return k, acm_map[k]
    return None, None

# =============================
# 主分析逻辑
# =============================
def analyze() -> List[Dict]:
    windows_profiles = load_windows_registered_profiles()
    edid_map = read_all_edid()
    acm_map = read_acm_registry()
    monitors = []

    MONITORENUMPROC = ctypes.WINFUNCTYPE(BOOL, HMONITOR, HDC, LPRECT, LPARAM)
    @MONITORENUMPROC
    def cb(hmon, hdc, rc, data):
        mi = MONITORINFOEX()
        mi.cbSize = ctypes.sizeof(MONITORINFOEX)
        if not user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            return True
        
        devname = mi.szDevice.strip()
        disp_id = devname.replace("\\\\.\\", "")
        rendering_device = get_rendering_device_name(devname) or "未知"

        dd = DISPLAY_DEVICE()
        dd.cb = ctypes.sizeof(DISPLAY_DEVICE)
        user32.EnumDisplayDevicesW(devname, 0, ctypes.byref(dd), 0)
        device_id = dd.DeviceID.strip()
        device_key = dd.DeviceKey.strip()
        vendor = device_id.split("\\")[1] if "\\" in device_id else None

        instance_id = extract_instance_id_from_device_key(device_key)
        monitor_name = get_monitor_friendly_name_by_instance_id(instance_id) if instance_id else (dd.DeviceString.strip() or "未知显示器")
        
        # 加载核心ICC配置（修正后的逻辑）
        icc_config = load_icc_config_by_instance(instance_id) if instance_id else {}
        use_user_profile = icc_config.get("user", {}).get("use_user_profile", False)

        # EDID和ACM
        edid_info = edid_map.get(vendor)
        parsed_edid = parse_edid(edid_info["edid"]) if edid_info else None
        fp = fingerprint_from_edid(parsed_edid)
        acm_key, acm_state = match_acm(parsed_edid, acm_map)

        # GDI生效ICC
        current_icc, icc_exists = get_current_icc_gdi(devname)

        monitors.append({
            "display_id": disp_id,
            "device_name": devname,
            "rendering_device": rendering_device,
            "friendly_name": monitor_name,
            "device_id": device_id,
            "device_key": device_key,
            "instance_id": instance_id,
            "use_user_profile": use_user_profile,
            "edid": parsed_edid,
            "fingerprint": fp,
            "acm_key": acm_key,
            "acm_state": acm_state,
            "current_icc_gdi": current_icc,
            "current_icc_exists": icc_exists,
            "icc_config": icc_config,
            "windows_profiles": windows_profiles,
        })
        
        return True

    user32.EnumDisplayMonitors(None, None, cb, 0)
    return monitors

# =============================
# 格式化输出
# =============================
def print_report(monitors: List[Dict]):
    print("="*40)
    print("Windows 显示器颜色系统 分析报告（修正版）")
    print("="*40)
    
    for i, m in enumerate(monitors, 1):
        icc = m["icc_config"]
        final = icc.get("final", {})
        user_cfg = icc.get("user", {})
        system_cfg = icc.get("system", {})
        cache = icc.get("cache_snapshot", {})

        print(f"\n【显示器 {i}】 {m['display_id']}")
        print(f"  🖥️  显示器名称: {m['friendly_name']}")
        print(f"  🎨 渲染设备: {m['rendering_device']}")
        print(f"  📋 实例ID: {m['instance_id']} | 硬件ID: {m['device_id']}")
        if m['edid']:
            print(f"  🏭 EDID厂商: {m['edid']['manufacturer']} | 产品代码: {m['edid']['product_code']:04X} | 序列号: {m['edid']['serial']:08X}")
        # ACM状态
        acm_status = "✅ 开启" if m['acm_state']==1 else "❌ 关闭" if m['acm_state']==0 else "未配置"
        print(f"  🤖 自动颜色管理(ACM): {acm_status}")

        # GDI真实生效ICC（最权威）
        print(f"\n  ✅ 【当前真实生效ICC（GDI内存读取）】")
        if m['current_icc_gdi']:
            print(f"    路径: {m['current_icc_gdi']} {get_exists_mark(m['current_icc_gdi'])}")
        else:
            print(f"    未获取到")
            
        # 优先级
        # ACM自动配置 > 显示器用户配置1 > 显示器系统设置2 > Windows用户默认设置3 > Windows系统默认设置4 > 兜底默认值(sRGB)5

        # 最终生效默认值
        print(f"\n  📌 【最终生效默认ICC】")
        print(f"    配置来源: {final.get('source', '未知')}")
        print(f"    SDR默认: {get_icc_friendly_name(final.get('sdr_default'))} | 路径: {final.get('sdr_default')}")
        print(f"    HDR默认: {get_icc_friendly_name(final.get('hdr_default'))} | 路径: {final.get('hdr_default')}")

        # 全配置表明细
        print(f"\n  📋 【显示器配置表明细】")
        print(f"    👲  用户级配置（HKCU，仅当前用户生效）:")
        print(f"       启用用户自定义: {'✅ 是' if m['use_user_profile'] else '❌ 否'}")
        # 是否生效
        is_usr_effective = m['use_user_profile'] # or (m['acm_state'] == 1 and m['fingerprint'] in acm_map)
        is_usr_effective_mark = "" if is_usr_effective else "(未生效)"
        print(f"       用户SDR默认: {get_icc_friendly_name(user_cfg.get('sdr_default'))} {is_usr_effective_mark}")
        print(f"       用户HDR默认: {get_icc_friendly_name(user_cfg.get('hdr_default'))} {is_usr_effective_mark}")
        print(f"    🖥️  系统级配置（HKLM，系统用户）:")

        is_sys_effective_mark = "(未生效)" if is_usr_effective else ""
        print(f"       系统SDR默认: {get_icc_friendly_name(system_cfg.get('sdr_default'))} {is_sys_effective_mark}")
        print(f"       系统HDR默认: {get_icc_friendly_name(system_cfg.get('hdr_default'))} {is_sys_effective_mark}")

        # 用户SDR ICC列表
        print(f"\n     👲 【用户SDR ICC列表（来自 HKCU ICMProfile）】")
        if user_cfg.get('sdr_icc'):
            for idx, (icc_path, source) in enumerate(user_cfg['sdr_icc'], 1):
                default_mark = " (默认值)" if icc_path == user_cfg.get('sdr_default') else ""
                print(f"    {idx:<2}. {get_icc_friendly_name(icc_path):<30} {source:<6} {icc_path} {default_mark} {get_exists_mark(icc_path)}")
        else:
            print(f"    无")

        # 用户HDR ICC列表
        print(f"\n     👮 【用户HDR ICC列表（来自 HKCU ICMProfileAC）】")
        if user_cfg.get('hdr_icc'):
            for idx, (icc_path, source) in enumerate(user_cfg['hdr_icc'], 1):
                default_mark = " (默认值)" if icc_path == user_cfg.get('hdr_default')  else ""
                print(f"    {idx:<2}. {get_icc_friendly_name(icc_path):<30} {source:<6} {icc_path} {default_mark} {get_exists_mark(icc_path)}")
        else:
            print(f"    无")

        # 系统级ICC列表（真正的系统配置，来自HKLM）
        print(f"\n     🖥️  【系统SDR ICC列表（来自 HKLM ICMProfile）】")
        if system_cfg.get('sdr_icc'):
            for idx, (icc_path, source) in enumerate(system_cfg['sdr_icc'], 1):
                default_mark = " (默认值)" if icc_path == system_cfg.get('sdr_default')  else ""
                print(f"    {idx:<2}. {get_icc_friendly_name(icc_path):<30} {source:<6} {icc_path} {default_mark} {get_exists_mark(icc_path)}")
        else:
            print(f"    无")

        print(f"\n     🖥️  【系统HDR ICC列表（来自 HKLM ICMProfileAC）】")
        if system_cfg.get('hdr_icc'):
            for idx, (icc_path, source) in enumerate(system_cfg['hdr_icc'], 1):
                default_mark = " (默认值)" if icc_path == system_cfg.get('hdr_default')  else ""
                print(f"    {idx:<2}. {get_icc_friendly_name(icc_path):<30} {source:<6} {icc_path} {default_mark} {get_exists_mark(icc_path)}")
        else:
            print(f"    无")
            
        

        # 缓存快照（仅展示，明确标注是缓存）
        print(f"\n     💾 【系统配置缓存快照（仅展示，非配置源）】")
        if cache.get('sdr_snapshot'):
            print(f"    SDR快照: {', '.join([get_icc_friendly_name(p) for p, _ in cache['sdr_snapshot']])}")
        if cache.get('hdr_snapshot'):
            print(f"    HDR快照: {', '.join([get_icc_friendly_name(p) for p, _ in cache['hdr_snapshot']])}")
        if not cache.get('sdr_snapshot') and not cache.get('hdr_snapshot'):
            print(f"    无")
            
        # =============================
        # Windows 颜色系统默认值
        # =============================
        win_profiles = m.get("windows_profiles", {})
        user_win = win_profiles.get("user", {})
        sys_win = win_profiles.get("system", {})

        print(f"\n  📋 【Windows配置表明细】")
        print(f"    👲 Windows用户级默认（HKCU RegisteredProfiles）:")
        if user_win:
            for k, v in user_win.items():
                print(f"       {k:<12} → {get_icc_friendly_name(v)} | {v} {get_exists_mark(v)}")
        else:
            print("       无")

        print(f"\n    🖥️ Windows系统级默认（HKLM RegisteredProfiles）:")
        if sys_win:
            for k, v in sys_win.items():
                print(f"       {k:<12} → {get_icc_friendly_name(v)} | {v} {get_exists_mark(v)}")
        else:
            print("       无")

        print(f"\n" + "-"*140)

# =============================
# 入口函数
# =============================
if __name__ == "__main__":
    # 保证中文输出
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    
    # 管理员权限提示
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    if not is_admin:
        print("⚠ 建议以管理员权限运行，可读取完整的HKLM系统级配置和EDID信息\n", file=sys.stderr)
    
    data = analyze()
    print_report(data)