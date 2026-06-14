"""ICC Profile 结构体定义（基于 ICC.1:2022 规范）"""

import struct
from dataclasses import dataclass
from typing import Tuple, List, Optional
from datetime import datetime


# ==================== 基础类型定义 ====================

# 基础数据类型 (格式, 字节数)
UINT8 = struct.Struct(">B")          # 1字节无符号
UINT16 = struct.Struct(">H")         # 2字节无符号
UINT32 = struct.Struct(">I")         # 4字节无符号
UINT64 = struct.Struct(">Q")         # 8字节无符号
INT32 = struct.Struct(">i")          # 4字节有符号

# 定点数类型
# u8Fixed8: 8.8定点数 (1字节整数 + 8位小数)
U8FIXED8 = struct.Struct(">B")       # 存储时只有整数，解析时除以256

# s15Fixed16: 15.16定点数 (1字节整数 + 16位小数)
S15FIXED16 = struct.Struct(">i")     # 存储时是有符号32位整数，解析时除以65536

# u1Fixed15: 1.15定点数 (用于介素)
U1FIXED15 = struct.Struct(">H")      # 存储时是16位，解析时除以32768


# ==================== 复合类型定义 ====================

class ICCTypes:
    """ICC数据类型工具类"""
    
    @staticmethod
    def unpack_uint8(data: bytes) -> int:
        return UINT8.unpack(data[0:1])[0]
    
    @staticmethod
    def unpack_uint16(data: bytes) -> int:
        return UINT16.unpack(data[0:2])[0]
    
    @staticmethod
    def unpack_uint32(data: bytes) -> int:
        return UINT32.unpack(data[0:4])[0]
    
    @staticmethod
    def unpack_int32(data: bytes) -> int:
        return INT32.unpack(data[0:4])[0]
    
    @staticmethod
    def unpack_s15fixed16(data: bytes) -> float:
        """解析s15Fixed16定点数 (15.16格式)"""
        raw = INT32.unpack(data[0:4])[0]
        return raw / 65536.0
    
    @staticmethod
    def unpack_u8fixed8(data: bytes) -> float:
        """解析u8Fixed8定点数 (8.8格式)"""
        raw = UINT8.unpack(data[0:1])[0]
        return raw / 256.0
    
    @staticmethod
    def unpack_u1fixed15(data: bytes) -> float:
        """解析u1Fixed15定点数 (1.15格式)"""
        raw = UINT16.unpack(data[0:2])[0]
        return raw / 32768.0
    
    @staticmethod
    def unpack_uint64(data: bytes) -> int:
        """解析uint64"""
        return UINT64.unpack(data[0:8])[0]
    
    @staticmethod
    def unpack_xyz(data: bytes) -> Tuple[float, float, float]:
        """解析XYZNumber (3个s15Fixed16)"""
        x = ICCTypes.unpack_s15fixed16(data[0:4])
        y = ICCTypes.unpack_s15fixed16(data[4:8])
        z = ICCTypes.unpack_s15fixed16(data[8:12])
        return (x, y, z)
    
    @staticmethod
    def unpack_datetime(data: bytes) -> datetime:
        """解析DateTimeNumber (6个uint16: year,month,day,hour,minute,second)"""
        year = UINT16.unpack(data[0:2])[0]
        month = UINT16.unpack(data[2:4])[0]
        day = UINT16.unpack(data[4:6])[0]
        hour = UINT16.unpack(data[6:8])[0]
        minute = UINT16.unpack(data[8:10])[0]
        second = UINT16.unpack(data[10:12])[0]
        return datetime(year, month, day, hour, minute, second)
    
    @staticmethod
    def unpack_signature(data: bytes) -> str:
        """解析4字节Signature (ASCII字符串，保留空格填充)"""
        return data[0:4].decode("ascii", errors="replace")
    
    @staticmethod
    def unpack_version(data: bytes) -> str:
        """解析版本号 (uint32: major.minor.revision)"""
        ver = UINT32.unpack(data[0:4])[0]
        major = (ver >> 24) & 0xFF
        minor = (ver >> 20) & 0x0F
        revision = (ver >> 16) & 0x0F
        return f"{major}.{minor}.{revision}"


