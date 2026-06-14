"""直接解析 ICC 二进制文件，并按需导出 JSON 或 Excel。

本模块负责无外部 ICC 解析库的二进制结构解析。命令行入口支持选择性导出
JSON 和 Excel，GUI 也会复用 parse_icc_binary 获取统一的数据结构。
"""

from icc_structs import (
    ICCHeader, ICC_HEADER_FIELDS, TagTableEntry, ICCTypes, ParsedField, parse_tag_type
)
from icc_serialize import to_json_compatible


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
    header_obj = ICCHeader.from_bytes(data)
    header_values = to_json_compatible(header_obj)
    header_values["reserved"] = header_obj._reserved.hex()
    header = {}

    for field_name, (offset, bytesize, datatype, datasize) in ICC_HEADER_FIELDS.items():
        header[field_name] = [
            header_values.get(field_name),
            offset,
            bytesize,
            datatype,
            datasize,
        ]

    return header


def _parse_tags(data: bytes, tag_count: int) -> dict:
    """解析Tag表"""
    tags = {}

    for i in range(tag_count):
        offset = 132 + i * 12
        entry = TagTableEntry.from_bytes(data, offset)
        tags[entry.signature] = {
            "signature": _field(entry.signature, offset, 4, "signature", 4),
            "data_offset": _field(entry.offset, offset + 4, 4, "uint32", 1),
            "data_size": _field(entry.size, offset + 8, 4, "uint32", 1),
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
        parsed_dict = to_json_compatible(parsed)

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
                        child_parsed = to_json_compatible(child_parsed_raw)
                    else:
                        child_parsed = None

                # assemble child dict with metadata
                child_parsed_dict = to_json_compatible(child_parsed)
                child_entry = {}
                child_entry['offset'] = tag_offset + child_rel
                child_entry['bytesize'] = child_size
                child_entry['datatype'] = child_type
                # datasize from parsed child
                if isinstance(child_parsed_dict, dict) and not child_parsed_dict.get("value") is child_parsed:
                    child_ds = _calculate_datasize(child_parsed_dict, child_type)
                    if child_ds:
                        child_entry['datasize'] = child_ds
                elif isinstance(child_parsed, list):
                    # matrix returns a list
                    child_entry['datasize'] = len(child_parsed) if child_parsed else 0

                # merge parsed content under child_entry
                if isinstance(child_parsed_dict, dict) and not child_parsed_dict.get("value") is child_parsed:
                    # remove redundant top-level metadata in child_parsed if present
                    for k in list(child_parsed_dict.keys()):
                        if k in ('offset', 'bytesize', 'datatype', 'datasize'):
                            continue
                        child_entry[k] = child_parsed_dict[k]
                    if child_name == 'matrix' and 'values' in child_parsed_dict:
                        # Keep the legacy key used by the GUI while exposing structured fields.
                        child_entry['matrix'] = child_parsed_dict['values']
                elif isinstance(child_parsed, list):
                    # matrix returns a list of floats
                    child_entry['matrix'] = child_parsed
                else:
                    # raw bytes or None
                    child_entry['value'] = child_parsed

                if isinstance(child_entry, dict):
                    _apply_mab_child_metadata(
                        child_entry,
                        child_name,
                        child_type,
                        child_bytes,
                        tag_offset + child_rel,
                        child_size,
                    )

                parsed_dict[child_name] = child_entry

        if isinstance(parsed_dict, dict):
            _apply_field_metadata(parsed_dict, type_sig, tag_data, tag_offset, tag_size)

        # 如果解析结果是单字段包装 {'value': ...}，拆开
        if isinstance(parsed_dict, dict) and list(parsed_dict.keys()) == ['value']:
            details[sig] = parsed_dict['value']
        else:
            details[sig] = parsed_dict

    return details


def _field(value, offset: int, bytesize: int, datatype: str, datasize: int = None) -> dict:
    """构造 JSON 友好的字段元信息。"""
    return to_json_compatible(ParsedField(value, offset, bytesize, datatype, datasize))


def _is_field(value) -> bool:
    """判断值是否已经是 ParsedField 序列化后的结构。"""
    return isinstance(value, dict) and {"value", "offset", "bytesize", "datatype"}.issubset(value.keys())


def _field_value(value, default=None):
    """兼容裸值与 ParsedField 结构，取出真实解析值。"""
    if _is_field(value):
        return value.get("value", default)
    return value if value is not None else default


def _wrap_common_type_header(parsed_dict: dict, tag_offset: int) -> None:
    """包装所有 tag type 通用头部: type_signature + reserved。"""
    if "type_signature" in parsed_dict and not _is_field(parsed_dict["type_signature"]):
        parsed_dict["type_signature"] = _field(
            parsed_dict["type_signature"], tag_offset, 4, "signature", 4
        )
    if "reserved" in parsed_dict and not _is_field(parsed_dict["reserved"]):
        parsed_dict["reserved"] = _field(
            parsed_dict["reserved"], tag_offset + 4, 4, "bytes", 4
        )


def _apply_field_metadata(parsed_dict: dict, type_sig: str, tag_data: bytes, tag_offset: int, tag_size: int) -> None:
    """为常见 tag type 的解析字段补充 value/offset/bytesize/datatype/datasize。

    大数组整体包装，不为每个元素重复写 offset，避免 JSON 体积膨胀。
    """
    _wrap_common_type_header(parsed_dict, tag_offset)

    if type_sig == "XYZ ":
        values = parsed_dict.get("values", [])
        if not _is_field(values):
            parsed_dict["values"] = _field(values, tag_offset + 8, max(0, tag_size - 8), "XYZNumber", len(values))
        if "value" in parsed_dict and not _is_field(parsed_dict["value"]):
            parsed_dict["value"] = _field(parsed_dict["value"], tag_offset + 8, 12 if values else 0, "XYZNumber", 1 if values else 0)

    elif type_sig == "curv":
        count = _field_value(parsed_dict.get("count"), 0)
        if not _is_field(parsed_dict.get("count")):
            parsed_dict["count"] = _field(count, tag_offset + 8, 4, "uint32", 1)
        curve_data = parsed_dict.get("curve_data", [])
        if not _is_field(curve_data):
            if count == 0:
                data_offset, data_bytesize, datatype = tag_offset + 12, 0, "none"
            elif count == 1:
                data_offset, data_bytesize, datatype = tag_offset + 12, 2, "u8Fixed8"
            else:
                data_offset, data_bytesize, datatype = tag_offset + 12, count * 2, "uint16"
            parsed_dict["curve_data"] = _field(curve_data, data_offset, data_bytesize, datatype, len(curve_data))

    elif type_sig == "para":
        parameters = parsed_dict.get("parameters", [])
        if not _is_field(parsed_dict.get("function_type")):
            parsed_dict["function_type"] = _field(parsed_dict.get("function_type"), tag_offset + 8, 2, "uint16", 1)
        if "reserved2" in parsed_dict and not _is_field(parsed_dict["reserved2"]):
            parsed_dict["reserved2"] = _field(parsed_dict["reserved2"], tag_offset + 10, 2, "bytes", 2)
        if not _is_field(parameters):
            parsed_dict["parameters"] = _field(parameters, tag_offset + 12, len(parameters) * 4, "s15Fixed16", len(parameters))

    elif type_sig == "text":
        text = parsed_dict.get("text", "")
        if not _is_field(text):
            text_bytesize = len(tag_data[8:].split(b"\x00")[0])
            parsed_dict["text"] = _field(text, tag_offset + 8, text_bytesize, "ascii", len(text))

    elif type_sig == "desc":
        _wrap_text_description_fields(parsed_dict, tag_data, tag_offset)

    elif type_sig == "sig ":
        if "signature" in parsed_dict and not _is_field(parsed_dict["signature"]):
            parsed_dict["signature"] = _field(parsed_dict["signature"], tag_offset + 8, 4, "signature", 4)

    elif type_sig == "sf32":
        values = parsed_dict.get("values", [])
        if not _is_field(values):
            parsed_dict["values"] = _field(values, tag_offset + 8, len(values) * 4, "s15Fixed16", len(values))

    elif type_sig in ("mAB ", "mBA "):
        _wrap_lut_ab_fields(parsed_dict, tag_offset)

    elif type_sig in ("mft1", "lut8"):
        _wrap_lut8_fields(parsed_dict, tag_offset)

    elif type_sig in ("mft2", "lut16"):
        _wrap_lut16_fields(parsed_dict, tag_offset)

    elif type_sig == "meas":
        _wrap_measurement_fields(parsed_dict, tag_offset)

    elif type_sig == "dtim":
        if "value" in parsed_dict and not _is_field(parsed_dict["value"]):
            parsed_dict["value"] = _field(parsed_dict["value"], tag_offset + 8, 12, "dateTimeNumber", 1)


def _wrap_lut_ab_fields(parsed_dict: dict, tag_offset: int) -> None:
    """包装 mAB/mBA 顶层固定字段。"""
    field_specs = {
        "input_channels": (8, 1, "uint8", 1),
        "output_channels": (9, 1, "uint8", 1),
        "padding": (10, 2, "bytes", 2),
        "offset_b_curve": (12, 4, "uint32", 1),
        "offset_matrix": (16, 4, "uint32", 1),
        "offset_m_curve": (20, 4, "uint32", 1),
        "offset_clut": (24, 4, "uint32", 1),
        "offset_a_curve": (28, 4, "uint32", 1),
    }
    for name, (rel, bytesize, datatype, datasize) in field_specs.items():
        if name in parsed_dict and not _is_field(parsed_dict[name]):
            parsed_dict[name] = _field(parsed_dict[name], tag_offset + rel, bytesize, datatype, datasize)


def _wrap_text_description_fields(parsed_dict: dict, tag_data: bytes, tag_offset: int) -> None:
    """包装 ICC v2 desc/textDescriptionType 字段。"""
    ascii_count = parsed_dict.get("ascii_count", 0)
    if not _is_field(parsed_dict.get("ascii_count")):
        parsed_dict["ascii_count"] = _field(ascii_count, tag_offset + 8, 4, "uint32", 1)

    ascii_bytesize = min(max(ascii_count, 0), max(len(tag_data) - 12, 0))
    if "ascii_description" in parsed_dict and not _is_field(parsed_dict["ascii_description"]):
        parsed_dict["ascii_description"] = _field(
            parsed_dict["ascii_description"],
            tag_offset + 12,
            ascii_bytesize,
            "ascii",
            _text_length(parsed_dict["ascii_description"]),
        )

    unicode_language_offset = 12 + ascii_bytesize
    unicode_count_offset = unicode_language_offset + 4
    unicode_text_offset = unicode_count_offset + 4
    unicode_count = parsed_dict.get("unicode_count", 0)
    unicode_bytesize = min(max(unicode_count * 2, 0), max(len(tag_data) - unicode_text_offset, 0))

    if "unicode_language_code" in parsed_dict and not _is_field(parsed_dict["unicode_language_code"]):
        parsed_dict["unicode_language_code"] = _field(parsed_dict["unicode_language_code"], tag_offset + unicode_language_offset, 4, "uint32", 1)
    if "unicode_count" in parsed_dict and not _is_field(parsed_dict["unicode_count"]):
        parsed_dict["unicode_count"] = _field(unicode_count, tag_offset + unicode_count_offset, 4, "uint32", 1)
    if "unicode_description" in parsed_dict and not _is_field(parsed_dict["unicode_description"]):
        parsed_dict["unicode_description"] = _field(
            parsed_dict["unicode_description"],
            tag_offset + unicode_text_offset,
            unicode_bytesize,
            "utf16-be",
            _text_length(parsed_dict["unicode_description"]),
        )

    script_code_offset = unicode_text_offset + unicode_bytesize
    script_count_offset = script_code_offset + 2
    script_text_offset = script_count_offset + 1
    script_count = parsed_dict.get("script_code_count", 0)
    script_bytesize = min(max(script_count, 0), max(len(tag_data) - script_text_offset, 0), 67)

    if "script_code_code" in parsed_dict and not _is_field(parsed_dict["script_code_code"]):
        parsed_dict["script_code_code"] = _field(parsed_dict["script_code_code"], tag_offset + script_code_offset, 2, "uint16", 1)
    if "script_code_count" in parsed_dict and not _is_field(parsed_dict["script_code_count"]):
        parsed_dict["script_code_count"] = _field(script_count, tag_offset + script_count_offset, 1, "uint8", 1)
    if "script_code_description" in parsed_dict and not _is_field(parsed_dict["script_code_description"]):
        parsed_dict["script_code_description"] = _field(
            parsed_dict["script_code_description"],
            tag_offset + script_text_offset,
            script_bytesize,
            "mac-roman",
            _text_length(parsed_dict["script_code_description"]),
        )


def _text_length(value) -> int:
    """返回文本长度，兼容 None 和非字符串值。"""
    return len(value) if isinstance(value, str) else 0


def _apply_mab_child_metadata(
    child_entry: dict,
    child_name: str,
    child_type: str,
    child_bytes: bytes,
    child_offset: int,
    child_size: int,
) -> None:
    """为 mAB/mBA 内部子结构继续补字段级 metadata。"""
    if child_type in ("curv", "para"):
        _apply_field_metadata(child_entry, child_type, child_bytes, child_offset, child_size)
    elif child_name == "matrix":
        _wrap_mab_matrix_fields(child_entry, child_offset)
    elif child_name == "clut":
        _wrap_mab_clut_fields(child_entry, child_offset)


def _wrap_mab_matrix_fields(child_entry: dict, child_offset: int) -> None:
    """包装 mAB/mBA 3x4 矩阵子结构字段。"""
    _wrap_sub_values(child_entry, "values", child_offset, 48, "s15Fixed16", 12)
    _wrap_sub_values(child_entry, "coefficients", child_offset, 36, "s15Fixed16", 9)
    _wrap_sub_values(child_entry, "offsets", child_offset + 36, 12, "s15Fixed16", 3)
    _wrap_sub_values(child_entry, "matrix", child_offset, 48, "s15Fixed16", 12)


def _wrap_mab_clut_fields(child_entry: dict, child_offset: int) -> None:
    """包装 mAB/mBA CLUT 子结构字段。"""
    grid_points = child_entry.get("grid_points", [])
    if not _is_field(grid_points):
        child_entry["grid_points"] = _field(
            grid_points,
            child_offset,
            len(grid_points),
            "uint8",
            len(grid_points),
        )

    precision = child_entry.get("precision")
    if not _is_field(precision):
        child_entry["precision"] = _field(precision, child_offset + 16, 1, "uint8", 1)

    values = child_entry.get("values", [])
    if not _is_field(values):
        data_type = child_entry.get("data_type", "uint8")
        bytes_per_value = 2 if data_type == "uint16" else 1
        child_entry["values"] = _field(
            values,
            child_offset + 20,
            len(values) * bytes_per_value,
            data_type,
            len(values),
        )


def _wrap_lut8_fields(parsed_dict: dict, tag_offset: int) -> None:
    """包装 mft1/lut8 顶层字段和大数组子结构。"""
    for name, rel in (("input_channels", 8), ("output_channels", 9), ("clut_grid_points", 10)):
        if name in parsed_dict and not _is_field(parsed_dict[name]):
            parsed_dict[name] = _field(parsed_dict[name], tag_offset + rel, 1, "uint8", 1)
    _wrap_lut_substructures(parsed_dict, tag_offset, matrix_offset=12, input_offset=48, bit_depth=8)


def _wrap_lut16_fields(parsed_dict: dict, tag_offset: int) -> None:
    """包装 mft2/lut16 顶层字段和大数组子结构。"""
    for name, rel in (("input_channels", 8), ("output_channels", 9), ("clut_grid_points", 10)):
        if name in parsed_dict and not _is_field(parsed_dict[name]):
            parsed_dict[name] = _field(parsed_dict[name], tag_offset + rel, 1, "uint8", 1)
    for name, rel in (("num_input_entries", 48), ("num_output_entries", 50)):
        if name in parsed_dict and not _is_field(parsed_dict[name]):
            parsed_dict[name] = _field(parsed_dict[name], tag_offset + rel, 2, "uint16", 1)
    _wrap_lut_substructures(parsed_dict, tag_offset, matrix_offset=12, input_offset=52, bit_depth=16)


def _wrap_lut_substructures(parsed_dict: dict, tag_offset: int, matrix_offset: int, input_offset: int, bit_depth: int) -> None:
    """包装 lut8/lut16 的矩阵、输入表、CLUT、输出表。"""
    matrix = parsed_dict.get("matrix")
    if isinstance(matrix, dict):
        _wrap_sub_values(matrix, "values", tag_offset + matrix_offset, 36, "s15Fixed16", 9)

    input_table = parsed_dict.get("input_table")
    if isinstance(input_table, dict):
        values = input_table.get("values", [])
        bytes_per_value = 1 if bit_depth == 8 else 2
        _wrap_sub_values(input_table, "values", tag_offset + input_offset, len(values) * bytes_per_value, f"uint{bit_depth}", len(values))

    clut = parsed_dict.get("clut")
    if isinstance(clut, dict):
        input_count = len(_field_value(input_table.get("values"), [])) if isinstance(input_table, dict) else 0
        input_bytes = input_count * (1 if bit_depth == 8 else 2)
        values = clut.get("values", [])
        clut_offset = tag_offset + input_offset + input_bytes
        _wrap_sub_values(clut, "values", clut_offset, len(values) * (1 if bit_depth == 8 else 2), f"uint{bit_depth}", len(values))

    output_table = parsed_dict.get("output_table")
    if isinstance(output_table, dict):
        clut_values = _field_value(clut.get("values"), []) if isinstance(clut, dict) else []
        input_values = _field_value(input_table.get("values"), []) if isinstance(input_table, dict) else []
        values = output_table.get("values", [])
        output_offset = tag_offset + input_offset + (len(input_values) + len(clut_values)) * (1 if bit_depth == 8 else 2)
        _wrap_sub_values(output_table, "values", output_offset, len(values) * (1 if bit_depth == 8 else 2), f"uint{bit_depth}", len(values))


def _wrap_sub_values(container: dict, key: str, offset: int, bytesize: int, datatype: str, datasize: int) -> None:
    """包装子结构中的同质数组字段。"""
    if key in container and not _is_field(container[key]):
        container[key] = _field(container[key], offset, bytesize, datatype, datasize)


def _wrap_measurement_fields(parsed_dict: dict, tag_offset: int) -> None:
    """包装 measurementType 字段。"""
    specs = {
        "observer": (8, 4, "uint32", 1),
        "xyz_backing": (12, 12, "XYZNumber", 1),
        "geometry": (24, 4, "uint32", 1),
        "flare": (28, 4, "uint32", 1),
        "illuminant": (32, 12, "XYZNumber", 1),
    }
    for name, (rel, bytesize, datatype, datasize) in specs.items():
        if name in parsed_dict and not _is_field(parsed_dict[name]):
            parsed_dict[name] = _field(parsed_dict[name], tag_offset + rel, bytesize, datatype, datasize)


def _calculate_datasize(parsed_dict: dict, type_sig: str) -> int:
    """根据datatype计算datasize（数据数量）。

    仅当当前 datatype 对应同质数据集合时返回数量；如果结构内部混合多种
    数据类型（如 mAB/mBA、mft1/mft2、measurementType），不填写 datasize。
    """
    if type_sig in ("XYZ ",):
        values = parsed_dict.get("values", [])
        return len(values) if isinstance(values, list) else 0
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
        # mAB/mBA matrix = 3x4 = 12 values (规范 10.12.5)
        return 12
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
    elif type_sig in ("clrt",):
        return parsed_dict.get("count", 0)
    else:
        return 0


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    from icc_export_excel import export_to_excel
    from export_json import export_to_json, print_summary

    parser = argparse.ArgumentParser(description="ICC Profile Binary Parser")
    parser.add_argument("icc_file", nargs="?", default=r"C:\Users\Admin\ALL\CODE\7-HoverColor\HoverColor\src\color_utils\profiles\sRGB.icc")
    parser.add_argument("-o", "--output", help="导出JSON文件路径")
    parser.add_argument("--no-json", action="store_true", help="不导出JSON")
    parser.add_argument("--excel", action="store_true", help="同时导出Excel文件")
    parser.add_argument("--excel-output", help="导出Excel文件路径；设置后会自动启用Excel导出")
    args = parser.parse_args()

    data = parse_icc_binary(args.icc_file)
    print_summary(data)

    if not args.no_json:
        export_to_json(data, output_path=args.output, icc_path=args.icc_file)

    if args.excel or args.excel_output:
        excel_output = args.excel_output
        if excel_output is None:
            excel_output = str(Path(args.icc_file).with_name(f"{Path(args.icc_file).stem}_parsed.xlsx"))
        export_to_excel(data, excel_output)
        print(f"Excel已导出: {excel_output}")
