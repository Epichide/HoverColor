"""Infer ICC conversion chain figures from parsed ICC profile data.

The extractor maps parsed tags such as A2B*, B2A*, matrix/TRC tags, and
DeviceLink-like structures to explanatory figures stored in
resource/ICC-Conversion-Chain. It returns plain dictionaries so the logic can
be tested without Qt.
"""

from typing import Any, Dict, List, Optional

try:
    from icc_summary_extract import _as_dict, _field_value
except ImportError:
    from .icc_summary_extract import _as_dict, _field_value


INTENT_NAMES = {
    "0": "Perceptual",
    "1": "Media-relative Colorimetric",
    "2": "Saturation",
}

A_TO_B_TAGS = ("A2B0", "A2B1", "A2B2")
B_TO_A_TAGS = ("B2A0", "B2A1", "B2A2")
D_TO_B_TAGS = ("D2B0", "D2B1", "D2B2", "D2B3")
B_TO_D_TAGS = ("B2D0", "B2D1", "B2D2", "B2D3")
RGB_PRIMARY_TAGS = {"rXYZ", "gXYZ", "bXYZ"}
RGB_TRC_TAGS = {"rTRC", "gTRC", "bTRC"}


def build_conversion_chains(parsed_data: dict) -> List[Dict[str, str]]:
    """Build conversion-chain rows from parsed ICC data.

    Args:
        parsed_data: Parsed ICC dictionary produced by parse_icc_binary or JSON import.

    Returns:
        List of rows with direction, tag, intent, figure, title, and reason.
    """
    header = parsed_data.get("header", {})
    tags = parsed_data.get("tags", {})
    tag_data = parsed_data.get("tag_data", {})
    device_class = _header_value(header, "device_class")

    rows: List[Dict[str, str]] = []
    if device_class == "link":
        rows.extend(_build_device_link_rows(tags, tag_data))
        if rows:
            return rows

    to_pcs_direction = _profile_direction(header, True)
    from_pcs_direction = _profile_direction(header, False)
    device_space = _space_name(_header_value(header, "color_space"), "RGB")
    pcs_space = _space_name(_header_value(header, "pcs"), "XYZ")
    rows.extend(_build_tag_direction_rows(A_TO_B_TAGS, tags, tag_data, to_pcs_direction, "AToB"))
    rows.extend(_build_tag_direction_rows(B_TO_A_TAGS, tags, tag_data, from_pcs_direction, "BToA"))
    rows.extend(_build_tag_direction_rows(D_TO_B_TAGS, tags, tag_data, to_pcs_direction, "DToB"))
    rows.extend(_build_tag_direction_rows(B_TO_D_TAGS, tags, tag_data, from_pcs_direction, "BToD"))

    if _has_matrix_trc(tags, tag_data):
        rows.append(_chain_row(
            to_pcs_direction,
            "Matrix/TRC",
            "Common RGB matrix profile",
            "figure3a_device_to_pcs_matrix_trc.jpg",
            f"{device_space} -> TRC -> Matrix -> {pcs_space}",
            "rXYZ/gXYZ/bXYZ and rTRC/gTRC/bTRC are present.",
        ))
        rows.append(_chain_row(
            from_pcs_direction,
            "Matrix/TRC",
            "Common RGB matrix profile",
            "figure2a_pcs_to_device_matrix_trc.jpg",
            f"{pcs_space} -> inverse Matrix -> inverse TRC -> {device_space}",
            "Matrix/TRC profiles are usually reversible when matrix and TRCs are valid.",
        ))

    if not rows:
        rows.append(_chain_row(
            "Unknown",
            "",
            "",
            "",
            "No matching conversion chain figure",
            "No A2B/B2A/D2B/B2D, matrix/TRC, or DeviceLink chain was detected.",
        ))
    return rows


def _build_tag_direction_rows(tag_names: tuple, tags: dict, tag_data: dict, direction: str, family: str) -> List[Dict[str, str]]:
    """Build rows for one tag family and direction."""
    rows = []
    for tag_name in tag_names:
        if tag_name not in tags and tag_name not in tag_data:
            continue
        tag_type = _tag_type(tags, tag_data, tag_name)
        pipeline = _as_dict(tag_data.get(tag_name))
        figure, title, reason = _select_direction_figure(family, tag_type, pipeline)
        rows.append(_chain_row(direction, tag_name, _intent_from_tag(tag_name), figure, title, reason))
    return rows


