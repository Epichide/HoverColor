"""导出ICC解析结果为JSON"""

import json
from pathlib import Path
from datetime import datetime


class ICCJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime等类型"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.hex()
        return super().default(obj)


def export_to_json(data: dict, output_path: str = None, icc_path: str = None):
    """
    导出ICC解析数据到JSON文件

    Args:
        data: ICC解析数据字典
        output_path: 输出JSON路径，如果为None则自动生成
        icc_path: 原ICC文件路径，用于自动生成输出文件名

    Returns:
        输出文件路径
    """
    if output_path is None:
        if icc_path:
            icc_name = Path(icc_path).stem
            output_path = f"{icc_name}_parsed.json"
        else:
            output_path = f"icc_parsed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # 添加导出时间
    data["export_time"] = datetime.now().isoformat()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=ICCJSONEncoder)

    print(f"JSON已导出: {output_path}")
    return output_path


def print_summary(data: dict):
    """打印解析数据摘要"""
    print("\n" + "=" * 60)
    print(f"【{data.get('parser', 'ICC解析')}】")

    if "header" in data:
        h = data["header"]
        print(f"  设备类: {h.get('device_class', 'N/A')}")
        print(f"  色彩空间: {h.get('color_space', 'N/A')}")
        print(f"  版本: {h.get('version', 'N/A')}")

    if "description" in data:
        print(f"  描述: {data['description']}")

    if "tags" in data:
        print(f"  Tag数量: {len(data['tags'])}")

    if "intent_support" in data:
        print(f"  渲染意图支持: {len(data['intent_support'])} 种")