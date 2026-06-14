"""直接解析ICC二进制文件（无外部依赖）- 基于结构体解析"""

import struct
from pathlib import Path
from icc_structs import (
    ICCHeader, TagTableEntry, ICCTypes, parse_tag_type, TAG_TYPE_PARSERS
)


# Header 字段定义：名称 -> (偏移量, 字节数, 数据类型)
HEADER_FIELDS = {
    "profile_size": (0, 4, "uint32"),
    "preferred_cmm": (4, 4, "signature"),
    "version": (8, 4, "version"),
    "device_class": (12, 4, "signature"),
    "color_space": (16, 4, "signature"),
    "pcs": (20, 4, "signature"),
    "datetime": (24, 12, "datetime"),
    "signature": (36, 4, "signature"),
    "primary_platform": (40, 4, "signature"),
    "flags": (44, 4, "uint32"),
    "device_manufacturer": (48, 4, "signature"),
    "device_model": (52, 4, "signature"),
    "device_attributes": (56, 8, "uint64"),
    "rendering_intent": (64, 4, "uint32"),
    "illuminant_xyz": (68, 12, "xyz"),
    "creator": (80, 4, "signature"),
    "profile_id": (84, 16, "bytes"),
    "reserved": (100, 28, "bytes"),
}


def parse_icc_binary(icc_path: str) -> dict:
    """
    直接解析ICC文件二进制结构

    Args:
        icc_path: ICC文件路径

    Returns:
        包含完整解析数据的字典
    """
    with open(icc_path, "rb") as f:
        data = f.read()

    result = {
        "parser": "Binary Parser (Struct-based)",
        "file_path": str(icc_path),
        "file_size": len(data),
    }

    # 解析头部（128字节）
    result["header"] = _parse_header_with_metadata(data[:128])

    # 解析Tag表
    tag_count = ICCTypes.unpack_uint32(data[128:132])
    result["tag_count"] = tag_count
    result["tags"] = _parse_tags(data, tag_count)

    # 解析Tag数据
    result["tag_data"] = _parse_all_tag_details(data, result["tags"])

    return result


def _parse_header_with_metadata(data: bytes) -> dict:
    """解析Header，每个字段带有元数据"""
    t = ICCTypes
    header = {}
    
    # profile_size: offset=0, bytesize=4, base datatype=uint32, datasize=4
    header["profile_size"] = [t.unpack_uint32(data[0:4]), 0, 4, "uint32", 4]
    # preferred_cmm: offset=4, bytesize=4, base datatype=signature, datasize=4
    header["preferred_cmm"] = [t.unpack_signature(data[4:8]), 4, 4, "signature", 4]
    # version: offset=8, bytesize=4, base datatype=uint32 (semantic: versionNumber)
    header["version"] = [t.unpack_version(data[8:12]), 8, 4, "uint32", 4]
    # device_class: offset=12, bytesize=4, base datatype=signature, datasize=4
    header["device_class"] = [t.unpack_signature(data[12:16]), 12, 4, "signature", 4]
    # color_space: offset=16, bytesize=4, base datatype=signature, datasize=4
    header["color_space"] = [t.unpack_signature(data[16:20]), 16, 4, "signature", 4]
    # pcs: offset=20, bytesize=4, base datatype=signature, datasize=4
    header["pcs"] = [t.unpack_signature(data[20:24]), 20, 4, "signature", 4]
    # datetime: offset=24, bytesize=12, base datatype=uint16[6] (year,month,day,hour,min,sec)
    header["datetime"] = [t.unpack_datetime(data[24:36]).isoformat(), 24, 12, "uint16[6]", 6]
    # signature: offset=36, bytesize=4, base datatype=signature, datasize=4
    header["signature"] = [t.unpack_signature(data[36:40]), 36, 4, "signature", 4]
    # primary_platform: offset=40, bytesize=4, base datatype=signature, datasize=4
    header["primary_platform"] = [t.unpack_signature(data[40:44]), 40, 4, "signature", 4]
    # flags: offset=44, bytesize=4, base datatype=uint32, datasize=4
    header["flags"] = [t.unpack_uint32(data[44:48]), 44, 4, "uint32", 4]
    # device_manufacturer: offset=48, bytesize=4, base datatype=signature, datasize=4
    header["device_manufacturer"] = [t.unpack_signature(data[48:52]), 48, 4, "signature", 4]
    # device_model: offset=52, bytesize=4, base datatype=signature, datasize=4
    header["device_model"] = [t.unpack_signature(data[52:56]), 52, 4, "signature", 4]
    # device_attributes: offset=56, bytesize=8, base datatype=uint64, datasize=8
    header["device_attributes"] = [t.unpack_uint64(data[56:64]), 56, 8, "uint64", 8]
    # rendering_intent: offset=64, bytesize=4, base datatype=uint32, datasize=4
    header["rendering_intent"] = [t.unpack_uint32(data[64:68]), 64, 4, "uint32", 4]
    # illuminant_xyz: offset=68, bytesize=12, base datatype=s15Fixed16[3]
    xyz = t.unpack_xyz(data[68:80])
    header["illuminant_xyz"] = [list(xyz), 68, 12, "s15Fixed16[3]", 3]
    # creator: offset=80, bytesize=4, base datatype=signature, datasize=4
    header["creator"] = [t.unpack_signature(data[80:84]), 80, 4, "signature", 4]
    # profile_id: offset=84, bytesize=16, raw bytes (represented as hex)
    header["profile_id"] = [data[84:100].hex(), 84, 16, "bytes", 16]
    # reserved: offset=100, bytesize=28, raw bytes (represented as hex)
    header["reserved"] = [data[100:128].hex(), 100, 28, "bytes", 28]
    
    return header


