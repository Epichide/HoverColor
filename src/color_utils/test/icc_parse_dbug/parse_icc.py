"""
ICC配置文件解析工具
支持多种解析方法，可选择性导出JSON

解析方法:
1. binary - 直接解析二进制（无外部依赖）
2. pil - PIL.ImageCms（需要Pillow）
3. lcms2 - lcms2底层API（需要lcms2包）

用法:
    python parse_icc.py [icc_file] [--method binary|pil|lcms2|all] [--json]
"""

import argparse
from pathlib import Path

from parse_binary import parse_icc_binary
from parse_pil import parse_icc_pil
from parse_lcms2 import parse_icc_lcms2
from export_json import export_to_json, print_summary


def parse_icc(icc_path: str, method: str = "all") -> dict:
    """
    解析ICC文件

    Args:
        icc_path: ICC文件路径
        method: 解析方法 (binary/pil/lcms2/all)

    Returns:
        解析数据字典
    """
    if method == "all":
        # 合合所有方法的结果
        result = {
            "parser": "Combined",
            "file_path": str(icc_path),
        }

        # Binary解析
        binary_data = parse_icc_binary(icc_path)
        result["binary"] = binary_data

        # PIL解析
        pil_data = parse_icc_pil(icc_path)
        result["pil"] = pil_data

        # lcms2解析
        lcms2_data = parse_icc_lcms2(icc_path)
        result["lcms2"] = lcms2_data

        return result

    elif method == "binary":
        return parse_icc_binary(icc_path)

    elif method == "pil":
        return parse_icc_pil(icc_path)

    elif method == "lcms2":
        return parse_icc_lcms2(icc_path)

    else:
        raise ValueError(f"未知解析方法: {method}")


def main(icc_file: str = None, method: str = "pil", export_json: bool = False, output_dir: str = None):
    """
    ICC解析主函数

    Args:
        icc_file: ICC文件路径，默认使用sRGB.icc
        method: 解析方法 (binary/pil/lcms2/all)
        export_json: 是否导出JSON
        output_dir: JSON输出目录，默认为output文件夹
    """
    # 默认ICC文件
    default_icc = r"D:\Note\CODE\HoverColor\src\resource\icc\sRGB.icc"
    icc_file = icc_file or default_icc

    # 默认输出目录
    script_dir = Path(__file__).parent
    output_dir = Path(output_dir) if output_dir else script_dir / "output"
    output_dir.mkdir(exist_ok=True)

    # ICC文件名（不含扩展名）
    icc_name = Path(icc_file).stem

    # 解析ICC
    data = parse_icc(icc_file, method)

    # 打印摘要
    if method == "all":
        for key in ["binary", "pil", "lcms2"]:
            if key in data:
                print_summary(data[key])
    else:
        print_summary(data)

    # 导出JSON
    if export_json:
        if method == "all":
            # 分别保存不同方法的JSON
            for key in ["binary", "pil", "lcms2"]:
                if key in data:
                    json_path = output_dir / f"{icc_name}_{key}.json"
                    export_to_json(data[key], str(json_path), icc_file)
        else:
            # 单个方法保存单个JSON
            json_path = output_dir / f"{icc_name}_{method}.json"
            export_to_json(data, str(json_path), icc_file)
    else:
        # 询问是否导出
        choice = input("\n是否导出JSON到output文件夹? (y/n): ").strip().lower()
        if choice == "y":
            if method == "all":
                for key in ["binary", "pil", "lcms2"]:
                    if key in data:
                        json_path = output_dir / f"{icc_name}_{key}.json"
                        export_to_json(data[key], str(json_path), icc_file)
            else:
                json_path = output_dir / f"{icc_name}_{method}.json"
                export_to_json(data, str(json_path), icc_file)


def run_cli():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="ICC配置文件解析工具")
    parser.add_argument("icc_file", nargs="?", default=None, help="ICC文件路径")
    parser.add_argument("--method", "-m", choices=["binary", "pil", "lcms2", "all"],
                        default="pil", help="解析方法")
    parser.add_argument("--json", "-j", action="store_true", help="导出JSON文件")
    parser.add_argument("--output", "-o", default=None, help="JSON输出目录")

    args = parser.parse_args()
    main(icc_file=args.icc_file, method=args.method, export_json=args.json, output_dir=args.output)


if __name__ == "__main__":
    # run_cli()

    default_icc = r"D:\Note\CODE\HoverColor\src\resource\icc\sRGB.icc"
    output_dir = r"D:\Note\CODE\HoverColor\src\color_utils\test\icc_parse\output"
    main(icc_file=default_icc, method="all", export_json=True, output_dir=output_dir)
   
