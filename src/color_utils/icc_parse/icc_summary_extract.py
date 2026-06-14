"""Extract concise ICC profile summary rows from parsed ICC data.

This module keeps interpretation logic outside the main inspector window. It
turns parsed ICC JSON-compatible data into rows that are easier to read in a
summary UI, including small derived values such as xy chromaticity.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple


PARSED_FIELD_REQUIRED_KEYS = {"value", "offset", "bytesize", "datatype"}
PARSED_FIELD_ALLOWED_KEYS = PARSED_FIELD_REQUIRED_KEYS | {"datasize"}

DEVICE_CLASS_NAMES = {
    "scnr": "Scanner",
    "mntr": "Display/Monitor",
    "prtr": "Printer",
    "link": "DeviceLink",
    "spac": "ColorSpace",
    "abst": "Abstract",
    "nmcl": "NamedColor",
}

RENDERING_INTENT_NAMES = {
    0: "Perceptual",
    1: "Media-relative Colorimetric",
    2: "Saturation",
    3: "ICC-absolute Colorimetric",
}

WHITE_ILLUMINANTS_XY = {
    "A": (0.44758, 0.40745),
    "B": (0.34842, 0.35161),
    "C": (0.31006, 0.31616),
    "D50": (0.34567, 0.35850),
    "D55": (0.33242, 0.34743),
    "D60": (0.32168, 0.33767),
    "D63": (0.31400, 0.35100),
    "D65": (0.31272, 0.32903),
    "D75": (0.29902, 0.31485),
    "D93": (0.28315, 0.29711),
    "E": (0.33333, 0.33333),
    "F1": (0.31310, 0.33727),
    "F2": (0.37208, 0.37529),
    "F3": (0.40910, 0.39430),
    "F4": (0.44018, 0.40329),
    "F5": (0.31379, 0.34531),
    "F6": (0.37790, 0.38835),
    "F7": (0.31292, 0.32933),
    "F8": (0.34588, 0.35875),
    "F9": (0.37417, 0.37281),
    "F10": (0.34609, 0.35986),
    "F11": (0.38052, 0.37713),
    "F12": (0.43695, 0.40441),
    "LED-B1": (0.45600, 0.40780),
    "LED-B2": (0.43570, 0.40120),
    "LED-B3": (0.37560, 0.37230),
    "LED-B4": (0.34220, 0.35020),
    "LED-B5": (0.31180, 0.32360),
    "LED-BH1": (0.44740, 0.40660),
    "LED-RGB1": (0.45570, 0.42110),
    "LED-V1": (0.45600, 0.45480),
    "LED-V2": (0.37810, 0.37750),
}


def build_icc_summary(parsed_data: dict) -> List[Dict[str, str]]:
    """Build user-facing ICC summary rows from parsed data.

    Args:
        parsed_data: Parsed ICC dictionary produced by parse_icc_binary or JSON import.

    Returns:
        A list of row dictionaries with section, item, value, source, note, and visualizable keys.
    """
    rows: List[Dict[str, str]] = []
    header = parsed_data.get("header", {})
    tags = parsed_data.get("tags", {})
    tag_data = parsed_data.get("tag_data", {})

    _append_general_rows(rows, parsed_data, header, tag_data)
    _append_metadata_rows(rows, parsed_data, tag_data)
    _append_colorimetry_rows(rows, header, tag_data)
    _append_trc_rows(rows, tag_data, tags)
    _append_pipeline_rows(rows, tag_data)
    _append_notes(rows, tags, tag_data)
    return rows


def _append_general_rows(rows: List[Dict[str, str]], parsed_data: dict, header: dict, tag_data: dict) -> None:
    """Append profile identity and header summary rows."""
    description = _extract_localized_text(tag_data.get("desc")) or _extract_text_value(tag_data.get("desc"))
    if description:
        rows.append(_row("General", "Profile Description", description, "tag_data.desc", ""))

    device_class = _header_value(header, "device_class")
    rows.append(_row("General", "Device Class", _format_code_with_name(device_class, DEVICE_CLASS_NAMES), "header.device_class", ""))
    rows.append(_row("General", "Color Space", _header_value(header, "color_space"), "header.color_space", ""))
    rows.append(_row("General", "PCS", _header_value(header, "pcs"), "header.pcs", "Profile Connection Space"))
    rows.append(_row("General", "ICC Version", _header_value(header, "version"), "header.version", ""))

    intent = _header_value(header, "rendering_intent")
    rows.append(_row("General", "Rendering Intent", _format_code_with_name(intent, RENDERING_INTENT_NAMES), "header.rendering_intent", ""))
    rows.append(_row("General", "Profile Size", f"{parsed_data.get('file_size', 0)} bytes", "file_size", ""))
    rows.append(_row("General", "Tag Count", parsed_data.get("tag_count", len(parsed_data.get("tags", {}))), "tag_count", ""))


def _append_metadata_rows(rows: List[Dict[str, str]], parsed_data: dict, tag_data: dict) -> None:
    """Append copyright and creator rows."""
    copyright_text = _extract_localized_text(tag_data.get("cprt")) or _extract_text_value(tag_data.get("cprt"))
    if copyright_text:
        rows.append(_row("Metadata", "Copyright", copyright_text, "tag_data.cprt", ""))

    creator = _header_value(parsed_data.get("header", {}), "creator")
    if creator:
        rows.append(_row("Metadata", "Creator", creator, "header.creator", ""))


def _append_colorimetry_rows(rows: List[Dict[str, str]], header: dict, tag_data: dict) -> None:
    """Append white point, primaries, and adaptation matrix rows."""
    media_white_point = _extract_xyz_values(tag_data.get("wtpt"))
    chad_values = _field_value(_as_dict(tag_data.get("chad")).get("values"))
    header_illuminant = _header_value(header, "illuminant_xyz")
    pcs_white_point = tuple(float(value) for value in header_illuminant) if _is_xyz_triplet(header_illuminant) else None
    source_white = _estimate_source_white_point(pcs_white_point, media_white_point, chad_values)

    _append_white_point_rows(rows, media_white_point, source_white, pcs_white_point, bool(_matrix3x3_from_values(chad_values)))

    black_point = _extract_xyz_values(tag_data.get("bkpt"))
    if black_point:
        near_illuminant = _get_near_illuminant(_xyz_to_xy(black_point))
        rows.append(_row("Colorimetry", "Black Point", _format_xyz(black_point), "tag_data.bkpt", near_illuminant, "illuminant"))
        rows.append(_row("Colorimetry", "Black Point xy", _format_xy(_xyz_to_xy(black_point)), "tag_data.bkpt", "Derived from Black Point XYZ"))

    for tag_name, label in (("rXYZ", "Red Primary"), ("gXYZ", "Green Primary"), ("bXYZ", "Blue Primary")):
        xyz = _extract_xyz_values(tag_data.get(tag_name))
        if xyz:
            rows.append(_row("RGB Primaries", label, _format_xyz(xyz), f"tag_data.{tag_name}", "", "illuminant"))
            rows.append(_row("RGB Primaries", f"{label} xy", _format_xy(_xyz_to_xy(xyz)), f"tag_data.{tag_name}", "Derived from XYZ"))

    if isinstance(chad_values, list) and chad_values:
        rows.append(_row("Colorimetry", "Chromatic Adaptation Matrix", _format_matrix(chad_values, 3, 3), "tag_data.chad.values", "Adapts estimated source/adopted white to PCS white", "matrix"))


def _append_white_point_rows(
    rows: List[Dict[str, str]],
    media_white_point: Optional[Tuple[float, float, float]],
    source_white: Optional[Tuple[float, float, float]],
    pcs_white_point: Optional[Tuple[float, float, float]],
    has_chad: bool,
) -> None:
    """Append related white point rows together with distinct ICC meanings."""
    if media_white_point:
        near_illuminant = _get_near_illuminant(_xyz_to_xy(media_white_point))
        note = _join_notes("Media white from wtpt tag; not necessarily PCS white", near_illuminant)
        rows.append(_row("Colorimetry", "Media White Point", _format_xyz(media_white_point), "tag_data.wtpt", note, "illuminant"))
        rows.append(_row("Colorimetry", "Media White Point xy", _format_xy(_xyz_to_xy(media_white_point)), "tag_data.wtpt", "Derived from Media White Point XYZ"))

    if source_white:
        near_illuminant = _get_near_illuminant(_xyz_to_xy(source_white))
        source_note = "Estimated adopted/source white by inverse(chad) * PCS White Point" if has_chad else "No chad; approximated from wtpt media white"
        rows.append(_row(
            "Colorimetry",
            "Estimated Source White Point",
            _format_xyz(source_white),
            "header.illuminant_xyz + tag_data.chad.values" if has_chad else "tag_data.wtpt",
            _join_notes(source_note, near_illuminant),
            "illuminant",
        ))
        rows.append(_row(
            "Colorimetry",
            "Estimated Source White Point xy",
            _format_xy(_xyz_to_xy(source_white)),
            "header.illuminant_xyz + tag_data.chad.values" if has_chad else "tag_data.wtpt",
            "Derived from Estimated Source White Point XYZ",
        ))

    if pcs_white_point:
        near_illuminant = _get_near_illuminant(_xyz_to_xy(pcs_white_point))
        note = _join_notes("PCS illuminant from ICC header; ICC PCS white is normally D50", near_illuminant)
        rows.append(_row("Colorimetry", "PCS White Point", _format_xyz(pcs_white_point), "header.illuminant_xyz", note, "illuminant"))
        rows.append(_row("Colorimetry", "PCS White Point xy", _format_xy(_xyz_to_xy(pcs_white_point)), "header.illuminant_xyz", "Derived from PCS White Point XYZ"))


def _append_trc_rows(rows: List[Dict[str, str]], tag_data: dict, tags: dict) -> None:
    """Append tone response curve rows."""
    for tag_name, label in (("rTRC", "Red TRC"), ("gTRC", "Green TRC"), ("bTRC", "Blue TRC")):
        trc = _as_dict(tag_data.get(tag_name))
        tag_type = _as_dict(tags.get(tag_name)).get("type") or trc.get("datatype")
        if not trc and not tag_type:
            continue

        value, note = _summarize_curve(trc, tag_type)
        rows.append(_row("TRC", label, value, f"tag_data.{tag_name}", note, "curve"))


def _append_pipeline_rows(rows: List[Dict[str, str]], tag_data: dict) -> None:
    """Append A2B/B2A pipeline availability and CLUT summary rows."""
    for tag_name in ("A2B0", "A2B1", "A2B2", "B2A0", "B2A1", "B2A2"):
        pipeline = _as_dict(tag_data.get(tag_name))
        if not pipeline:
            continue

        input_channels = _field_value(pipeline.get("input_channels"), pipeline.get("input_channels", ""))
        output_channels = _field_value(pipeline.get("output_channels"), pipeline.get("output_channels", ""))
        rows.append(_row("Pipeline", tag_name, f"{input_channels} input -> {output_channels} output", f"tag_data.{tag_name}", ""))

        clut = _as_dict(pipeline.get("clut"))
        if clut:
            grid_points = _field_value(clut.get("grid_points"), [])
            precision = _field_value(clut.get("precision"), "")
            value_count = _field_value(_as_dict(clut.get("values")).get("datasize"), "")
            if not value_count:
                values = _field_value(clut.get("values"), [])
                value_count = len(values) if isinstance(values, list) else ""
            rows.append(_row(
                "Pipeline",
                f"{tag_name} CLUT",
                f"grid={_format_number_list(grid_points)}, precision={precision}, values={value_count}",
                f"tag_data.{tag_name}.clut",
                "Double-click visualization planned",
                "lut",
            ))

        matrix = _as_dict(pipeline.get("matrix"))
        matrix_values = _field_value(matrix.get("values"), matrix.get("matrix", []))
        if matrix_values:
            rows.append(_row("Pipeline", f"{tag_name} Matrix", _format_pipeline_matrix(matrix_values), f"tag_data.{tag_name}.matrix", "Double-click visualization planned", "matrix"))


def _append_notes(rows: List[Dict[str, str]], tags: dict, tag_data: dict) -> None:
    """Append useful notes and lightweight warnings."""
    for required_tag, description in (
        ("desc", "Profile description tag"),
        ("wtpt", "Media white point tag"),
        ("cprt", "Copyright tag"),
    ):
        if required_tag not in tags and required_tag not in tag_data:
            rows.append(_row("Notes", f"Missing {required_tag}", description, required_tag, "Not found in this profile"))

    rgb_tags = {"rXYZ", "gXYZ", "bXYZ"}
    if rgb_tags.issubset(tags.keys()):
        rows.append(_row("Notes", "RGB Primary Tags", "rXYZ/gXYZ/bXYZ are present", "tags", "Can derive xy primaries"))


def _row(section: str, item: str, value: Any, source: str, note: str = "", visualizable: str = "") -> Dict[str, str]:
    """Create one summary row dictionary."""
    return {
        "section": str(section),
        "item": str(item),
        "value": _format_value(value),
        "source": str(source),
        "note": str(note),
        "visualizable": str(visualizable),
    }


def _is_parsed_field(value: Any) -> bool:
    """Return whether value is a single ParsedField-like wrapper."""
    if not isinstance(value, dict):
        return False
    return PARSED_FIELD_REQUIRED_KEYS.issubset(value.keys()) and set(value.keys()).issubset(PARSED_FIELD_ALLOWED_KEYS)


def _field_value(value: Any, default: Any = "") -> Any:
    """Return the payload of a ParsedField wrapper or the original value."""
    if _is_parsed_field(value):
        return value.get("value", default)
    if isinstance(value, dict) and "value" in value:
        return value.get("value", default)
    return value if value is not None else default


def _as_dict(value: Any) -> dict:
    """Return value if it is a dict, otherwise an empty dict."""
    return value if isinstance(value, dict) else {}


def _header_value(header: dict, field_name: str) -> Any:
    """Read a header value from the [value, offset, bytesize, datatype, datasize] layout."""
    value = header.get(field_name, "")
    if isinstance(value, list) and value:
        return value[0]
    return value


def _extract_localized_text(tag: Any) -> str:
    """Extract the first localized text record, preferring English records."""
    tag_dict = _as_dict(tag)
    records = tag_dict.get("records", [])
    if not isinstance(records, list):
        return ""

    selected_record = None
    for record in records:
        record_dict = _as_dict(record)
        if _field_value(record_dict.get("language_code")) == "en":
            selected_record = record_dict
            break
    if selected_record is None and records:
        selected_record = _as_dict(records[0])
    return _field_value(selected_record.get("text"), "") if selected_record else ""


def _extract_text_value(tag: Any) -> str:
    """Extract text from common text-like tag structures."""
    tag_dict = _as_dict(tag)
    for key in ("text", "description", "ascii_description", "unicode_description", "script_code_description", "value"):
        value = _field_value(tag_dict.get(key))
        if isinstance(value, str) and value:
            return value
    return ""


def _extract_xyz_values(tag: Any) -> Optional[Tuple[float, float, float]]:
    """Extract the first XYZ triple from XYZ tag data."""
    tag_dict = _as_dict(tag)
    value = _field_value(tag_dict.get("value"))
    if _is_xyz_triplet(value):
        return tuple(float(item) for item in value)

    values = _field_value(tag_dict.get("values"))
    if isinstance(values, list) and values:
        first = values[0]
        if _is_xyz_triplet(first):
            return tuple(float(item) for item in first)
    return None


def _is_xyz_triplet(value: Any) -> bool:
    """Return whether value looks like a numeric XYZ triple."""
    return isinstance(value, (list, tuple)) and len(value) == 3 and all(isinstance(item, (int, float)) for item in value)


def _xyz_to_xy(xyz: Sequence[float]) -> Optional[Tuple[float, float]]:
    """Convert XYZ to xy chromaticity coordinates."""
    total = sum(xyz)
    if total == 0:
        return None
    return float(xyz[0]) / total, float(xyz[1]) / total


def _get_near_illuminant(xy_value: Optional[Sequence[float]]) -> str:
    """Return the nearest named illuminant by xy Euclidean distance."""
    if xy_value is None:
        return ""

    nearest_name = ""
    min_distance = None
    x_value, y_value = float(xy_value[0]), float(xy_value[1])
    for illuminant, illuminant_xy in WHITE_ILLUMINANTS_XY.items():
        dx = x_value - illuminant_xy[0]
        dy = y_value - illuminant_xy[1]
        distance = (dx * dx + dy * dy) ** 0.5
        if min_distance is None or distance < min_distance:
            min_distance = distance
            nearest_name = illuminant

    return f"Near {nearest_name}" if nearest_name else ""


def _join_notes(*notes: str) -> str:
    """Join non-empty note fragments with semicolons."""
    return "; ".join(note for note in notes if note)


def _estimate_source_white_point(
    illuminant_xyz: Optional[Sequence[float]],
    wtpt_xyz: Optional[Sequence[float]],
    chad_values: Any,
) -> Optional[Tuple[float, float, float]]:
    """Estimate the pre-adaptation source white point.

    chad adapts the source/adopted white to the ICC PCS illuminant. When chad
    is available, use inverse(chad) * header.illuminant_xyz. Without chad, wtpt
    is the best available approximation of the source/media white.
    """
    matrix = _matrix3x3_from_values(chad_values)
    if matrix is None:
        return tuple(float(value) for value in wtpt_xyz) if wtpt_xyz is not None else None

    if illuminant_xyz is None:
        return None

    inverse_matrix = _invert_3x3(matrix)
    if inverse_matrix is None:
        return None

    return _multiply_matrix_vector(inverse_matrix, illuminant_xyz)


def _matrix3x3_from_values(values: Any) -> Optional[List[List[float]]]:
    """Convert a flat 9-number row-major list to a 3x3 matrix."""
    if not isinstance(values, list) or len(values) < 9:
        return None
    matrix_values = values[:9]
    if not all(isinstance(item, (int, float)) for item in matrix_values):
        return None
    return [
        [float(matrix_values[0]), float(matrix_values[1]), float(matrix_values[2])],
        [float(matrix_values[3]), float(matrix_values[4]), float(matrix_values[5])],
        [float(matrix_values[6]), float(matrix_values[7]), float(matrix_values[8])],
    ]


def _invert_3x3(matrix: Sequence[Sequence[float]]) -> Optional[List[List[float]]]:
    """Invert a 3x3 matrix without adding a heavy numeric dependency."""
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]

    determinant = (
        a * (e * i - f * h)
        - b * (d * i - f * g)
        + c * (d * h - e * g)
    )
    if abs(determinant) < 1e-12:
        return None

    inv_det = 1.0 / determinant
    return [
        [(e * i - f * h) * inv_det, (c * h - b * i) * inv_det, (b * f - c * e) * inv_det],
        [(f * g - d * i) * inv_det, (a * i - c * g) * inv_det, (c * d - a * f) * inv_det],
        [(d * h - e * g) * inv_det, (b * g - a * h) * inv_det, (a * e - b * d) * inv_det],
    ]


def _multiply_matrix_vector(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> Tuple[float, float, float]:
    """Multiply a 3x3 matrix by an XYZ vector."""
    x, y, z = float(vector[0]), float(vector[1]), float(vector[2])
    return (
        matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * z,
        matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * z,
        matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * z,
    )


def _summarize_curve(curve: dict, tag_type: Any) -> Tuple[str, str]:
    """Return a readable TRC expression and a type/parameter note."""
    tag_type_text = str(tag_type or _field_value(curve.get("type_signature"), curve.get("datatype", "")) or "")
    if tag_type_text == "para" or "function_type" in curve:
        function_type = int(_field_value(curve.get("function_type"), 0) or 0)
        parameters = _curve_parameter_values(curve)
        note = f"parametric type={function_type}; params={_format_number_list(parameters)}"
        return _resolved_parametric_formula(function_type, parameters), note

    count = int(_field_value(curve.get("count"), 0) or 0)
    curve_data = _field_value(curve.get("curve_data"), [])
    curve_values = curve_data if isinstance(curve_data, list) else []
    if count == 0:
        return "y = x", "curveType count=0; identity curve"
    if count == 1:
        gamma = _curve_gamma_value(curve, curve_values)
        return f"y = x^{_format_number(gamma)}", "curveType count=1; gamma curve"
    if curve_values:
        return "y = f(x)", f"curveType 1D sampled curve; points={len(curve_values)}, declared count={count}"
    return "y = f(x)", f"type={tag_type_text or 'unknown'}; count={count}"


def _curve_parameter_values(curve: dict) -> List[float]:
    """Read parametric curve parameters from parser list or dict layouts."""
    names = ["g", "a", "b", "c", "d", "e", "f"]
    raw_parameters = _field_value(curve.get("parameters"), [])
    if isinstance(raw_parameters, dict):
        return [_to_float(raw_parameters[name]) for name in names if name in raw_parameters]
    if isinstance(raw_parameters, list):
        return [_to_float(value) for value in raw_parameters]
    return []


def _resolved_parametric_formula(function_type: int, parameters: Sequence[float]) -> str:
    """Substitute numeric ICC parametric parameters into the selected formula."""
    params = list(parameters) + [0.0] * 7
    g, a, b, c, d, e, f = params[:7]
    base = f"({_format_number(a)}*x + {_format_number(b)})^{_format_number(g)}"
    if function_type == 0:
        return f"y = x^{_format_number(g)}"
    if function_type == 1:
        return f"y = {base} if {_format_threshold(b, a)} else 0"
    if function_type == 2:
        return f"y = {base} + {_format_number(c)} if {_format_threshold(b, a)} else {_format_number(c)}"
    if function_type == 3:
        return f"y = {base} if x >= {_format_number(d)} else {_format_number(c)}*x"
    if function_type == 4:
        return (
            f"y = {base} + {_format_number(e)} if x >= {_format_number(d)} "
            f"else {_format_number(c)}*x + {_format_number(f)}"
        )
    return "y = x"


def _curve_gamma_value(curve: dict, curve_values: Sequence[Any]) -> float:
    """Return gamma from either explicit gamma field or single curve entry."""
    gamma = _field_value(curve.get("gamma"), None)
    if gamma not in (None, ""):
        return _to_float(gamma)
    if curve_values:
        return _to_float(curve_values[0])
    return 1.0


def _format_threshold(b_value: float, a_value: float) -> str:
    """Format the parametric branch threshold, avoiding division by zero."""
    if a_value == 0:
        return "x >= -b/a"
    return f"x >= {_format_number(-b_value / a_value)}"


def _to_float(value: Any) -> float:
    """Convert parsed numeric-like values to float."""
    if isinstance(value, dict):
        return _to_float(_field_value(value, 0.0))
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _format_code_with_name(value: Any, name_map: dict) -> str:
    """Format an ICC enum code with a friendly name when known."""
    if value in name_map:
        return f"{value} ({name_map[value]})"
    return _format_value(value)


def _format_xyz(xyz: Sequence[float]) -> str:
    """Format XYZ triple."""
    return f"X={xyz[0]:.6f}, Y={xyz[1]:.6f}, Z={xyz[2]:.6f}"


def _format_xy(xy: Optional[Tuple[float, float]]) -> str:
    """Format xy chromaticity pair."""
    if xy is None:
        return ""
    return f"x={xy[0]:.6f}, y={xy[1]:.6f}"


def _format_number_list(values: Any, max_items: int = 12) -> str:
    """Format a numeric list with a compact preview."""
    if not isinstance(values, list):
        return _format_value(values)
    preview = ", ".join(_format_number(item) for item in values[:max_items])
    if len(values) > max_items:
        preview = f"{preview}, ... ({len(values)} items)"
    return f"[{preview}]"


def _format_number(value: Any) -> str:
    """Format a numeric value compactly for formulas."""
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return _format_value(value)


def _format_pipeline_matrix(values: Any) -> str:
    """Format a parsed pipeline matrix as 3x4 or 3x3 rows when possible."""
    if isinstance(values, list) and len(values) >= 12:
        return _format_matrix(_matrix_3x4_display_values(values[:12]), 3, 4)
    if isinstance(values, list) and len(values) >= 9:
        return _format_matrix(values[:9], 3, 3)
    return _format_number_list(values)


def _matrix_3x4_display_values(values: Sequence[float]) -> List[float]:
    """Return ICC mAB/mBA matrix values in visual 3x4 row-major order."""
    return [
        values[0], values[1], values[2], values[9],
        values[3], values[4], values[5], values[10],
        values[6], values[7], values[8], values[11],
    ]


def _format_matrix(values: Sequence[float], rows: int, columns: int) -> str:
    """Format matrix values as aligned multi-line rows."""
    if len(values) < rows * columns:
        return _format_number_list(list(values))
    lines = []
    for row in range(rows):
        start = row * columns
        row_values = values[start:start + columns]
        lines.append("[ " + "  ".join(f"{float(value): .6f}" for value in row_values) + " ]")
    return "\n".join(lines)


def _format_value(value: Any) -> str:
    """Format values for summary display."""
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, list):
        return _format_number_list(value)
    return str(value)
