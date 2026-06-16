"""ICC Profile 结构体定义（基于 ICC.1:2022 规范）"""

import struct
from dataclasses import dataclass
from typing import Any, Tuple, List, Optional, Union
from datetime import datetime


# ==================== 基础类型定义 ====================

# 基础数据类型 (格式, 字节数)
UINT8 = struct.Struct(">B")          # 1字节无符号
UINT16 = struct.Struct(">H")         # 2字节无符号
UINT32 = struct.Struct(">I")         # 4字节无符号
UINT64 = struct.Struct(">Q")         # 8字节无符号
INT32 = struct.Struct(">i")          # 4字节有符号

# 定点数类型
# u8Fixed8: 8.8定点数 (规范4.9: 16位量, 8位小数, 1.0=0100h)，解析时除以256
U8FIXED8 = struct.Struct(">H")       # 存储为16位无符号整数，解析时除以256

# s15Fixed16: 15.16定点数 (1字节整数 + 16位小数)
S15FIXED16 = struct.Struct(">i")     # 存储时是有符号32位整数，解析时除以65536

# u1Fixed15: 1.15定点数 (用于介素)
U1FIXED15 = struct.Struct(">H")      # 存储时是16位，解析时除以32768


# Header 字段元信息：名称 -> (偏移量, 字节数, 基础数据类型, 数据数量)
ICC_HEADER_FIELDS = {
    "profile_size": (0, 4, "uint32", 4),
    "preferred_cmm": (4, 4, "signature", 4),
    "version": (8, 4, "uint32", 4),
    "device_class": (12, 4, "signature", 4),
    "color_space": (16, 4, "signature", 4),
    "pcs": (20, 4, "signature", 4),
    "datetime": (24, 12, "uint16[6]", 6),
    "signature": (36, 4, "signature", 4),
    "primary_platform": (40, 4, "signature", 4),
    "flags": (44, 4, "uint32", 4),
    "device_manufacturer": (48, 4, "signature", 4),
    "device_model": (52, 4, "signature", 4),
    "device_attributes": (56, 8, "uint64", 8),
    "rendering_intent": (64, 4, "uint32", 4),
    "illuminant_xyz": (68, 12, "s15Fixed16[3]", 3),
    "creator": (80, 4, "signature", 4),
    "profile_id": (84, 16, "bytes", 16),
    "reserved": (100, 28, "bytes", 28),
}


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
        """解析u8Fixed8定点数 (规范4.9: 16位量, 8位小数)"""
        raw = U8FIXED8.unpack(data[0:2])[0]
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
    profile_id: bytes           # 16字节 profile ID (MD5), 偏移84-99
    _reserved: bytes            # 28字节保留, 偏移100-127
    
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
            profile_id=data[84:100],
            _reserved=data[100:128],
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
    """XYZ Type - 规范 10.31 / Table 84

    数据部分为 XYZNumber 数组 (每组12字节)。大多数 tag 只含1组。
    value 保留第一组以兼容旧 Python 调用; JSON 导出只保留 values，避免重复。
    """
    type_signature: str           # 'XYZ '
    reserved: bytes               # 4字节保留
    value: Tuple[float, float, float]       # 第一组 XYZNumber
    values: List[Tuple[float, float, float]]  # 全部 XYZNumber

    @classmethod
    def from_bytes(cls, data: bytes) -> "XYZType":
        t = ICCTypes
        count = max(0, (len(data) - 8) // 12)
        values = [t.unpack_xyz(data[8 + i*12:20 + i*12]) for i in range(count)]
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            value=values[0] if values else (0.0, 0.0, 0.0),
            values=values,
        )


@dataclass
class ColorantEntry:
    """Colorant Table Entry (38字节 = 32字节名字 + uInt16Number[3] PCS值)

    规范 10.5 / Table 34。PCS 值为相对比色，按 uInt16Number 编码。
    """
    name: str               # 32字节, null-terminated 7-bit ASCII
    pcs: Tuple[int, int, int]  # 3个 uInt16Number (PCSXYZ 或 PCSLAB)

    @classmethod
    def from_bytes(cls, data: bytes) -> "ColorantEntry":
        name = data[0:32].decode("ascii", errors="replace").split("\x00")[0]
        pcs = (
            UINT16.unpack(data[32:34])[0],
            UINT16.unpack(data[34:36])[0],
            UINT16.unpack(data[36:38])[0],
        )
        return cls(name=name, pcs=pcs)