def _parse_tags(data: bytes, tag_count: int) -> dict:
    """解析Tag表"""
    tags = {}

    for i in range(tag_count):
        offset = 132 + i * 12
        entry = TagTableEntry.from_bytes(data, offset)
        tags[entry.signature] = {
            "offset": entry.offset,
            "size": entry.size,
            "type": None,  # 待解析
        }

    return tags


def _parse_all_tag_details(data: bytes, tags: dict) -> dict:
    """解析所有Tag的详细数据"""
    details = {}

    for sig, info in tags.items():
        tag_offset = info["offset"]
        tag_size = info["size"]
        
        if tag_offset + tag_size > len(data):
            details[sig] = ["Error", tag_offset, tag_size, "error", 0]
            continue
        
        tag_data = data[tag_offset:tag_offset + tag_size]
        
        # Tag类型签名在数据的前4字节
        if len(tag_data) < 4:
            details[sig] = ["Error", tag_offset, tag_size, "error", 0]
            continue
            
        type_sig = ICCTypes.unpack_signature(tag_data[0:4])
        info["type"] = type_sig

        # 使用结构体解析器解析，传入完整数据以便计算相对偏移
        parsed = parse_tag_type(tag_data, type_sig, full_data=data, tag_offset=tag_offset)
        parsed_dict = _convert_to_dict(parsed)

        # 如果解析器返回错误信息，保留错误字典
        if isinstance(parsed_dict, dict) and parsed_dict.get('error'):
            details[sig] = parsed_dict
            continue

        # 将基础元信息写入解析结果（方便 GUI 直接读取）
        if isinstance(parsed_dict, dict):
            parsed_dict['offset'] = tag_offset
            parsed_dict['bytesize'] = tag_size
            parsed_dict['datatype'] = type_sig
            datasize = _calculate_datasize(parsed_dict, type_sig)
            if datasize:
                parsed_dict['datasize'] = datasize

        # 对于包含子偏移的复杂类型（如 mAB / mBA），为子元素补充元信息并嵌入解析结果
        if type_sig in ("mAB ", "mBA ") and isinstance(parsed_dict, dict):
            from icc_structs import LutAToBType
            
            # list of (rel_field_name, child_key_name)
            child_offsets = [
                ('offset_b_curve', 'b_curve'),
                ('offset_matrix', 'matrix'),
                ('offset_m_curve', 'm_curve'),
                ('offset_clut', 'clut'),
                ('offset_a_curve', 'a_curve'),
            ]

            # collect relative offsets present
            rels = []
            for rel_name, child_name in child_offsets:
                rel = parsed_dict.get(rel_name)
                if isinstance(rel, int) and rel > 0:
                    rels.append((rel, rel_name, child_name))

            # sort by relative offset
            rels.sort(key=lambda x: x[0])

            for idx, (rel, rel_name, child_name) in enumerate(rels):
                # compute size: next_rel - rel, or tag_size - rel for last
                next_rel = rels[idx+1][0] if idx+1 < len(rels) else tag_size
                child_rel = rel
                child_size = max(0, next_rel - child_rel)
                # bounds check
                if child_rel >= tag_size:
                    continue

                # slice child bytes relative to tag_data
                child_bytes = tag_data[child_rel:child_rel + child_size]

                # parse child: special handling for matrix and clut
                child_parsed = None
                child_type = None
                
                if child_name == 'matrix':
                    # Matrix is 3x3 s15Fixed16 array (no type signature)
                    child_type = "matrix"
                    child_parsed = LutAToBType._parse_matrix(data, tag_offset + child_rel)
                elif child_name == 'clut':
                    # CLUT has special structure (no type signature)
                    child_type = "clut"
                    input_channels = parsed_dict.get('input_channels', 0)
                    output_channels = parsed_dict.get('output_channels', 0)
                    child_parsed = LutAToBType._parse_clut(data, tag_offset + child_rel, input_channels, output_channels)
                else:
                    # For curves (b_curve, m_curve, a_curve), detect type signature
                    if len(child_bytes) >= 4:
                        child_type = ICCTypes.unpack_signature(child_bytes[0:4])
                    
                    if child_type and child_type in ("curv", "para"):
                        child_parsed_raw = parse_tag_type(child_bytes, child_type, full_data=data, tag_offset=tag_offset + child_rel)
                        child_parsed = _convert_to_dict(child_parsed_raw)
                    else:
                        child_parsed = None

                # assemble child dict with metadata
                child_entry = {}
                child_entry['offset'] = tag_offset + child_rel
                child_entry['bytesize'] = child_size
                child_entry['datatype'] = child_type
                # datasize from parsed child
                if isinstance(child_parsed, dict):
                    child_ds = _calculate_datasize(child_parsed, child_type)
                    if child_ds:
                        child_entry['datasize'] = child_ds
                elif isinstance(child_parsed, list):
                    # matrix returns a list
                    child_entry['datasize'] = len(child_parsed) if child_parsed else 0

                # merge parsed content under child_entry
                if isinstance(child_parsed, dict):
                    # remove redundant top-level metadata in child_parsed if present
                    for k in list(child_parsed.keys()):
                        if k in ('offset', 'bytesize', 'datatype', 'datasize'):
                            continue
                        child_entry[k] = child_parsed[k]
                elif isinstance(child_parsed, list):
                    # matrix returns a list of floats
                    child_entry['matrix'] = child_parsed
                else:
                    # raw bytes or None
                    child_entry['value'] = child_parsed

                parsed_dict[child_name] = child_entry

        # 如果解析结果是单字段包装 {'value': ...}，拆开
        if isinstance(parsed_dict, dict) and list(parsed_dict.keys()) == ['value']:
            details[sig] = parsed_dict['value']
        else:
            details[sig] = parsed_dict

    return details


