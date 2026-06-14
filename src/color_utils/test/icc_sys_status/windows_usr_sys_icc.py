import winreg
import os
import ctypes
from ctypes import wintypes

# 兼容 Python 3.8 手动定义缺失类型
if not hasattr(wintypes, 'ULONG_PTR'):
    import sys
    wintypes.ULONG_PTR = ctypes.c_ulonglong if sys.maxsize > 2**32 else ctypes.c_ulong

def get_monitor_class_guid():
    """从注册表动态获取显示器类的GUID"""
    # 显示器类GUID通常是这个值
    monitor_class_guid = "{4d36e96e-e325-11ce-bfc1-08002be10318}"
    
    try:
        # 打开 Class 键
        class_hkey = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Class",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )
        
        try:
            # 遍历所有子键，找到显示器类GUID
            index = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(class_hkey, index)
                    # 检查子键是否符合显示器类GUID的格式
                    if subkey_name.startswith("{") and subkey_name.endswith("}"):
                        # 打开子键，检查是否有显示器相关的信息
                        subkey = winreg.OpenKey(class_hkey, subkey_name)
                        try:
                            # 尝试读取Class键值，显示器类的Class值应该是"Monitor"
                            class_value, _ = winreg.QueryValueEx(subkey, "Class")
                            if class_value.strip() == "Monitor":
                                return subkey_name
                        except FileNotFoundError:
                            pass
                        finally:
                            winreg.CloseKey(subkey)
                    index += 1
                except OSError:
                    # 没有更多子键了，退出循环
                    break
        finally:
            winreg.CloseKey(class_hkey)
    except Exception as e:
        print(f"获取显示器类GUID失败: {e}")
    
    # 如果没有找到，返回默认的显示器类GUID
    return monitor_class_guid

# 全局常量
MONITOR_CLASS_GUID = get_monitor_class_guid()
CM_REG_PATH = r"Software\Microsoft\Windows NT\CurrentVersion\ICM\ProfileAssociations\Display"
ICC_SYSTEM_DIR = os.path.expandvars(r"C:\Windows\System32\spool\drivers\color")

def get_monitor_friendly_name(instance_id: str) -> str:
    """
    核心功能：通过实例ID获取显示器友好名称（适配你的系统结构）
    """
    try:
        reg_path = fr"SYSTEM\CurrentControlSet\Control\Class\{MONITOR_CLASS_GUID}\{instance_id}"
        hkey = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            reg_path,
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )

        friendly_name = ""
        # 1. 优先读取 DriverDesc（你的系统里这个键就是显示器名称）
        try:
            friendly_name, _ = winreg.QueryValueEx(hkey, "DriverDesc")
        except FileNotFoundError:
            # 2. 兜底尝试 FriendlyName
            try:
                friendly_name, _ = winreg.QueryValueEx(hkey, "FriendlyName")
            except FileNotFoundError:
                pass

        winreg.CloseKey(hkey)
        return friendly_name.strip() if friendly_name.strip() else f"显示器_{instance_id}"

    except FileNotFoundError:
        return f"无效实例ID_{instance_id}"
    except Exception as e:
        return f"读取失败_{instance_id}"