@dataclass 
class ColorantTableType:
    """Colorant Table Type - 规范 10.5 / Table 34"""
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
            entry_data = data[12 + i*38:12 + (i+1)*38]
            entries.append(ColorantEntry.from_bytes(entry_data))
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            count=count,
            entries=entries,
        )


@dataclass
class CurveType:
    """Curve Type (可变长度) - 规范 10.6 / Table 35

    count==0: identity 响应（无后续数据）
    count==1: 1个 u8Fixed8Number (2字节) gamma 值
    count>1 : count 个 uint16 曲线点 (÷65535)
    """
    type_signature: str
    reserved: bytes
    count: int
    curve_data: List[float]  # count==0 时为空; count==1 时为[gamma]; 否则为曲线点

    @classmethod
    def from_bytes(cls, data: bytes) -> "CurveType":
        t = ICCTypes
        count = t.unpack_uint32(data[8:12])

        if count == 0:
            # identity 响应，无曲线数据
            return cls(
                type_signature=t.unpack_signature(data[0:4]),
                reserved=data[4:8],
                count=0,
                curve_data=[],
            )
        elif count == 1:
            # 1个 u8Fixed8Number (2字节) 作为 gamma 值
            gamma = t.unpack_u8fixed8(data[12:14])
            return cls(
                type_signature=t.unpack_signature(data[0:4]),
                reserved=data[4:8],
                count=1,
                curve_data=[gamma],
            )
        else:
            # count>1: count个uint16曲线点 (÷65535)
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
    
    # function_type 对应的参数个数 (规范 Table 68)
    PARAMETER_COUNTS = {
        0: 1,  # Y = X^g                       参数: g
        1: 3,  # Y = (aX + b)^g                 参数: g a b
        2: 4,  # Y = (aX + b)^g + c             参数: g a b c
        3: 5,  # 分段: (aX+b)^g / cX            参数: g a b c d
        4: 7,  # 分段含偏移                     参数: g a b c d e f
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
class TextDescriptionType:
    """Text Description Type (desc) - ICC v2 legacy profile description.

    The structure contains an ASCII description, followed by optional Unicode
    and ScriptCode descriptions. ICC v4 profiles usually use mluc instead.
    """
    type_signature: str
    reserved: bytes
    ascii_count: int
    ascii_description: str
    unicode_language_code: int
    unicode_count: int
    unicode_description: str
    script_code_code: int
    script_code_count: int
    script_code_description: str

    @classmethod
    def from_bytes(cls, data: bytes) -> "TextDescriptionType":
        t = ICCTypes
        ascii_count = t.unpack_uint32(data[8:12]) if len(data) >= 12 else 0
        ascii_start = 12
        ascii_end = min(len(data), ascii_start + ascii_count)
        ascii_raw = data[ascii_start:ascii_end]
        ascii_description = ascii_raw.split(b"\x00")[0].decode("ascii", errors="replace")

        unicode_language_offset = ascii_end
        unicode_count_offset = unicode_language_offset + 4
        unicode_text_offset = unicode_count_offset + 4
        unicode_language_code = t.unpack_uint32(data[unicode_language_offset:unicode_language_offset + 4]) if len(data) >= unicode_language_offset + 4 else 0
        unicode_count = t.unpack_uint32(data[unicode_count_offset:unicode_count_offset + 4]) if len(data) >= unicode_count_offset + 4 else 0
        unicode_bytesize = unicode_count * 2
        unicode_raw = data[unicode_text_offset:unicode_text_offset + unicode_bytesize]
        unicode_description = unicode_raw.decode("utf-16-be", errors="replace").split("\x00")[0] if unicode_raw else ""

        script_code_offset = unicode_text_offset + unicode_bytesize
        script_count_offset = script_code_offset + 2
        script_text_offset = script_count_offset + 1
        script_code_code = t.unpack_uint16(data[script_code_offset:script_code_offset + 2]) if len(data) >= script_code_offset + 2 else 0
        script_code_count = t.unpack_uint8(data[script_count_offset:script_count_offset + 1]) if len(data) >= script_count_offset + 1 else 0
        script_raw = data[script_text_offset:script_text_offset + min(script_code_count, 67)]
        script_code_description = script_raw.split(b"\x00")[0].decode("mac_roman", errors="replace") if script_raw else ""

        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            ascii_count=ascii_count,
            ascii_description=ascii_description,
            unicode_language_code=unicode_language_code,
            unicode_count=unicode_count,
            unicode_description=unicode_description,
            script_code_code=script_code_code,
            script_code_count=script_code_count,
            script_code_description=script_code_description,
        )


