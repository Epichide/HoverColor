"""Shared bilingual UI text helpers for ICC inspector widgets.

This module keeps lightweight English/Chinese translations in Python so the
hand-written PyQt widgets can switch language without Qt .ts/.qm resources.
"""

from typing import Any


DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {"en", "zh"}


TEXTS = {
    "en": {
        "language.menu": "Language",
        "language.english": "English",
        "language.chinese": "中文",
        "tab.summary": "ICC Summary",
        "tab.gamut": "Gamut",
        "table.basic.headers": ["Item", "Value"],
        "table.detail.headers": ["Item", "Value", "Offset", "Bytesize", "Datatype", "Datasize"],
        "table.tag_name.header": "Tag Name",
        "summary.title": "<b>ICC Summary</b>",
        "summary.help": (
            "Key ICC information and small derived values. "
            "Rows marked with a visualize type can be double-clicked when a viewer is available."
        ),
        "summary.headers": ["Section", "Item", "Value", "Source", "Note", "Visualize"],
        "summary.visualize_prefix": "Open: {value}",
        "summary.visualization_title": "Visualization",
        "summary.visualization_message": (
            "{label} is marked as '{visualizable}'.\n\n"
            "Double-click visualization for curve/LUT/matrix/illuminant data is planned."
        ),
        "summary.no_curve_data": "No curve data was found for this row.",
        "gamut.title": "<b>Gamut</b>",
        "gamut.help": (
            "CIE 1931 xy chromaticity diagram for RGB primary tags. "
            "Solid triangle uses ICC PCS/D50-adapted rXYZ/gXYZ/bXYZ values; "
            "dashed triangle estimates source primaries when chad is available."
        ),
        "gamut.headers": ["Item", "XYZ", "xy", "Note"],
        "gamut.chromaticity": "Chromaticity",
        "gamut.conversion_chain": "Conversion Chain",
        "gamut.axes_title": "CIE 1931 xy Chromaticity Diagram",
        "gamut.no_profile": "No profile data",
        "gamut.no_layers": "No gamut layers selected",
        "gamut.show_pcs": "PCS/D50",
        "gamut.show_source": "Estimated Source",
        "gamut.reset_view": "Reset View",
        "gamut.pcs_primaries": "PCS/D50-adapted primaries",
        "gamut.source_primaries": "Estimated source primaries",
        "gamut.source_label_prefix": "Src {label}",
        "gamut.media_white_point": "Media WP",
        "gamut.source_white_point": "Source WP",
        "chain.title": "<b>Conversion Chain</b>",
        "chain.help": (
            "Inferred ICC transform direction with component-level visualization. "
            "Select a row to inspect curves, matrices, and CLUT/LUT data from left to right."
        ),
        "chain.headers": ["Direction", "Tag", "Intent", "Figure", "Title", "Reason"],
        "chain.select_prompt": "Select a chain row to visualize its components.",
        "chain.no_data": "No conversion-chain data.",
        "chain.no_figure": "No visualizable component was found.",
        "chain.reference_figure": "Reference Figure",
        "chain.no_reference_figure": "No reference figure for this chain.",
        "chain.figure_error": "Figure not found or failed to load:\n{image_path}",
        "chain.reset_view": "Reset View",
    },
    "zh": {
        "language.menu": "语言",
        "language.english": "English",
        "language.chinese": "中文",
        "tab.summary": "ICC 摘要",
        "tab.gamut": "色域",
        "table.basic.headers": ["项目", "值"],
        "table.detail.headers": ["项目", "值", "偏移", "字节数", "数据类型", "数据数量"],
        "table.tag_name.header": "标签名",
        "summary.title": "<b>ICC 摘要</b>",
        "summary.help": "显示 ICC 配置文件的关键信息和少量派生值。标记了可视化类型的行在有对应视图时可双击打开。",
        "summary.headers": ["分类", "项目", "值", "来源", "说明", "可视化"],
        "summary.visualize_prefix": "打开: {value}",
        "summary.visualization_title": "可视化",
        "summary.visualization_message": "{label} 标记为“{visualizable}”。\n\n曲线/LUT/矩阵/光源数据的双击可视化后续接入。",
        "summary.no_curve_data": "没有找到这一行对应的曲线数据。",
        "gamut.title": "<b>色域</b>",
        "gamut.help": (
            "基于 RGB primary 标签显示 CIE 1931 xy 色度图。实线三角形使用 ICC PCS/D50 适配后的 "
            "rXYZ/gXYZ/bXYZ；虚线三角形在存在 chad 时估算源色域原色。"
        ),
        "gamut.headers": ["项目", "XYZ", "xy", "说明"],
        "gamut.chromaticity": "色度图",
        "gamut.conversion_chain": "转换链",
        "gamut.axes_title": "CIE 1931 xy 色度图",
        "gamut.no_profile": "暂无配置文件数据",
        "gamut.no_layers": "未选择要显示的色域图层",
        "gamut.show_pcs": "PCS/D50",
        "gamut.show_source": "估算源",
        "gamut.reset_view": "重置视图",
        "gamut.pcs_primaries": "PCS/D50 适配原色",
        "gamut.source_primaries": "估算源原色",
        "gamut.source_label_prefix": "源 {label}",
        "gamut.media_white_point": "介质白点",
        "gamut.source_white_point": "源白点",
        "chain.title": "<b>转换链</b>",
        "chain.help": "显示推断出的 ICC 转换方向，并按链路顺序可视化曲线、矩阵和 CLUT/LUT 组件。",
        "chain.headers": ["方向", "标签", "意图", "图示", "标题", "原因"],
        "chain.select_prompt": "选择一条转换链记录以可视化其中的组件。",
        "chain.no_data": "暂无转换链数据。",
        "chain.no_figure": "未找到可视化组件。",
        "chain.reference_figure": "参考图",
        "chain.no_reference_figure": "该链路没有参考图。",
        "chain.figure_error": "图示不存在或加载失败:\n{image_path}",
        "chain.reset_view": "重置视图",
    },
}