def get_color_management_config():
    """读取Windows颜色管理完整配置（整合显示器名称 + 区分系统SDR/HDR）"""
    result = {
        "system_default": {},
        "display_devices": []
    }

    try:
        root_hkey = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            CM_REG_PATH,
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )

        guid_idx = 0
        while True:
            try:
                guid_name = winreg.EnumKey(root_hkey, guid_idx)
                guid_path = f"{CM_REG_PATH}\\{guid_name}"
                guid_hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, guid_path)

                instance_idx = 0
                while True:
                    try:
                        instance_id = winreg.EnumKey(guid_hkey, instance_idx)
                        instance_path = f"{guid_path}\\{instance_id}"
                        instance_hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, instance_path)

                        # 初始化配置对象，直接绑定显示器名称
                        config = {
                            "instance_id": instance_id,
                            "reg_path": instance_path,
                            "display_name": get_monitor_friendly_name(instance_id),  # 整合友好名称
                            "use_user_profile": False,
                            "user_sdr_icc": [],      # 用户SDR：来自 ICMProfile
                            "user_hdr_icc": [],      # 用户HDR：来自 ICMProfileAC
                            "system_sdr_icc": [],     # 系统SDR：来自 ICMProfileSnapshot
                            "system_hdr_icc": [],     # 系统HDR：来自 ICMProfileSnapshotAC
                            "default_sdr_profile": None,  # 全局默认SDR配置文件
                            "default_hdr_profile": None   # 全局默认HDR配置文件
                        }

                        # 读取所有键值
                        value_idx = 0
                        while True:
                            try:
                                value_name, value_data, value_type = winreg.EnumValue(instance_hkey, value_idx)
                                value_name = value_name.strip()

                                # 1. 读取配置开关
                                if value_name == "UsePerUserProfiles" and value_type == winreg.REG_DWORD:
                                    config["use_user_profile"] = (value_data == 1)
                                # 2. 读取默认配置文件
                                elif value_name == "DefaultProfile" and value_type == winreg.REG_SZ:
                                    # DefaultProfile 通常只存储文件名，不包含路径
                                    if value_data.strip():
                                        full_path = os.path.join(ICC_SYSTEM_DIR, value_data.strip())
                                        if os.path.exists(full_path):
                                            # 默认配置通常是SDR配置
                                            config["default_sdr_profile"] = full_path
                                            # print(f"DEBUG: 从注册表读取到默认SDR配置: {value_data.strip()} -> {full_path}")
                                        else:
                                            # print(f"DEBUG: 注册表默认SDR配置文件不存在: {full_path}")
                                            pass
                                # 调试：打印所有键值
                                # print(f"  键名: {value_name}, 类型: {value_type}, 数据: {value_data}")

                                # 3. 读取用户SDR ICC（ICMProfile）
                                elif value_name == "ICMProfile" and value_type == winreg.REG_MULTI_SZ:
                                    if value_data:
                                        for filename in value_data:
                                            if filename.strip():
                                                full_path = os.path.join(ICC_SYSTEM_DIR, filename.strip())
                                                if os.path.exists(full_path):
                                                    config["user_sdr_icc"].append(full_path)

                                # 4. 读取用户HDR ICC（ICMProfileAC）
                                elif value_name == "ICMProfileAC" and value_type == winreg.REG_MULTI_SZ:
                                    if value_data:
                                        for filename in value_data:
                                            if filename.strip():
                                                full_path = os.path.join(ICC_SYSTEM_DIR, filename.strip())
                                                if os.path.exists(full_path):
                                                    config["user_hdr_icc"].append(full_path)

                                # 5. 读取系统SDR ICC（ICMProfileSnapshot）
                                elif value_name == "ICMProfileSnapshot" and value_type == winreg.REG_MULTI_SZ:
                                    if value_data:
                                        for filename in value_data:
                                            if filename.strip():
                                                full_path = os.path.join(ICC_SYSTEM_DIR, filename.strip())
                                                if os.path.exists(full_path) and full_path not in config["system_sdr_icc"]:
                                                    config["system_sdr_icc"].append(full_path)

                                # 6. 读取系统HDR ICC（ICMProfileSnapshotAC）
                                elif value_name == "ICMProfileSnapshotAC" and value_type == winreg.REG_MULTI_SZ:
                                    if value_data:
                                        for filename in value_data:
                                            if filename.strip():
                                                full_path = os.path.join(ICC_SYSTEM_DIR, filename.strip())
                                                if os.path.exists(full_path) and full_path not in config["system_hdr_icc"]:
                                                    config["system_hdr_icc"].append(full_path)

                                # 7. 兼容：读取其他 ICMProfileSnap 开头的键（兜底）
                                elif value_name.startswith("ICMProfileSnap") and value_type == winreg.REG_MULTI_SZ:
                                    if value_data:
                                        for filename in value_data:
                                            if filename.strip():
                                                full_path = os.path.join(ICC_SYSTEM_DIR, filename.strip())
                                                if os.path.exists(full_path):
                                                    # 根据键名判断是SDR还是HDR
                                                    if "AC" in value_name:
                                                        if full_path not in config["system_hdr_icc"]:
                                                            config["system_hdr_icc"].append(full_path)
                                                    else:
                                                        if full_path not in config["system_sdr_icc"]:
                                                            config["system_sdr_icc"].append(full_path)

                                value_idx += 1
                            except OSError:
                                break
                        
                        # 备用逻辑：如果没有找到DefaultProfile键，设置默认SDR配置
                        if not config.get("default_sdr_profile"):
                            # 优先使用用户SDR配置的第一个
                            if config.get("user_sdr_icc"):
                                config["default_sdr_profile"] = config["user_sdr_icc"][0]
                            # 如果没有用户SDR配置，使用系统SDR配置的第一个
                            elif config.get("system_sdr_icc"):
                                config["default_sdr_profile"] = config["system_sdr_icc"][0]
                        
                        # 备用逻辑：如果没有找到DefaultHDRProfile键，设置默认HDR配置
                        if not config.get("default_hdr_profile"):
                            # 优先使用用户HDR配置的第一个
                            if config.get("user_hdr_icc"):
                                config["default_hdr_profile"] = config["user_hdr_icc"][0]
                            # 如果没有用户HDR配置，使用系统HDR配置的第一个
                            elif config.get("system_hdr_icc"):
                                config["default_hdr_profile"] = config["system_hdr_icc"][0]

                        # 区分系统默认设置和显示器设备
                        if instance_id == "0000":
                            result["system_default"] = config
                        else:
                            # 检查设备是否已经存在于列表中
                            device_exists = False
                            for existing_device in result["display_devices"]:
                                if existing_device["instance_id"] == instance_id:
                                    device_exists = True
                                    break
                            if not device_exists:
                                result["display_devices"].append(config)

                        winreg.CloseKey(instance_hkey)
                        instance_idx += 1
                    except OSError:
                        break

                winreg.CloseKey(guid_hkey)
                guid_idx += 1
            except OSError:
                break

        winreg.CloseKey(root_hkey)
    except Exception as e:
        print(f"读取注册表失败: {e}")

    return result