# ==================== ICC Profile 结构体 ====================

@dataclass
class ICCHeader:
    """ICC Profile Header (128字节)"""
    # 文件偏移0-127
    
    profile_size: int          # 4字节 uint32
    preferred_cmm: str          # 4字节 signature
    version: str                # 4字节 uint32versionNumber
    device_class: str           # 4字节 signature
    color_space: str            # 4字节 signature  
    pcs: str                    # 4字节 signature (PCS = Profile Connection Space)
    datetime: datetime          # 12字节 DateTime
    signature: str              # 4字节 signature ('acsp')
    primary_platform: str       # 4字节 signature
    flags: int                  # 4字节 uint32
    device_manufacturer: str    # 4字节 signature
    device_model: str           # 4字节 signature
    device_attributes: int      # 8字节 uint64
    rendering_intent: int       # 4字节 uint32
    illuminant_xyz: Tuple[float, float, float]  # XYZNumber
    creator: str                # 4字节 signature
    _reserved: bytes            # 44字节保留
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "ICCHeader":
        """从字节数据解析Header"""
        t = ICCTypes
        return cls(
            profile_size=t.unpack_uint32(data[0:4]),
            preferred_cmm=t.unpack_signature(data[4:8]),
            version=t.unpack_version(data[8:12]),
            device_class=t.unpack_signature(data[12:16]),
            color_space=t.unpack_signature(data[16:20]),
            pcs=t.unpack_signature(data[20:24]),
            datetime=t.unpack_datetime(data[24:36]),
            signature=t.unpack_signature(data[36:40]),
            primary_platform=t.unpack_signature(data[40:44]),
            flags=t.unpack_uint32(data[44:48]),
            device_manufacturer=t.unpack_signature(data[48:52]),
            device_model=t.unpack_signature(data[52:56]),
            device_attributes=t.unpack_uint64(data[56:64]),
            rendering_intent=t.unpack_uint32(data[64:68]),
            illuminant_xyz=t.unpack_xyz(data[68:80]),
            creator=t.unpack_signature(data[80:84]),
            _reserved=data[84:128],
        )


@dataclass
class TagTableEntry:
    """Tag Table Entry (12字节)"""
    # 文件偏移128开始
    
    signature: str      # 4字节 signature (tag type)
    offset: int         # 4字节 uint32 (数据偏移)
    size: int           # 4字节 uint32 (数据大小)
    
    @classmethod
    def from_bytes(cls, data: bytes, offset: int) -> "TagTableEntry":
        t = ICCTypes
        sig_data = data[offset:offset+4]
        return cls(
            signature=t.unpack_signature(sig_data),
            offset=t.unpack_uint32(data[offset+4:offset+8]),
            size=t.unpack_uint32(data[offset+8:offset+12]),
        )


# ==================== Tag Type 结构体 ====================

@dataclass
class XYZType:
    """XYZ Type (12字节数据部分)"""
    type_signature: str           # 'XYZ '
    reserved: bytes               # 4字节保留
    value: Tuple[float, float, float]  # XYZNumber
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "XYZType":
        t = ICCTypes
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            value=t.unpack_xyz(data[8:20]),
        )


@dataclass
class ColorantEntry:
    """Colorant Table Entry (32字节)"""
    name: str           # 32字节 (前32字节是 colorant name, null-terminated ASCII)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "ColorantEntry":
        name = data[0:32].decode("ascii", errors="replace").split("\x00")[0]
        return cls(name=name)


@dataclass 
class ColorantTableType:
    """Colorant Table Type"""
    type_signature: str
    reserved: bytes
    count: int
    entries: List[ColorantEntry]
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "ColorantTableType":
        t = ICCTypes
        count = t.unpack_uint32(data[8:12])
        entries = []
        for i in range(count):
            entry_data = data[12 + i*32:12 + (i+1)*32]
            entries.append(ColorantEntry.from_bytes(entry_data))
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            count=count,
            entries=entries,
        )