@dataclass
class ParsedField:
    """带字节位置元信息的已解析字段。"""
    value: Any
    offset: int
    bytesize: int
    datatype: str
    datasize: int


@dataclass
class MultiLocalizedUnicodeRecord:
    """mluc 记录项 - 规范 10.13

    每条记录描述一段本地化文本的位置与语言信息。文本内容位于 mluc
    数据块内的独立字符串区域，text_offset 是相对 mluc type 起点的偏移。
    """
    language_code: ParsedField  # 2字节语言代码，如 "en"
    country_code: ParsedField   # 2字节国家/地区代码，如 "US"
    text: ParsedField           # UTF-16BE 文本内容，bytesize 来自 text_length


@dataclass
class MultiLocalizedUnicodeType:
    """Multi-Localized Unicode Type (mluc)"""
    type_signature: ParsedField
    reserved: ParsedField
    count: ParsedField              # 记录数
    record_size: ParsedField        # 每条记录字节数
    records: List[MultiLocalizedUnicodeRecord]
    
    @classmethod
    def from_bytes(cls, data: bytes, tag_offset: int = 0) -> "MultiLocalizedUnicodeType":
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
            
            records.append(MultiLocalizedUnicodeRecord(
                language_code=ParsedField(
                    value=lang_code,
                    offset=tag_offset + record_offset,
                    bytesize=2,
                    datatype="ascii",
                    datasize=2,
                ),
                country_code=ParsedField(
                    value=country_code,
                    offset=tag_offset + record_offset + 2,
                    bytesize=2,
                    datatype="ascii",
                    datasize=2,
                ),
                text=ParsedField(
                    value=text,
                    offset=tag_offset + text_start_offset,
                    bytesize=text_len,
                    datatype="utf16-be",
                    datasize=len(text),
                ),
            ))
        
        return cls(
            type_signature=ParsedField(
                value=t.unpack_signature(data[0:4]),
                offset=tag_offset,
                bytesize=4,
                datatype="signature",
                datasize=4,
            ),
            reserved=ParsedField(
                value=data[4:8],
                offset=tag_offset + 4,
                bytesize=4,
                datatype="bytes",
                datasize=4,
            ),
            count=ParsedField(
                value=count,
                offset=tag_offset + 8,
                bytesize=4,
                datatype="uint32",
                datasize=1,
            ),
            record_size=ParsedField(
                value=record_size,
                offset=tag_offset + 12,
                bytesize=4,
                datatype="uint32",
                datasize=1,
            ),
            records=records,
        )
    
    def get_primary_text(self) -> str:
        """获取主文本（通常返回英文或第一个）"""
        for record in self.records:
            if record.language_code.value == "en":
                return record.text.value
        return self.records[0].text.value if self.records else ""


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
class LutMatrix3x3:
    """lut8/lut16 3x3 矩阵子结构。

    该矩阵位于 lut8/lut16 头部之后，共 9 个 s15Fixed16Number。
    注意它不同于 mAB/mBA 的 3x4 矩阵。
    """
    values: List[float]
    rows: List[List[float]]

    @classmethod
    def from_bytes(cls, data: bytes, offset: int) -> "LutMatrix3x3":
        """从指定偏移解析 9 个 s15Fixed16Number。"""
        if offset + 36 > len(data):
            raise ValueError("lut matrix exceeds data length")

        values = [
            ICCTypes.unpack_s15fixed16(data[offset + i*4:offset + (i+1)*4])
            for i in range(9)
        ]
        rows = [values[i:i+3] for i in range(0, 9, 3)]
        return cls(values=values, rows=rows)