def _calculate_datasize(parsed_dict: dict, type_sig: str) -> int:
    """根据datatype计算datasize（数据数量）"""
    # 根据不同类型计算数据数量
    if type_sig in ("XYZ ",):
        return 3
    elif type_sig in ("curv",):
        return parsed_dict.get("count", 0)
    elif type_sig in ("para",):
        params = parsed_dict.get("parameters", [])
        return len(params) if isinstance(params, list) else 0
    elif type_sig in ("sf32",):
        if "values" in parsed_dict:
            return len(parsed_dict["values"])
        return 0
    elif type_sig in ("mluc",):
        records = parsed_dict.get("records", [])
        return len(records) if isinstance(records, list) else 0
    elif type_sig in ("sig ",):
        return len(parsed_dict.get("signature", ""))
    elif type_sig in ("text",):
        return len(parsed_dict.get("text", ""))
    elif type_sig in ("matrix",):
        # 3x3 matrix = 9 values
        return 9
    elif type_sig in ("clut",):
        # CLUT datasize = product of grid points * output_channels
        grid = parsed_dict.get("grid_points", [])
        output_channels = parsed_dict.get("output_channels", 3)
        if grid:
            total = 1
            for g in grid:
                total *= g
            return total * output_channels
        return 0
    elif type_sig in ("mAB ", "mBA "):
        clut = parsed_dict.get("clut", {})
        if isinstance(clut, dict):
            grid = clut.get("grid_points", [])
            if len(grid) >= 3:
                return grid[0] * grid[1] * grid[2] * parsed_dict.get("output_channels", 3)
        return 0
    elif type_sig in ("lut8", "lut16"):
        return parsed_dict.get("clut_values_count", 0)
    elif type_sig in ("clrt",):
        return parsed_dict.get("count", 0)
    elif type_sig in ("meas",):
        return 1
    else:
        return 0