@dataclass
class CurveType:
    """Curve Type (可变长度)"""
    type_signature: str
    reserved: bytes
    count: int
    curve_data: List[float]  # 如果count=0则是gamma值，否则是曲线点
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "CurveType":
        t = ICCTypes
        count = t.unpack_uint32(data[8:12])
        
        if count == 0:
            # count=0: 接下来4字节是gamma值 (u8Fixed8)
            gamma_raw = t.unpack_uint32(data[12:16])
            gamma = gamma_raw / 256.0
            return cls(
                type_signature=t.unpack_signature(data[0:4]),
                reserved=data[4:8],
                count=0,
                curve_data=[gamma],  # gamma值放在列表第一项
            )
        else:
            # count>0: count个uint16曲线点
            points = []
            for i in range(count):
                val_raw = UINT16.unpack(data[12 + i*2:12 + i*2 + 2])[0]
                points.append(val_raw / 65535.0)
            return cls(
                type_signature=t.unpack_signature(data[0:4]),
                reserved=data[4:8],
                count=count,
                curve_data=points,
            )


@dataclass
class ParametricCurveType:
    """Parametric Curve Type (para) - ICC.1:2022 Table 50"""
    type_signature: str
    reserved: bytes
    function_type: int      # uint16, 0-4
    reserved2: bytes         # uint16
    parameters: List[float]  # s15Fixed16 数组，参数个数取决于 function_type
    
    # function_type 对应的参数个数
    PARAMETER_COUNTS = {
        0: 1,  # Y = X^n
        1: 3,  # Y = (aX + b)^n
        2: 4,  # Y = (aX + b)^n + c
        3: 5,  # Y = (aX + b)^n + c (扩展)
        4: 6,  # Y = (aX + b)^n + c (扩展)
    }
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "ParametricCurveType":
        t = ICCTypes
        function_type = t.unpack_uint16(data[8:10])
        param_count = cls.PARAMETER_COUNTS.get(function_type, 1)
        
        parameters = []
        for i in range(param_count):
            parameters.append(t.unpack_s15fixed16(data[12 + i*4:16 + i*4]))
        
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            function_type=function_type,
            reserved2=data[10:12],
            parameters=parameters,
        )


@dataclass
class TextType:
    """Text Type (简单文本)"""
    type_signature: str
    reserved: bytes
    text: str
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "TextType":
        t = ICCTypes
        # 从偏移8开始是文本，null-terminated
        text_data = data[8:].split(b"\x00")[0]
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            text=text_data.decode("ascii", errors="replace"),
        )


@dataclass
class MultiLocalizedUnicodeType:
    """Multi-Localized Unicode Type (mluc)"""
    type_signature: str
    reserved: bytes
    count: int              # 记录数
    record_size: int        # 每条记录字节数
    records: List[dict]     # [{lang_code, country_code, text}, ...]
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "MultiLocalizedUnicodeType":
        t = ICCTypes
        count = t.unpack_uint32(data[8:12])
        record_size = t.unpack_uint32(data[12:16])
        
        records = []
        for i in range(count):
            record_offset = 16 + i * record_size
            lang_code = t.unpack_signature(data[record_offset:record_offset+2])
            country_code = t.unpack_signature(data[record_offset+2:record_offset+4])
            text_len = t.unpack_uint32(data[record_offset+4:record_offset+8])
            text_start_offset = t.unpack_uint32(data[record_offset+8:record_offset+12])
            
            # text 数据从 offset 位置开始，读取 size 字节
            text_data = data[text_start_offset:text_start_offset + text_len]
            try:
                text = text_data.decode("utf-16-be", errors="replace").strip("\x00")
            except Exception:
                text = ""
            
            records.append({
                "lang": lang_code,
                "country": country_code,
                "text": text,
            })
        
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            count=count,
            record_size=record_size,
            records=records,
        )
    
    def get_primary_text(self) -> str:
        """获取主文本（通常返回英文或第一个）"""
        for record in self.records:
            if record["lang"] == "en":
                return record["text"]
        return self.records[0]["text"] if self.records else ""


@dataclass
class SignatureType:
    """Signature Type"""
    type_signature: str
    reserved: bytes
    signature: str
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "SignatureType":
        t = ICCTypes
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            signature=t.unpack_signature(data[8:12]),
        )