@dataclass
class LutTable:
    """lut8/lut16 输入表或输出表子结构。"""
    values: List[int]
    channels: int
    entries_per_channel: int
    bit_depth: int
    normalized_values: List[float]

    @classmethod
    def from_uint8_bytes(
        cls,
        data: bytes,
        offset: int,
        channels: int,
        entries_per_channel: int,
    ) -> "LutTable":
        """解析 uint8 LUT 表。"""
        count = channels * entries_per_channel
        values = list(data[offset:offset + count])
        return cls(
            values=values,
            channels=channels,
            entries_per_channel=entries_per_channel,
            bit_depth=8,
            normalized_values=[value / 255.0 for value in values],
        )

    @classmethod
    def from_uint16_bytes(
        cls,
        data: bytes,
        offset: int,
        channels: int,
        entries_per_channel: int,
    ) -> "LutTable":
        """解析 uint16 LUT 表。"""
        count = channels * entries_per_channel
        values = [
            UINT16.unpack(data[offset + i*2:offset + i*2 + 2])[0]
            for i in range(count)
        ]
        return cls(
            values=values,
            channels=channels,
            entries_per_channel=entries_per_channel,
            bit_depth=16,
            normalized_values=[value / 65535.0 for value in values],
        )


@dataclass
class LutClut:
    """lut8/lut16 CLUT 子结构。"""
    values: List[int]
    grid_points: int
    input_channels: int
    output_channels: int
    bit_depth: int
    normalized_values: List[float]

    @classmethod
    def from_uint8_bytes(
        cls,
        data: bytes,
        offset: int,
        grid_points: int,
        input_channels: int,
        output_channels: int,
    ) -> "LutClut":
        """解析 uint8 CLUT。"""
        count = grid_points ** input_channels * output_channels
        values = list(data[offset:offset + count])
        return cls(
            values=values,
            grid_points=grid_points,
            input_channels=input_channels,
            output_channels=output_channels,
            bit_depth=8,
            normalized_values=[value / 255.0 for value in values],
        )

    @classmethod
    def from_uint16_bytes(
        cls,
        data: bytes,
        offset: int,
        grid_points: int,
        input_channels: int,
        output_channels: int,
    ) -> "LutClut":
        """解析 uint16 CLUT。"""
        count = grid_points ** input_channels * output_channels
        values = [
            UINT16.unpack(data[offset + i*2:offset + i*2 + 2])[0]
            for i in range(count)
        ]
        return cls(
            values=values,
            grid_points=grid_points,
            input_channels=input_channels,
            output_channels=output_channels,
            bit_depth=16,
            normalized_values=[value / 65535.0 for value in values],
        )


@dataclass
class Lut8Type:
    """8-bit LUT Type (mft1 / lut8)"""
    type_signature: str
    reserved: bytes
    input_channels: int
    output_channels: int
    clut_grid_points: int
    matrix: LutMatrix3x3
    input_table: LutTable
    clut: LutClut
    output_table: LutTable
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "Lut8Type":
        t = ICCTypes
        input_channels = t.unpack_uint8(data[8:9])
        output_channels = t.unpack_uint8(data[9:10])
        clut_grid_points = t.unpack_uint8(data[10:11])
        
        matrix = LutMatrix3x3.from_bytes(data, 12)
        
        # Input table (256 * input_channels)
        input_table_offset = 12 + 9*4
        input_table = LutTable.from_uint8_bytes(data, input_table_offset, input_channels, 256)
        
        # CLUT (clut_grid_points^input_channels * output_channels), 规范 10.11
        clut_entries = clut_grid_points ** input_channels * output_channels
        clut_offset = input_table_offset + 256 * input_channels
        clut = LutClut.from_uint8_bytes(data, clut_offset, clut_grid_points, input_channels, output_channels)
        
        # Output table (256 * output_channels)
        output_offset = clut_offset + clut_entries
        output_table = LutTable.from_uint8_bytes(data, output_offset, output_channels, 256)
        
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            input_channels=input_channels,
            output_channels=output_channels,
            clut_grid_points=clut_grid_points,
            matrix=matrix,
            input_table=input_table,
            clut=clut,
            output_table=output_table,
        )


