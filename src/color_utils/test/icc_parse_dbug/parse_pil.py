"""使用PIL.ImageCms解析ICC"""

from PIL import ImageCms
from pathlib import Path


def parse_icc_pil(icc_path: str) -> dict:
    """
    使用PIL.ImageCms解析ICC

    Args:
        icc_path: ICC文件路径

    Returns:
        包含完整解析数据的字典
    """
    profile = ImageCms.getOpenProfile(icc_path)

    result = {
        "parser": "PIL.ImageCms",
        "file_path": str(icc_path),
        "file_name": profile.filename,
    }

    # 基础属性
    result["name"] = ImageCms.getProfileName(profile) or ""
    result["description"] = ImageCms.getProfileDescription(profile) or ""
    result["manufacturer"] = ImageCms.getProfileManufacturer(profile) or ""
    result["model"] = ImageCms.getProfileModel(profile) or ""
    result["copyright"] = ImageCms.getProfileCopyright(profile) or ""
    result["info"] = ImageCms.getProfileInfo(profile) or ""

    # 渲染意图
    result["default_intent"] = _get_intent_name(ImageCms.getDefaultIntent(profile))

    # 渲染意图支持矩阵
    result["intent_support"] = _get_intent_support(profile)

    # Profile属性
    result["product_name"] = profile.product_name
    result["product_info"] = profile.product_info

    # 原始数据
    raw_data = profile.tobytes()
    result["raw_data_size"] = len(raw_data)

    # 尝试从原始数据解析更多信息
    result["header"] = _parse_header_from_raw(raw_data)

    return result


def _get_intent_name(intent) -> str:
    """获取渲染意图名称"""
    names = {
        ImageCms.Intent.PERCEPTUAL: "Perceptual",
        ImageCms.Intent.RELATIVE_COLORIMETRIC: "Relative Colorimetric",
        ImageCms.Intent.SATURATION: "Saturation",
        ImageCms.Intent.ABSOLUTE_COLORIMETRIC: "Absolute Colorimetric",
    }
    return names.get(intent, str(intent))


def _get_intent_direction_name(direction) -> str:
    """获取方向名称"""
    names = {
        ImageCms.Direction.INPUT: "Input",
        ImageCms.Direction.OUTPUT: "Output",
        ImageCms.Direction.PROOF: "Proof",
    }
    return names.get(direction, str(direction))


def _get_intent_support(profile) -> dict:
    """获取渲染意图支持矩阵"""
    support = {}

    for intent in ImageCms.Intent:
        intent_name = _get_intent_name(intent)
        support[intent_name] = {}

        for direction in ImageCms.Direction:
            dir_name = _get_intent_direction_name(direction)
            result = ImageCms.isIntentSupported(profile, intent, direction)
            support[intent_name][dir_name] = {
                "supported": result == 1,
                "value": result,
            }

    return support


def _parse_header_from_raw(raw_data: bytes) -> dict:
    """从原始数据解析头部"""
    import struct

    if len(raw_data) < 132:
        return {}

    return {
        "profile_size": struct.unpack(">I", raw_data[0:4])[0],
        "version": f"{raw_data[8]}.{raw_data[9]}.{raw_data[10]}.{raw_data[11]}",
        "device_class": raw_data[12:16].decode("ascii", errors="replace").strip(),
        "color_space": raw_data[16:20].decode("ascii", errors="replace").strip(),
        "pcs": raw_data[20:24].decode("ascii", errors="replace").strip(),
        "signature": raw_data[36:40].decode("ascii", errors="replace").strip(),
    }


if __name__ == "__main__":
    import sys
    from export_json import export_to_json, print_summary

    icc_file = r"D:\Note\CODE\HoverColor\src\resource\icc\sRGB.icc"
    if len(sys.argv) > 1:
        icc_file = sys.argv[1]

    data = parse_icc_pil(icc_file)
    print_summary(data)

    # 可选导出JSON
    export_json = input("\n是否导出JSON? (y/n): ").strip().lower() == "y"
    if export_json:
        export_to_json(data, icc_path=icc_file)