@dataclass
class S15Fixed16ArrayType:
    """s15Fixed16 Array Type (sf32)"""
    type_signature: str
    reserved: bytes
    values: List[float]
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "S15Fixed16ArrayType":
        t = ICCTypes
        count = (len(data) - 8) // 4
        values = []
        for i in range(count):
            values.append(t.unpack_s15fixed16(data[8 + i*4:12 + i*4]))
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            values=values,
        )


@dataclass
class Lut8Type:
    """8-bit LUT Type (lut8)"""
    type_signature: str
    reserved: bytes
    input_channels: int
    output_channels: int
    clut_grid_points: int
    matrix: List[float]      # 9个s15Fixed16
    input_table: List[int]   # 256 * input_channels 字节
    clut_values: List[int]   # 可变长度
    output_table: List[int]  # 256 * output_channels 字节
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "Lut8Type":
        t = ICCTypes
        input_channels = t.unpack_uint8(data[8:9])
        output_channels = t.unpack_uint8(data[9:10])
        clut_grid_points = t.unpack_uint8(data[10:11])
        
        # Matrix (9个s15Fixed16)
        matrix = []
        for i in range(9):
            matrix.append(t.unpack_s15fixed16(data[12 + i*4:16 + i*4]))
        
        # Input table (256 * input_channels)
        input_table_offset = 12 + 9*4
        input_table = list(data[input_table_offset:input_table_offset + 256 * input_channels])
        
        # CLUT (clut_grid_points^3 * output_channels)
        clut_offset = input_table_offset + 256 * input_channels
        clut_values = list(data[clut_offset:clut_offset + clut_grid_points**3 * output_channels])
        
        # Output table (256 * output_channels)
        output_offset = clut_offset + clut_grid_points**3 * output_channels
        output_table = list(data[output_offset:output_offset + 256 * output_channels])
        
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            input_channels=input_channels,
            output_channels=output_channels,
            clut_grid_points=clut_grid_points,
            matrix=matrix,
            input_table=input_table,
            clut_values=clut_values,
            output_table=output_table,
        )


@dataclass
class Lut16Type:
    """16-bit LUT Type (lut16)"""
    type_signature: str
    reserved: bytes
    input_channels: int
    output_channels: int
    clut_grid_points: int
    matrix: List[float]
    input_table: List[int]   # 4096 * input_channels 字节 (uint16)
    clut_values: List[int]  # clut_grid_points^3 * output_channels * 2 字节
    output_table: List[int]  # 4096 * output_channels 字节 (uint16)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "Lut16Type":
        t = ICCTypes
        input_channels = t.unpack_uint8(data[8:9])
        output_channels = t.unpack_uint8(data[9:10])
        clut_grid_points = t.unpack_uint8(data[10:11])
        
        # Matrix (9个s15Fixed16)
        matrix = []
        for i in range(9):
            matrix.append(t.unpack_s15fixed16(data[12 + i*4:16 + i*4]))
        
        # Input table (4096 * input_channels 字节, uint16)
        input_table_offset = 12 + 9*4
        input_table = []
        for i in range(4096 * input_channels):
            val = UINT16.unpack(data[input_table_offset + i*2:input_table_offset + i*2 + 2])[0]
            input_table.append(val)
        
        # CLUT
        clut_offset = input_table_offset + 4096 * input_channels * 2
        clut_count = clut_grid_points ** 3 * output_channels
        clut_values = []
        for i in range(clut_count):
            val = UINT16.unpack(data[clut_offset + i*2:clut_offset + i*2 + 2])[0]
            clut_values.append(val)
        
        # Output table
        output_offset = clut_offset + clut_count * 2
        output_table = []
        for i in range(4096 * output_channels):
            val = UINT16.unpack(data[output_offset + i*2:output_offset + i*2 + 2])[0]
            output_table.append(val)
        
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            input_channels=input_channels,
            output_channels=output_channels,
            clut_grid_points=clut_grid_points,
            matrix=matrix,
            input_table=input_table,
            clut_values=clut_values,
            output_table=output_table,
        )


