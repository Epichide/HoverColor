"""ICC 解析结构的序列化工具。

本模块只负责把 ICC 解析得到的 dataclass、bytes、datetime 等 Python 对象
递归转换为 JSON 可存储的基础数据类型：dict、list、str、int、float、bool、None。
"""

from datetime import datetime
from pathlib import Path
from typing import Any


def to_json_compatible(value: Any) -> Any:
    """
    递归转换 ICC 解析结构为 JSON 可存储格式。

    Args:
        value: 任意 Python 对象，通常是 ICC dataclass、dict、list、bytes 等。

    Returns:
        JSON 兼容对象，仅包含 dict/list/str/int/float/bool/None。
    """
    if hasattr(value, "__dataclass_fields__"):
        skipped_fields = _json_skipped_dataclass_fields(value)
        result = {
            field: to_json_compatible(field_value)
            for field, field_value in value.__dict__.items()
            if not field.startswith("_") and field not in skipped_fields
        }
        _add_lut_legacy_value_aliases(value, result)
        return result

    if isinstance(value, dict):
        return {
            key: to_json_compatible(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            to_json_compatible(item)
            for item in value
        ]

    if isinstance(value, bytes):
        return value.hex()

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, str) and _is_null_signature(value):
        return None

    return value


def _is_null_signature(value: str) -> bool:
    """检查 signature 字符串是否为空签名（全零、空格或制表符）。"""
    if not isinstance(value, str):
        return False
    return all(char in ("\x00", " ", "\t") for char in value)


def _json_skipped_dataclass_fields(value: Any) -> set:
    """返回 JSON 输出中需要隐藏的兼容字段，避免导出重复信息。"""
    if value.__class__.__name__ == "XYZType":
        # XYZType.value 是第一组 XYZNumber 的旧兼容别名；完整数据使用 values。
        return {"value"}
    return set()


def _add_lut_legacy_value_aliases(source: Any, result: dict) -> None:
    """为 lut8/lut16 结构化输出补充旧版 value 列表别名。"""
    if source.__class__.__name__ not in ("Lut8Type", "Lut16Type"):
        return

    matrix = result.get("matrix")
    input_table = result.get("input_table")
    clut = result.get("clut")
    output_table = result.get("output_table")

    if isinstance(matrix, dict) and "values" in matrix:
        result["matrix_values"] = matrix["values"]
    if isinstance(input_table, dict) and "values" in input_table:
        result["input_table_values"] = input_table["values"]
    if isinstance(clut, dict) and "values" in clut:
        result["clut_values"] = clut["values"]
    if isinstance(output_table, dict) and "values" in output_table:
        result["output_table_values"] = output_table["values"]
