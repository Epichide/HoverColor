# ICC配置文件解析工具

Python解析ICC色彩配置文件的多种方法。

## 文件结构

```
icc_parse/
├── export_json.py      # 导出JSON的通用函数
├── parse_binary.py     # 直接解析二进制（无依赖）
├── parse_pil.py        # PIL.ImageCms解析
├── parse_lcms2.py      # lcms2底层API解析
├── parse_icc.py        # 主入口，整合所有方法
├── README.md           # 说明文档
└── output/             # JSON输出目录
    ├── *_binary.json
    ├── *_pil.json
    └── *_lcms2.json
```

## 用法

### 命令行

```bash
# PIL方法（默认）
python parse_icc.py [icc_file] --method pil --json

# 二进制解析（无依赖）
python parse_icc.py --method binary --json

# lcms2底层
python parse_icc.py --method lcms2 --json

# 合并所有方法（分别保存3个JSON文件）
python parse_icc.py --method all --json

# 不带--json会询问是否导出
python parse_icc.py
```

### 参数

- `--method` / `-m`: 选择解析方法 (binary/pil/lcms2/all)
- `--json` / `-j`: 直接导出JSON到output文件夹
- `--output` / `-o`: 指定输出目录（默认为output文件夹）

### 直接调用

```python
from parse_icc import main

# 直接传参，导出到output文件夹
main(icc_file="path/to/icc", method="all", export_json=True)

# 使用默认参数
main()
```

## 解析方法对比

| 方法 | 依赖 | 特点 |
|------|------|------|
| binary | 无 | 直接解析二进制，获取头部和Tag信息 |
| pil | Pillow | 通过ImageCms获取描述、渲染意图等 |
| lcms2 | lcms2 | 底层API，功能最全 |

## 依赖安装

```bash
pip install Pillow
pip install lcms2  # 可选，用于lcms2方法
```