@dataclass
class LutAToBType:
    """LUT A to B Type (mAB) - 基于 ICC.1:2022 Table 45 及 tt_AB.py"""
    type_signature: str
    reserved: bytes
    input_channels: int       # offset 8
    output_channels: int      # offset 9
    padding: bytes            # offset 10-11 (reserved)
    offset_b_curve: int       # offset 12-15: Offset to first "B" curve
    offset_matrix: int        # offset 16-19: Offset to B matrix
    offset_m_curve: int       # offset 20-23: Offset to M curve
    offset_clut: int          # offset 24-27: Offset to CLUT
    offset_a_curve: int       # offset 28-31: Offset to "A" curve
    
    # 解析出的子元素数据
    b_curve: dict = None      # B曲线 (curv/para类型)
    matrix: List[float] = None  # 3x3矩阵 (s15Fixed16数组)
    m_curve: dict = None     # M曲线 (curv/para类型)
    clut: dict = None        # CLUT数据
    a_curve: dict = None     # A曲线 (curv/para类型)
    
    @classmethod
    def from_bytes(cls, data: bytes, full_data: bytes = None, tag_offset: int = 0) -> "LutAToBType":
        """解析 LutAToB 类型
        Args:
            data: tag数据 (相对偏移)
            full_data: 完整文件数据
            tag_offset: tag在完整文件中的起始偏移量
        """
        t = ICCTypes
        offset_b_curve = t.unpack_uint32(data[12:16])
        offset_matrix = t.unpack_uint32(data[16:20])
        offset_m_curve = t.unpack_uint32(data[20:24])
        offset_clut = t.unpack_uint32(data[24:28])
        offset_a_curve = t.unpack_uint32(data[28:32])
        
        instance = cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            input_channels=t.unpack_uint8(data[8:9]),
            output_channels=t.unpack_uint8(data[9:10]),
            padding=data[10:12],
            offset_b_curve=offset_b_curve,
            offset_matrix=offset_matrix,
            offset_m_curve=offset_m_curve,
            offset_clut=offset_clut,
            offset_a_curve=offset_a_curve,
        )
        
        # 使用完整数据解析子元素
        parse_data = full_data if full_data is not None else data
        
        # 解析 B curve
        if offset_b_curve > 0:
            instance.b_curve = cls._parse_curve(parse_data, tag_offset + offset_b_curve)
        
        # 解析 Matrix
        if offset_matrix > 0:
            instance.matrix = cls._parse_matrix(parse_data, tag_offset + offset_matrix)
        
        # 解析 M curve
        if offset_m_curve > 0:
            instance.m_curve = cls._parse_curve(parse_data, tag_offset + offset_m_curve)
        
        # 解析 CLUT
        if offset_clut > 0:
            instance.clut = cls._parse_clut(parse_data, tag_offset + offset_clut, instance.input_channels, instance.output_channels)
        
        # 解析 A curve
        if offset_a_curve > 0:
            instance.a_curve = cls._parse_curve(parse_data, tag_offset + offset_a_curve)
        
        return instance
    
    @staticmethod
    def _parse_curve(data: bytes, offset: int) -> dict:
        """解析curve类型数据 (curv 或 para)"""
        if offset + 4 > len(data):
            return {"error": "offset exceeds data length"}
        
        type_sig = ICCTypes.unpack_signature(data[offset:offset+4])
        if type_sig == "curv":
            return CurveType.from_bytes(data[offset:]).__dict__
        elif type_sig == "para":
            return ParametricCurveType.from_bytes(data[offset:]).__dict__
        return {"error": f"Expected curve type, got {type_sig}"}
    
    @staticmethod
    def _parse_clut(data: bytes, offset: int, input_channels: int, output_channels: int) -> dict:
        """解析CLUT数据 - 基于 ICC.1:2022 Table 45
        
        CLUT 结构：
        - offset + 0-15: gridPointsArray (input_channels 个 uint8，后跟填充0)
        - offset + 16: precision (uint8: 1=int8, 2=int16)
        - offset + 17-19: reserved (3个字节, 0x00)
        - offset + 20+: CLUTData (gridPoints^input_channels * output_channels 个值)
        """
        if offset + 20 > len(data):
            return {"error": "offset exceeds data length"}
        
        result = {}
        
        # 读取网格点数 (图表 45: gridPointsArray 在前 16 字节,取 input_channels 个值)
        grid_points_list = []
        for i in range(input_channels):
            gp = data[offset + i]
            if gp > 0:
                grid_points_list.append(gp)
        
        result["grid_points"] = grid_points_list
        result["input_channels"] = input_channels
        result["output_channels"] = output_channels
        
        # Precision byte at offset + 16
        precision = data[offset + 16]
        result["precision"] = precision
        
        # CLUT data starts at offset + 20
        clut_data_start = offset + 20
        
        # 计算总点数
        total_points = 1
        for g in grid_points_list:
            total_points *= g
        
        total_values = total_points * output_channels
        
        # 读取 CLUT 数据
        if precision == 1:
            # uint8 (uInt8Number 按 0-255 表示 0.0-1.0)
            clut_raw = list(data[clut_data_start:clut_data_start + total_values])
            result["values"] = [v / 255.0 for v in clut_raw]
            result["data_type"] = "uint8"
        elif precision == 2:
            # uint16 (uInt16Number 按 0-65535 表示 0.0-1.0)
            values = []
            for i in range(total_values):
                val = UINT16.unpack(data[clut_data_start + i*2:clut_data_start + i*2 + 2])[0]
                values.append(val / 65535.0)
            result["values"] = values
            result["data_type"] = "uint16"
        else:
            # 其他精度值不支持
            result["error"] = f"Unsupported precision: {precision} (use 1 for uint8, 2 for uint16)"
        
        return result
    
    @staticmethod
    def _parse_matrix(data: bytes, offset: int) -> List[float]:
        """解析3x3矩阵 (9个s15Fixed16)"""
        if offset + 36 > len(data):
            return []
        
        matrix = []
        for i in range(9):
            matrix.append(ICCTypes.unpack_s15fixed16(data[offset + i*4:offset + (i+1)*4]))
        return matrix