def _is_null_signature(value: str) -> bool:
    """检查签名字段是否为空（全零或全空白）"""
    if not isinstance(value, str):
        return False
    return all(c in ('\x00', ' ', '\t') for c in value)


def _convert_to_dict(obj) -> dict:
    """将dataclass对象转换为字典"""
    from datetime import datetime
    
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for field, value in obj.__dict__.items():
            if field.startswith("_"):
                continue
            if isinstance(value, tuple):
                result[field] = list(value) if len(value) <= 3 else value
            elif isinstance(value, datetime):
                result[field] = value.isoformat()
            elif isinstance(value, str) and _is_null_signature(value):
                result[field] = None
            else:
                result[field] = value
        return result
    return {"value": obj}


def _parse_tag_details_old(data: bytes, tags: dict) -> dict:
    """解析关键Tag的详细数据（旧版本，保留参考）"""
    details = {}

    for sig, info in tags.items():
        tag_data = data[info["offset"]:info["offset"]+info["size"]]
        tag_type = info["type"]

        if tag_type == "XYZ ":
            xyz = _parse_xyz_tag(tag_data)
            details[sig] = {"type": "XYZ", "value": xyz}
        elif tag_type == "mluc":
            text = _parse_mluc_tag(tag_data)
            details[sig] = {"type": "mluc", "value": text}
        elif tag_type == "curv":
            curve = _parse_curv_tag(tag_data)
            details[sig] = {"type": "curv", "value": curve}
        elif tag_type == "sf32":
            values = _parse_sf32_tag(tag_data)
            details[sig] = {"type": "sf32", "value": values}
        elif tag_type == "sig ":
            sig_val = tag_data[8:12].decode("ascii", errors="replace")
            details[sig] = {"type": "sig", "value": sig_val}
        elif tag_type in ("mAB ", "mBA "):
            lut_info = _parse_lut_tag(tag_data, tag_type)
            details[sig] = lut_info

    return details


def _parse_xyz_tag(data: bytes) -> dict:
    """解析XYZ Tag"""
    t = ICCTypes
    xyz = t.unpack_xyz(data[8:20])
    return {"X": xyz[0], "Y": xyz[1], "Z": xyz[2]}


def _parse_mluc_tag(data: bytes) -> str:
    """解析多语言Unicode描述Tag"""
    from icc_structs import MultiLocalizedUnicodeType
    mluc = MultiLocalizedUnicodeType.from_bytes(data)
    return mluc.get_primary_text()


def _parse_curv_tag(data: bytes) -> dict:
    """解析曲线Tag"""
    from icc_structs import CurveType
    curve = CurveType.from_bytes(data)
    return {
        "count": curve.count,
        "data": curve.curve_data,
    }


def _parse_sf32_tag(data: bytes) -> list:
    """解析s15Fixed16数组Tag"""
    t = ICCTypes
    count = (len(data) - 8) // 4
    values = []
    for i in range(count):
        values.append(t.unpack_s15fixed16(data[8 + i*4:12 + i*4]))
    return values


def _parse_lut_tag(data: bytes, tag_type: str) -> dict:
    """解析LUT Tag（mAB/mBA）"""
    t = ICCTypes
    result = {"type": tag_type.strip()}

    offset = 8
    input_channels = t.unpack_uint8(data[offset:offset+1])
    output_channels = t.unpack_uint8(data[offset+1:offset+2])
    grid_points = t.unpack_uint8(data[offset+2:offset+3])

    result["input_channels"] = input_channels
    result["output_channels"] = output_channels
    result["grid_points"] = grid_points

    return result


if __name__ == "__main__":
    import sys
    import argparse
    from export_json import export_to_json, print_summary

    parser = argparse.ArgumentParser(description="ICC Profile Binary Parser")
    parser.add_argument("icc_file", nargs="?", default=r"D:\material\CODE\HoverColor\src\color_utils\profiles\sRGB.icc")
    parser.add_argument("-o", "--output", help="导出JSON文件路径")
    parser.add_argument("--no-json", action="store_true", help="不导出JSON")
    args = parser.parse_args()

    data = parse_icc_binary(args.icc_file)
    print_summary(data)

    if not args.no_json:
        export_to_json(data, output_path=args.output, icc_path=args.icc_file)