def main():
    print("=" * 80)
    print("Windows 显示器 ICC 配置（完整整合版 + 区分系统SDR/HDR）")
    print("=" * 80)

    # 读取完整配置
    cm_config = get_color_management_config()

    # 输出系统默认设置
    sys_default = cm_config.get("system_default", {})
    if sys_default:
        print(f"\n📌 【系统默认设置】（实例ID: 0000）")
        print(f"   启用用户配置: {'是' if sys_default.get('use_user_profile', False) else '否'}")
        print(f"   注册表路径: HKEY_CURRENT_USER\\{sys_default.get('reg_path', '')}")

    # 输出所有显示器设备（带真实友好名称）
    print("\n" + "-" * 80)
    display_devices = cm_config.get("display_devices", [])
    print(f"\n🎯 【显示器设备列表】（共 {len(display_devices)} 个）")

    for idx, device in enumerate(display_devices, 1):
        print(f"\n--- 显示器 {idx} ---")
        print(f"🖥️  显示器名称: {device['display_name']}")
        print(f"📋 设备实例ID: {device['instance_id']}")
        print(f"🔘 配置状态: {'✅ 已启用用户自定义配置' if device['use_user_profile'] else '❌ 使用系统默认配置'}")
        print(f"📍 注册表路径: HKEY_CURRENT_USER\\{device['reg_path']}")

        # 输出用户SDR ICC（来自 ICMProfile）
        print("\n   🟢 用户SDR ICC配置（来自 ICMProfile）:")
        if device["user_sdr_icc"]:
            for i, path in enumerate(device["user_sdr_icc"], 1):
                filename = os.path.basename(path)
                # 标记默认值：如果是全局默认SDR配置文件
                if path == device.get("default_sdr_profile"):
                    print(f"    {i}. {filename} (默认值)")
                else:
                    print(f"    {i}. {filename}")
        else:
            print("    无")

        # 输出用户HDR ICC（来自 ICMProfileAC）
        print("\n   🔵 用户HDR ICC配置（来自 ICMProfileAC）:")
        if device["user_hdr_icc"]:
            for i, path in enumerate(device["user_hdr_icc"], 1):
                filename = os.path.basename(path)
                # 标记默认值：如果是全局默认HDR配置文件
                if path == device.get("default_hdr_profile"):
                    print(f"    {i}. {filename} (默认值)")
                else:
                    print(f"    {i}. {filename}")
        else:
            print("    无")

        # 输出系统SDR ICC（来自 ICMProfileSnapshot）
        print("\n   🖥️  系统SDR ICC配置（来自 ICMProfileSnapshot）:")
        if device["system_sdr_icc"]:
            for i, path in enumerate(device["system_sdr_icc"], 1):
                filename = os.path.basename(path)
                # 标记默认值：如果是全局默认SDR配置文件
                if path == device.get("default_sdr_profile"):
                    print(f"    {i}. {filename} (默认值)")
                else:
                    print(f"    {i}. {filename}")
        else:
            print("    无")

        # 输出系统HDR ICC（来自 ICMProfileSnapshotAC）
        print("\n   🎆 系统HDR ICC配置（来自 ICMProfileSnapshotAC）:")
        if device["system_hdr_icc"]:
            for i, path in enumerate(device["system_hdr_icc"], 1):
                filename = os.path.basename(path)
                # 标记默认值：如果是全局默认HDR配置文件
                if path == device.get("default_hdr_profile"):
                    print(f"    {i}. {filename} (默认值)")
                else:
                    print(f"    {i}. {filename}")
        else:
            print("    无")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()