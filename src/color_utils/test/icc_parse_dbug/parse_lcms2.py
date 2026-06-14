"""使用lcms2底层API解析ICC"""

from PIL import ImageCms
from pathlib import Path


def parse_icc_lcms2(icc_path: str) -> dict:
    """
    使用lcms2底层API解析ICC

    Args:
        icc_path: ICC文件路径

    Returns:
        包含完整解析数据的字典
    """
    try:
        import lcms2
    except ImportError:
        return {
            "parser": "lcms2",
            "error": "需要安装 lcms2: pip install lcms2",
            "available": False,
        }

    profile = ImageCms.getOpenProfile(icc_path)
    handle = profile.profile

    result = {
        "parser": "lcms2",
        "file_path": str(icc_path),
        "available": True,
    }

    # 基础信息
    result["profile_size"] = lcms2.ICCProfileGetSize(handle)
    result["device_class"] = lcms2.ICCProfileGetDeviceClass(handle)
    result["color_space"] = lcms2.ICCProfileGetColorSpace(handle)
    result["pcs"] = lcms2.ICCProfileGetPCS(handle)

    # Tag信息
    tag_count = lcms2.ICCProfileGetTagCount(handle)
    result["tag_count"] = tag_count

    tags = []
    for i in range(tag_count):
        sig = lcms2.ICCProfileGetTagSignature(handle, i)
        sig_str = sig.decode("ascii", errors="replace")
        tags.append(sig_str)

    result["tags"] = tags

    # 尝试读取关键Tag数据
    result["tag_details"] = _read_tag_details(handle, lcms2, tags)

    # Profile属性
    result["pil_info"] = {
        "name": ImageCms.getProfileName(profile) or "",
        "description": ImageCms.getProfileDescription(profile) or "",
        "copyright": ImageCms.getProfileCopyright(profile) or "",
    }

    return result


def _read_tag_details(handle, lcms2, tags: list) -> dict:
    """读取关键Tag的详细信息"""
    details = {}

    # 常见Tag签名映射
    important_tags = {
        "wtpt": "white_point",
        "rXYZ": "red_xyz",
        "gXYZ": "green_xyz",
        "bXYZ": "blue_xyz",
        "rTRC": "red_trc",
        "gTRC": "green_trc",
        "bTRC": "blue_trc",
        "desc": "description",
        "cprt": "copyright",
    }

    for tag in tags:
        if tag in important_tags:
            tag_sig = tag.encode("ascii")
            try:
                data = lcms2.ICCProfileReadTag(handle, tag_sig)
                if data:
                    details[important_tags[tag]] = {
                        "signature": tag,
                        "data_type": str(type(data)),
                        "data": _serialize_tag_data(data),
                    }
            except Exception as e:
                details[important_tags[tag]] = {
                    "signature": tag,
                    "error": str(e),
                }

    return details


def _serialize_tag_data(data) -> dict:
    """序列化Tag数据为可JSON化的格式"""
    import numpy as np

    if isinstance(data, (int, float, str)):
        return {"value": data}

    if isinstance(data, (list, tuple)):
        return {"values": list(data)}

    if isinstance(data, np.ndarray):
        return {"values": data.tolist(), "shape": list(data.shape)}

    if hasattr(data, "__dict__"):
        return {"type": type(data).__name__, "attrs": list(vars(data).keys())}

    return {"type": type(data).__name__, "repr": repr(data)[:200]}


if __name__ == "__main__":
    import sys
    from export_json import export_to_json, print_summary

    icc_file = r"D:\Note\CODE\HoverColor\src\resource\icc\sRGB.icc"
    if len(sys.argv) > 1:
        icc_file = sys.argv[1]

    data = parse_icc_lcms2(icc_file)
    print_summary(data)

    if data.get("error"):
        print(f"\n错误: {data['error']}")
    else:
        # 可选导出JSON
        export_json = input("\n是否导出JSON? (y/n): ").strip().lower() == "y"
        if export_json:
            export_to_json(data, icc_path=icc_file)