@dataclass
class MeasurementType:
    """Measurement Type"""
    type_signature: str
    reserved: bytes
    observer: int           # uint32
    xyz_backing: Tuple[float, float, float]
    geometry: int           # uint32
    flare: int              # uint32
    illuminant: Tuple[float, float, float]
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "MeasurementType":
        t = ICCTypes
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            observer=t.unpack_uint32(data[8:12]),
            xyz_backing=t.unpack_xyz(data[12:24]),
            geometry=t.unpack_uint32(data[24:28]),
            flare=t.unpack_uint32(data[28:32]),
            illuminant=t.unpack_xyz(data[32:44]),
        )


# ==================== Tag Type 注册表 ====================

TAG_TYPE_PARSERS = {
    "XYZ ": XYZType.from_bytes,
    "curv": CurveType.from_bytes,
    "para": ParametricCurveType.from_bytes,
    "text": TextType.from_bytes,
    "mluc": MultiLocalizedUnicodeType.from_bytes,
    "sig ": SignatureType.from_bytes,
    "sf32": S15Fixed16ArrayType.from_bytes,
    "lut8": Lut8Type.from_bytes,
    "lut16": Lut16Type.from_bytes,
    "mAB ": LutAToBType.from_bytes,
    "mBA ": LutAToBType.from_bytes,
    "clrt": ColorantTableType.from_bytes,
    "meas": MeasurementType.from_bytes,
}


def parse_tag_type(data: bytes, type_sig: str, full_data: bytes = None, tag_offset: int = 0) -> Optional[object]:
    """根据type signature解析tag数据"""
    parser = TAG_TYPE_PARSERS.get(type_sig)
    if parser:
        try:
            # 对于 LutAToB/B 类型，传入完整数据和偏移量以便计算子元素位置
            if type_sig in ("mAB ", "mBA ") and full_data is not None:
                return parser(data, full_data, tag_offset)
            return parser(data)
        except Exception as e:
            return {"error": str(e), "raw_data": data.hex()}
    return {"error": f"Unknown type: {type_sig}", "raw_data": data.hex()}
