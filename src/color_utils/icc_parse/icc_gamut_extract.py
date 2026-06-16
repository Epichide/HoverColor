"""Extract gamut visualization data from parsed ICC profile dictionaries.

This module contains no GUI dependencies. It prepares RGB primary points,
white points, and optional inverse-chad source estimates for the Gamut tab.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from icc_summary_extract import (
        WHITE_ILLUMINANTS_XY,
        _as_dict,
        _estimate_source_white_point,
        _extract_xyz_values,
        _field_value,
        _format_xy,
        _format_xyz,
        _get_near_illuminant,
        _header_value,
        _invert_3x3,
        _matrix3x3_from_values,
        _multiply_matrix_vector,
        _xyz_to_xy,
    )
except ImportError:
    from .icc_summary_extract import (
        WHITE_ILLUMINANTS_XY,
        _as_dict,
        _estimate_source_white_point,
        _extract_xyz_values,
        _field_value,
        _format_xy,
        _format_xyz,
        _get_near_illuminant,
        _header_value,
        _invert_3x3,
        _matrix3x3_from_values,
        _multiply_matrix_vector,
        _xyz_to_xy,
    )


PRIMARY_TAGS = (("rXYZ", "Red", "#e53935"), ("gXYZ", "Green", "#43a047"), ("bXYZ", "Blue", "#1e88e5"))


def build_gamut_data(parsed_data: dict) -> Dict[str, Any]:
    """Extract gamut plot data and table rows from parsed ICC data.

    Args:
        parsed_data: Parsed ICC dictionary produced by parse_icc_binary or JSON import.

    Returns:
        Dictionary containing PCS primary points, optional estimated source
        primary points, white points, and table rows.
    """
    header = parsed_data.get("header", {})
    tag_data = parsed_data.get("tag_data", {})
    chad_values = _field_value(_as_dict(tag_data.get("chad")).get("values"))
    inverse_chad = _get_inverse_chad(chad_values)

    pcs_points = []
    source_points = []
    rows = []

    for tag_name, label, color in PRIMARY_TAGS:
        xyz = _extract_xyz_values(tag_data.get(tag_name))
        if not xyz:
            continue
        xy = _xyz_to_xy(xyz)
        pcs_points.append({"tag": tag_name, "label": label, "xyz": xyz, "xy": xy, "color": color})
        rows.append(_table_row(f"{label} Primary (PCS/D50)", xyz, xy, f"from tag_data.{tag_name}"))

        source_xyz = _adapt_by_inverse_chad(xyz, inverse_chad)
        if source_xyz:
            source_xy = _xyz_to_xy(source_xyz)
            source_points.append({"tag": tag_name, "label": label, "xyz": source_xyz, "xy": source_xy, "color": color})
            rows.append(_table_row(f"{label} Primary (Estimated Source)", source_xyz, source_xy, "inverse(chad) * primary"))

    media_white_xyz = _extract_xyz_values(tag_data.get("wtpt"))
    media_white = None
    if media_white_xyz:
        media_white_xy = _xyz_to_xy(media_white_xyz)
        media_white = {"xyz": media_white_xyz, "xy": media_white_xy}
        rows.append(_table_row("Media White Point", media_white_xyz, media_white_xy, _join_note("PCS (D50)", _get_near_illuminant(media_white_xy))))

    header_illuminant_xyz = _header_value(header, "illuminant_xyz")
    source_white_xyz = _estimate_source_white_point(header_illuminant_xyz, media_white_xyz, chad_values)
    source_white = None
    if source_white_xyz:
        source_white_xy = _xyz_to_xy(source_white_xyz)
        source_white = {"xyz": source_white_xyz, "xy": source_white_xy}
        source_note = "inverse(chad) * illuminant_xyz" if inverse_chad else "wtpt (no chad)"
        rows.append(_table_row("Estimated Source White Point", source_white_xyz, source_white_xy, _join_note(source_note, _get_near_illuminant(source_white_xy))))

    return {
        "pcs_points": pcs_points,
        "source_points": source_points,
        "media_white": media_white,
        "source_white": source_white,
        "rows": rows,
    }


def _get_inverse_chad(chad_values: Any) -> Optional[List[List[float]]]:
    """Return inverse chad matrix when available."""
    matrix = _matrix3x3_from_values(chad_values)
    if matrix is None:
        return None
    return _invert_3x3(matrix)


def _adapt_by_inverse_chad(xyz: Sequence[float], inverse_chad: Optional[Sequence[Sequence[float]]]) -> Optional[Tuple[float, float, float]]:
    """Estimate source XYZ by applying inverse chad to an adapted XYZ value."""
    if inverse_chad is None:
        return None
    return _multiply_matrix_vector(inverse_chad, xyz)


def _table_row(item: str, xyz: Sequence[float], xy: Optional[Tuple[float, float]], note: str) -> Dict[str, str]:
    """Create one row for the gamut detail table."""
    return {
        "item": item,
        "xyz": _format_xyz(xyz),
        "xy": _format_xy(xy),
        "note": note,
    }


def _join_note(*parts: str) -> str:
    """Join non-empty note fragments."""
    return "; ".join(part for part in parts if part)