@dataclass
class Lut16Type:
    """16-bit LUT Type (mft2 / lut16) - 规范 10.10 / Table 40

    输入/输出表条目数为可变值 (n, m)，分别存放在字节 48-49 与 50-51。
    输入表从偏移 52 开始。CLUT 大小 = grid^input_channels * output_channels。
    """
    type_signature: str
    reserved: bytes
    input_channels: int
    output_channels: int
    clut_grid_points: int
    num_input_entries: int   # n: 每通道输入表条目数
    num_output_entries: int  # m: 每通道输出表条目数
    matrix: LutMatrix3x3
    input_table: LutTable
    clut: LutClut
    output_table: LutTable
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "Lut16Type":
        t = ICCTypes
        input_channels = t.unpack_uint8(data[8:9])
        output_channels = t.unpack_uint8(data[9:10])
        clut_grid_points = t.unpack_uint8(data[10:11])
        
        matrix = LutMatrix3x3.from_bytes(data, 12)
        
        # 可变条目数: n (偏移48-49), m (偏移50-51)
        num_input_entries = UINT16.unpack(data[48:50])[0]
        num_output_entries = UINT16.unpack(data[50:52])[0]
        
        # Input table (n * input_channels 个 uint16, 从偏移 52 开始)
        input_table_offset = 52
        input_table = LutTable.from_uint16_bytes(data, input_table_offset, input_channels, num_input_entries)
        
        # CLUT (grid^input_channels * output_channels 个 uint16)
        clut_offset = input_table_offset + num_input_entries * input_channels * 2
        clut_count = clut_grid_points ** input_channels * output_channels
        clut = LutClut.from_uint16_bytes(data, clut_offset, clut_grid_points, input_channels, output_channels)
        
        # Output table (m * output_channels 个 uint16)
        output_offset = clut_offset + clut_count * 2
        output_table = LutTable.from_uint16_bytes(data, output_offset, output_channels, num_output_entries)
        
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            input_channels=input_channels,
            output_channels=output_channels,
            clut_grid_points=clut_grid_points,
            num_input_entries=num_input_entries,
            num_output_entries=num_output_entries,
            matrix=matrix,
            input_table=input_table,
            clut=clut,
            output_table=output_table,
        )


CurveLike = Union[CurveType, ParametricCurveType]


@dataclass
class LutABMatrix:
    """mAB/mBA Matrix 子结构 - 规范 10.12.5

    该矩阵不是带 type signature 的 Tag Type，而是 lutAToB/lutBToA 内部
    通过相对偏移定位的裸数据块。共 12 个 s15Fixed16Number：
    e1-e9 为 3x3 矩阵系数，e10-e12 为常数偏移项。
    """
    values: List[float]       # e1-e12, 12个 s15Fixed16Number
    coefficients: List[float] # e1-e9, 3x3 矩阵系数
    offsets: List[float]      # e10-e12, 常数偏移项

    @classmethod
    def from_bytes(cls, data: bytes, offset: int) -> "LutABMatrix":
        """从完整数据中的绝对偏移解析 mAB/mBA 3x4 矩阵。"""
        if offset + 48 > len(data):
            raise ValueError("mAB/mBA matrix exceeds data length")

        values = [
            ICCTypes.unpack_s15fixed16(data[offset + i*4:offset + (i+1)*4])
            for i in range(12)
        ]
        return cls(
            values=values,
            coefficients=values[:9],
            offsets=values[9:12],
        )