DISPLAY_TEXTS_ZH = {
    "General": "基本信息",
    "Metadata": "元数据",
    "Colorimetry": "色度信息",
    "RGB Primaries": "RGB 原色",
    "TRC": "TRC",
    "Pipeline": "转换管线",
    "Notes": "备注",
    "Profile Description": "Profile 描述",
    "Device Class": "设备类别",
    "Color Space": "颜色空间",
    "PCS": "PCS",
    "ICC Version": "ICC 版本",
    "Rendering Intent": "渲染意图",
    "Profile Size": "Profile 大小",
    "Tag Count": "Tag 数量",
    "Copyright": "版权",
    "Creator": "创建者",
    "Media White Point": "介质白点",
    "Media White Point xy": "介质白点 xy",
    "PCS White Point": "PCS 白点",
    "PCS White Point xy": "PCS 白点 xy",
    "Black Point": "黑点",
    "Black Point xy": "黑点 xy",
    "Red Primary": "红原色",
    "Red Primary xy": "红原色 xy",
    "Green Primary": "绿原色",
    "Green Primary xy": "绿原色 xy",
    "Blue Primary": "蓝原色",
    "Blue Primary xy": "蓝原色 xy",
    "Chromatic Adaptation Matrix": "色适应矩阵",
    "Estimated Source White Point": "估算源白点",
    "Estimated Source White Point xy": "估算源白点 xy",
    "Red TRC": "红色 TRC",
    "Green TRC": "绿色 TRC",
    "Blue TRC": "蓝色 TRC",
    "RGB TRC": "RGB TRC",
    "B Curves / RGB TRC": "B 曲线 / RGB TRC",
    "B Curves / RGB TRC^-1": "B 曲线 / RGB TRC^-1",
    "A Curves": "A 曲线",
    "B Curves": "B 曲线",
    "M Curves": "M 曲线",
    "CLUT": "CLUT",
    "Matrix": "矩阵",
    "RGB -> PCSXYZ Matrix": "RGB -> PCSXYZ 矩阵",
    "PCSXYZ -> RGB Matrix^-1": "PCSXYZ -> RGB 逆矩阵",
    "RGB Primary Tags": "RGB 原色标签",
    "Profile description tag": "Profile 描述标签",
    "Media white point tag": "介质白点标签",
    "Copyright tag": "版权标签",
    "Profile Connection Space": "Profile 连接空间",
    "PCS (D50)": "PCS (D50)",
    "Derived from XYZ": "由 XYZ 派生",
    "Derived from Media White Point XYZ": "由介质白点 XYZ 派生",
    "Derived from Estimated Source White Point XYZ": "由估算源白点 XYZ 派生",
    "Derived from PCS White Point XYZ": "由 PCS 白点 XYZ 派生",
    "Derived from Black Point XYZ": "由黑点 XYZ 派生",
    "parametric type=": "参数曲线 type=",
    "params=": "参数=",
    "curveType count=0; identity curve": "curveType count=0；恒等曲线",
    "curveType count=1; gamma curve": "curveType count=1；gamma 曲线",
    "curveType 1D sampled curve": "curveType 1D 采样曲线",
    "points=": "点数=",
    "declared count=": "声明 count=",
    "Derived by inverse(chad) * wtpt": "由 inverse(chad) * wtpt 推导",
    "Derived by inverse(chad) * illuminant_xyz": "由 inverse(chad) * illuminant_xyz 推导",
    "Approximated from wtpt because chad is not present": "未找到 chad，使用 wtpt 近似",
    "Media white from wtpt tag; not necessarily PCS white": "来自 wtpt 标签的介质白点；不一定等同于 PCS 白点",
    "Estimated adopted/source white by inverse(chad) * PCS White Point": "通过 inverse(chad) * PCS 白点估算 adopted/source 白点",
    "No chad; approximated from wtpt media white": "没有 chad；使用 wtpt 介质白点近似",
    "PCS illuminant from ICC header; ICC PCS white is normally D50": "来自 ICC header 的 PCS illuminant；ICC PCS 白点通常为 D50",
    "Adapts estimated source/adopted white to PCS white": "将估算的 source/adopted 白点适配到 PCS 白点",
    "Double-click visualization planned": "计划支持双击可视化",
    "Not found in this profile": "当前 profile 中未找到",
    "Can derive xy primaries": "可派生 xy 原色",
    "rXYZ/gXYZ/bXYZ are present": "rXYZ/gXYZ/bXYZ 均存在",
    "illuminant": "光源",
    "curve": "曲线",
    "matrix": "矩阵",
    "lut": "LUT",
    "Scanner": "扫描仪",
    "Display/Monitor": "显示器",
    "Printer": "打印机",
    "DeviceLink": "设备链接",
    "ColorSpace": "颜色空间",
    "Abstract": "抽象",
    "NamedColor": "命名颜色",
    "Perceptual": "感知",
    "Media-relative Colorimetric": "媒介相对色度",
    "Saturation": "饱和度",
    "ICC-absolute Colorimetric": "ICC 绝对色度",
    "Red": "红",
    "Green": "绿",
    "Blue": "蓝",
    "Red Primary (PCS/D50)": "红原色 (PCS/D50)",
    "Green Primary (PCS/D50)": "绿原色 (PCS/D50)",
    "Blue Primary (PCS/D50)": "蓝原色 (PCS/D50)",
    "Red Primary (Estimated Source)": "红原色 (估算源)",
    "Green Primary (Estimated Source)": "绿原色 (估算源)",
    "Blue Primary (Estimated Source)": "蓝原色 (估算源)",
    "from tag_data.rXYZ": "来自 tag_data.rXYZ",
    "from tag_data.gXYZ": "来自 tag_data.gXYZ",
    "from tag_data.bXYZ": "来自 tag_data.bXYZ",
    "inverse(chad) * primary": "inverse(chad) * primary",
    "inverse(chad) * wtpt": "inverse(chad) * wtpt",
    "inverse(chad) * illuminant_xyz": "inverse(chad) * illuminant_xyz",
    "wtpt (no chad)": "wtpt（无 chad）",
    "Device / Color Encoding -> PCS": "设备/颜色编码 -> PCS",
    "PCS -> Device / Color Encoding": "PCS -> 设备/颜色编码",
    "Device RGB -> PCSXYZ": "设备 RGB -> PCSXYZ",
    "PCSXYZ -> Device RGB": "PCSXYZ -> 设备 RGB",
    "Device -> Device": "设备 -> 设备",
    "Common RGB matrix profile": "常见 RGB 矩阵 profile",
    "Device RGB -> TRC -> Matrix -> PCSXYZ": "设备 RGB -> TRC -> 矩阵 -> PCSXYZ",
    "PCSXYZ -> inverse Matrix -> inverse TRC -> Device RGB": "PCSXYZ -> 逆矩阵 -> 逆 TRC -> 设备 RGB",
    "Matrix/TRC profiles are usually reversible when matrix and TRCs are valid.": "当矩阵和 TRC 有效时，Matrix/TRC profile 通常可逆。",
    "multiProcessElements-like tag type detected.": "检测到类似 multiProcessElements 的标签类型。",
    "CLUT and matrix components detected.": "检测到 CLUT 和矩阵组件。",
    "CLUT component detected.": "检测到 CLUT 组件。",
    "Matrix component detected.": "检测到矩阵组件。",
    "Curve component detected.": "检测到曲线组件。",
}


def normalize_language(language: str) -> str:
    """Return a supported language code."""
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def tr(key: str, language: str = DEFAULT_LANGUAGE) -> Any:
    """Return translated UI text by key."""
    lang = normalize_language(language)
    return TEXTS.get(lang, TEXTS[DEFAULT_LANGUAGE]).get(key, TEXTS[DEFAULT_LANGUAGE].get(key, key))


def tr_display(value: Any, language: str = DEFAULT_LANGUAGE) -> str:
    """Translate common table/plot display strings while preserving raw data."""
    text = "" if value is None else str(value)
    if normalize_language(language) != "zh" or not text:
        return text

    if text in DISPLAY_TEXTS_ZH:
        return DISPLAY_TEXTS_ZH[text]
    if text.startswith("Missing "):
        return text.replace("Missing ", "缺少 ", 1)

    translated = text
    for source, target in sorted(DISPLAY_TEXTS_ZH.items(), key=lambda item: len(item[0]), reverse=True):
        translated = translated.replace(source, target)
    translated = translated.replace(" input -> ", " 输入 -> ").replace(" output", " 输出")
    translated = translated.replace("bytes", "字节").replace("items", "项").replace("chars", "字符")
    return translated