def _build_device_link_rows(tags: dict, tag_data: dict) -> List[Dict[str, str]]:
    """Build DeviceLink rows using Figure 5 mappings."""
    candidate_tags = [tag for tag in A_TO_B_TAGS + D_TO_B_TAGS if tag in tags or tag in tag_data]
    if not candidate_tags:
        figure, title, reason = _select_device_link_figure("", {})
        return [_chain_row("Device -> Device", "DeviceLink", "DeviceLink transform", figure, title, reason)]

    rows = []
    for tag_name in candidate_tags:
        tag_type = _tag_type(tags, tag_data, tag_name)
        pipeline = _as_dict(tag_data.get(tag_name))
        figure, title, reason = _select_device_link_figure(tag_type, pipeline)
        rows.append(_chain_row("Device -> Device", tag_name, _intent_from_tag(tag_name), figure, title, reason))
    return rows


def _select_direction_figure(family: str, tag_type: str, pipeline: dict) -> tuple:
    """Select Figure 2/3 image for AToB/BToA-like tags."""
    is_to_pcs = family in {"AToB", "DToB"}
    if tag_type in {"mpet", "mpE "}:
        figure = "figure3f_device_to_pcs_multiProcessElements.jpg" if is_to_pcs else "figure2f_pcs_to_device_multiProcessElements.jpg"
        title = "Device -> process elements -> PCS" if is_to_pcs else "PCS -> process elements -> Device"
        return figure, title, "multiProcessElements-like tag type detected."

    has_matrix = _has_component(pipeline, "matrix", "offset_matrix")
    has_clut = _has_component(pipeline, "clut", "offset_clut")
    has_a_curve = _has_component(pipeline, "a_curve", "offset_a_curve")
    has_b_curve = _has_component(pipeline, "b_curve", "offset_b_curve")
    has_m_curve = _has_component(pipeline, "m_curve", "offset_m_curve")
    channels = _channel_count_for_family(family, pipeline)

    if is_to_pcs:
        if has_clut and has_matrix:
            return (
                "figure3e_device_to_pcs_lutAToB.jpg",
                'Device -> "A" curves -> CLUT -> "M" curves -> Matrix -> "B" curves -> PCS',
                _component_reason(tag_type, has_a_curve, has_b_curve, has_m_curve, has_matrix, has_clut),
            )
        if has_clut:
            figure = "figure3d_device_to_pcs_lutAToB.jpg" if channels and channels != 3 else "figure3c_device_to_pcs_lutAToB.jpg"
            title = 'Device channels 1..n -> "A" curves -> CLUT -> "B" curves -> PCS' if channels and channels != 3 else 'Device -> "A" curves -> CLUT -> "B" curves -> PCS'
            return figure, title, _component_reason(tag_type, has_a_curve, has_b_curve, has_m_curve, has_matrix, has_clut)
        return (
            "figure3b_device_to_pcs_lutAToB.jpg",
            'Device -> "A" curves -> Matrix -> "M" curves -> "B" curves -> PCS',
            _component_reason(tag_type, has_a_curve, has_b_curve, has_m_curve, has_matrix, has_clut),
        )

    if has_clut and has_matrix:
        return (
            "figure2e_pcs_to_device_lutBToA.jpg",
            'PCS -> "B" curves -> Matrix -> "M" curves -> CLUT -> "A" curves -> Device',
            _component_reason(tag_type, has_a_curve, has_b_curve, has_m_curve, has_matrix, has_clut),
        )
    if has_clut:
        figure = "figure2d_pcs_to_device_lutBToA.jpg" if channels and channels != 3 else "figure2c_pcs_to_device_lutBToA.jpg"
        title = 'PCS -> "B" curves -> CLUT -> "A" curves -> Device channels 1..n' if channels and channels != 3 else 'PCS -> "B" curves -> CLUT -> "A" curves -> Device'
        return figure, title, _component_reason(tag_type, has_a_curve, has_b_curve, has_m_curve, has_matrix, has_clut)
    return (
        "figure2b_pcs_to_device_lutBToA.jpg",
        'PCS -> "B" curves -> Matrix -> "M" curves -> "A" curves -> Device',
        _component_reason(tag_type, has_a_curve, has_b_curve, has_m_curve, has_matrix, has_clut),
    )