@dataclass
class LutABClut:
    """mAB/mBA CLUT 子结构 - 规范 10.12.4

    该 CLUT 不是带 type signature 的 Tag Type，而是 lutAToB/lutBToA 内部
    通过相对偏移定位的裸数据块。
    """
    grid_points: List[int]    # 每个输入通道的网格点数
    precision: int            # 1=uint8, 2=uint16
    data_type: str            # "uint8" 或 "uint16"
    values: List[float]       # 归一化后的 CLUT 值
    input_channels: int
    output_channels: int

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        offset: int,
        input_channels: int,
        output_channels: int,
    ) -> "LutABClut":
        """从完整数据中的绝对偏移解析 mAB/mBA CLUT。"""
        if offset + 20 > len(data):
            raise ValueError("mAB/mBA CLUT exceeds data length")

        grid_points = [
            data[offset + i]
            for i in range(input_channels)
            if data[offset + i] > 0
        ]
        precision = data[offset + 16]

        total_points = 1
        for grid in grid_points:
            total_points *= grid

        total_values = total_points * output_channels
        clut_data_start = offset + 20

        if precision == 1:
            raw_values = list(data[clut_data_start:clut_data_start + total_values])
            values = [value / 255.0 for value in raw_values]
            data_type = "uint8"
        elif precision == 2:
            values = []
            for i in range(total_values):
                raw = UINT16.unpack(data[clut_data_start + i*2:clut_data_start + i*2 + 2])[0]
                values.append(raw / 65535.0)
            data_type = "uint16"
        else:
            raise ValueError(f"Unsupported precision: {precision} (use 1 for uint8, 2 for uint16)")

        return cls(
            grid_points=grid_points,
            precision=precision,
            data_type=data_type,
            values=values,
            input_channels=input_channels,
            output_channels=output_channels,
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
    b_curve: Optional[CurveLike] = None       # B曲线 (curv/para类型)
    matrix: Optional[LutABMatrix] = None      # 3x4矩阵 (12个s15Fixed16)
    m_curve: Optional[CurveLike] = None       # M曲线 (curv/para类型)
    clut: Optional[LutABClut] = None          # CLUT子结构
    a_curve: Optional[CurveLike] = None       # A曲线 (curv/para类型)
    
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
    def _parse_curve(data: bytes, offset: int) -> CurveLike:
        """解析curve类型数据 (curv 或 para)"""
        if offset + 4 > len(data):
            raise ValueError("curve offset exceeds data length")
        
        type_sig = ICCTypes.unpack_signature(data[offset:offset+4])
        if type_sig == "curv":
            return CurveType.from_bytes(data[offset:])
        elif type_sig == "para":
            return ParametricCurveType.from_bytes(data[offset:])
        raise ValueError(f"Expected curve type, got {type_sig}")
    
    @staticmethod
    def _parse_clut(data: bytes, offset: int, input_channels: int, output_channels: int) -> LutABClut:
        """解析CLUT数据 - 基于 ICC.1:2022 Table 45
        
        CLUT 结构：
        - offset + 0-15: gridPointsArray (input_channels 个 uint8，后跟填充0)
        - offset + 16: precision (uint8: 1=int8, 2=int16)
        - offset + 17-19: reserved (3个字节, 0x00)
        - offset + 20+: CLUTData (gridPoints^input_channels * output_channels 个值)
        """
        return LutABClut.from_bytes(data, offset, input_channels, output_channels)
    
    @staticmethod
    def _parse_matrix(data: bytes, offset: int) -> LutABMatrix:
        """解析 mAB/mBA 矩阵 (规范 10.12.5: 3x4 数组, e1-e12, 共48字节)

        e1-e9 为 3x3 矩阵系数, e10-e12 为偏移项 (常数项)。
        """
        return LutABMatrix.from_bytes(data, offset)


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

@dataclass
class DateTimeType:
    """dateTimeType (dtim) - 规范 10.8 / Table 38

    数据部分为 1 个 dateTimeNumber (12字节, 6个uint16)。
    """
    type_signature: str
    reserved: bytes
    value: str   # ISO 格式时间字符串

    @classmethod
    def from_bytes(cls, data: bytes) -> "DateTimeType":
        t = ICCTypes
        return cls(
            type_signature=t.unpack_signature(data[0:4]),
            reserved=data[4:8],
            value=t.unpack_datetime(data[8:20]).isoformat(),
        )


TAG_TYPE_PARSERS = {
    "XYZ ": XYZType.from_bytes,
    "curv": CurveType.from_bytes,
    "para": ParametricCurveType.from_bytes,
    "text": TextType.from_bytes,
    "desc": TextDescriptionType.from_bytes,
    "mluc": MultiLocalizedUnicodeType.from_bytes,
    "sig ": SignatureType.from_bytes,
    "sf32": S15Fixed16ArrayType.from_bytes,
    "mft1": Lut8Type.from_bytes,
    "mft2": Lut16Type.from_bytes,
    "lut8": Lut8Type.from_bytes,   # 兼容旧命名
    "lut16": Lut16Type.from_bytes,  # 兼容旧命名（真实 type signature 为4字节，通常是 mft2）
    "mAB ": LutAToBType.from_bytes,
    "mBA ": LutAToBType.from_bytes,
    "clrt": ColorantTableType.from_bytes,
    "meas": MeasurementType.from_bytes,
    "dtim": DateTimeType.from_bytes,
}


def parse_tag_type(data: bytes, type_sig: str, full_data: bytes = None, tag_offset: int = 0) -> Optional[object]:
    """根据type signature解析tag数据"""
    parser = TAG_TYPE_PARSERS.get(type_sig)
    if parser:
        try:
            # 对于 LutAToB/B 类型，传入完整数据和偏移量以便计算子元素位置
            if type_sig in ("mAB ", "mBA ") and full_data is not None:
                return parser(data, full_data, tag_offset)
            if type_sig == "mluc":
                return parser(data, tag_offset=tag_offset)
            return parser(data)
        except Exception as e:
            return {"error": str(e), "raw_data": data.hex()}
    return {"error": f"Unknown type: {type_sig}", "raw_data": data.hex()}