def _select_device_link_figure(tag_type: str, pipeline: dict) -> tuple:
    """Select Figure 5 image for DeviceLink profile chains."""
    if tag_type in {"mpet", "mpE "}:
        return "figure5e_device_to_device_multiProcessElements.jpg", "Source Device -> process elements -> Destination Device", "multiProcessElements-like tag type detected."

    has_matrix = _has_component(pipeline, "matrix", "offset_matrix")
    has_clut = _has_component(pipeline, "clut", "offset_clut")
    has_curve = any(_has_component(pipeline, key, offset_key) for key, offset_key in (
        ("a_curve", "offset_a_curve"),
        ("b_curve", "offset_b_curve"),
        ("m_curve", "offset_m_curve"),
    ))
    if has_clut and has_matrix:
        return "figure5d_device_to_device_clut_matrix_trc.jpg", "Source Device -> CLUT -> Matrix -> TRC -> Destination Device", "CLUT and matrix components detected."
    if has_clut:
        return "figure5c_device_to_device_clut_trc.jpg", "Source Device -> CLUT -> TRC -> Destination Device", "CLUT component detected."
    if has_matrix:
        return "figure5b_device_to_device_matrix_trc.jpg", "Source Device -> TRC -> Matrix -> Destination Device", "Matrix component detected."
    if has_curve:
        return "figure5a_device_to_device_trc.jpg", "Source Device channel -> TRC -> Destination Device channel", "Curve component detected."
    return "figure5e_device_to_device_multiProcessElements.jpg", "Source Device -> Destination Device", "DeviceLink profile class detected; detailed components were not parsed."


def _has_matrix_trc(tags: dict, tag_data: dict) -> bool:
    """Return whether classic RGB matrix/TRC tags are present."""
    keys = set(tags.keys()) | set(tag_data.keys())
    return RGB_PRIMARY_TAGS.issubset(keys) and RGB_TRC_TAGS.issubset(keys)


def _has_component(pipeline: dict, data_key: str, offset_key: str) -> bool:
    """Return whether a pipeline component is present."""
    component = pipeline.get(data_key)
    if isinstance(component, dict) and component:
        return True
    if component not in (None, "", [], {}):
        return True
    return bool(_field_value(pipeline.get(offset_key), 0))


def _channel_count_for_family(family: str, pipeline: dict) -> Optional[int]:
    """Return device-side channel count for choosing RGB vs n-channel figures."""
    if family in {"AToB", "DToB"}:
        value = _field_value(pipeline.get("input_channels"), 0)
    else:
        value = _field_value(pipeline.get("output_channels"), 0)
    return int(value) if isinstance(value, int) and value > 0 else None


def _component_reason(tag_type: str, has_a_curve: bool, has_b_curve: bool, has_m_curve: bool, has_matrix: bool, has_clut: bool) -> str:
    """Build a compact component summary."""
    components = []
    if has_a_curve:
        components.append("A curves")
    if has_b_curve:
        components.append("B curves")
    if has_m_curve:
        components.append("M curves")
    if has_matrix:
        components.append("Matrix")
    if has_clut:
        components.append("CLUT")
    component_text = ", ".join(components) if components else "no parsed optional component"
    return f"type={tag_type or 'unknown'}; components: {component_text}."


def _tag_type(tags: dict, tag_data: dict, tag_name: str) -> str:
    """Read tag type from tag table or parsed payload."""
    tag_entry = _as_dict(tags.get(tag_name))
    tag_type = tag_entry.get("type")
    if tag_type:
        return str(tag_type)
    parsed = _as_dict(tag_data.get(tag_name))
    return str(_field_value(parsed.get("type_signature"), parsed.get("datatype", "")))


def _intent_from_tag(tag_name: str) -> str:
    """Map A2B/B2A intent suffix to user-facing rendering intent."""
    suffix = tag_name[-1:] if tag_name else ""
    return INTENT_NAMES.get(suffix, "")


def _header_value(header: dict, field_name: str) -> Any:
    """Read a header value from the [value, offset, bytesize, datatype, datasize] layout."""
    value = header.get(field_name, "")
    if isinstance(value, list) and value:
        return value[0]
    return value


def _profile_direction(header: dict, to_pcs: bool) -> str:
    """Build an explicit profile direction such as RGB -> Lab from header spaces."""
    device_space = _space_name(_header_value(header, "color_space"), "Device")
    pcs_space = _space_name(_header_value(header, "pcs"), "PCS")
    return f"{device_space} -> {pcs_space}" if to_pcs else f"{pcs_space} -> {device_space}"


def _space_name(value: Any, fallback: str) -> str:
    """Normalize ICC space signatures for compact direction labels."""
    signature = str(value or "").strip()
    if not signature:
        return fallback
    names = {
        "RGB": "RGB",
        "CMYK": "CMYK",
        "CMY": "CMY",
        "GRAY": "Gray",
        "XYZ": "XYZ",
        "Lab": "Lab",
        "Luv": "Luv",
        "YCbr": "YCbCr",
        "Yxy": "Yxy",
        "HSV": "HSV",
        "HLS": "HLS",
    }
    return names.get(signature, signature)


def _chain_row(direction: str, tag: str, intent: str, figure: str, title: str, reason: str) -> Dict[str, str]:
    """Create one conversion-chain row."""
    return {
        "direction": str(direction),
        "tag": str(tag),
        "intent": str(intent),
        "figure": str(figure),
        "title": str(title),
        "reason": str(reason),
    }
