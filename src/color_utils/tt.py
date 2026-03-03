import struct
import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


# ============================================================
# 基础读取函数
# ============================================================

def read_u32(data, offset):
    return struct.unpack(">I", data[offset:offset+4])[0]


def read_s15fixed16(data, offset):
    raw = struct.unpack(">i", data[offset:offset+4])[0]
    return raw / 65536.0


# ============================================================
# Tag Table 解析
# ============================================================

def parse_tag_table(data):
    tag_count = read_u32(data, 128)
    tags = {}
    offset = 132

    for _ in range(tag_count):
        sig = data[offset:offset+4].decode("ascii")
        tag_offset = read_u32(data, offset+4)
        tag_size = read_u32(data, offset+8)
        tags[sig] = (tag_offset, tag_size)
        offset += 12

    return tags


# ============================================================
# 解析 mAB / A2B0
# ============================================================

def parse_mab(data, offset):
    input_channels = data[offset+8]
    output_channels = data[offset+9]
    offset_Bcurve = read_u32(data,offset+12)
    offset_matrix =read_u32(data,offset+16)
    offset_Mcurve= read_u32(data,offset+20)
    offset_clut = read_u32(data, offset+24)
    offset_Acurve=read_u32(data,offset+28)
    

    if offset_clut == 0:
        raise ValueError("No CLUT in this A2B0")

    clut_pos = offset + offset_clut

    # grid size
    grid_points = list(data[clut_pos:clut_pos+16])
    # find 0 index
    zero_index = grid_points.index(0)
    grid_points = grid_points[:zero_index]
    precision = data[clut_pos+16]

    clut_data_start = clut_pos + 20

    total_points = 1
    for g in grid_points:
        total_points *= g

    total_values = total_points * output_channels

    if precision == 0:
        fmt = f"{total_values}f"
        size = total_values * 4
        norm = 1.0  # 浮点数不需要归一化
        raise ValueError(f"Unsupported CLUT precision: {precision} , only support 0 and 1")
    elif precision == 1:
        fmt = f">{total_values}B"
        size = total_values
        norm = 255.0
    elif precision == 2:
        fmt = f">{total_values}H"
        size = total_values * 2
        norm = 65535.0
    else:
        raise ValueError(f"Unsupported CLUT precision: {precision}")

    clut_raw = struct.unpack(
        fmt,
        data[clut_data_start:clut_data_start+size]
    )

    cube = np.array(clut_raw, dtype=np.uint16) / norm
    cube = cube.reshape(
        grid_points[0],
        grid_points[1],
        grid_points[2],
        output_channels
    )

    return cube, grid_points


# ============================================================
# 可视化 1：1D 切片
# ============================================================

def visualize_1d(cube):
    plt.figure()
    r_curve = cube[:, 0, 0, 0]
    plt.plot(r_curve)
    plt.title("1D Slice along R axis (G=0, B=0)")
    plt.xlabel("R index")
    plt.ylabel("Output R")
    plt.show()


# ============================================================
# 可视化 2：2D 热图
# ============================================================

def visualize_2d(cube):
    plt.figure()
    slice2d = cube[:, :, 0, 0]
    plt.imshow(slice2d)
    plt.colorbar()
    plt.title("2D Slice (R-G plane, B=0)")
    plt.xlabel("G index")
    plt.ylabel("R index")
    plt.show()


# ============================================================
# 可视化 3：3D 散点
# ============================================================
# ============================================================
# 3D LUT 映射可视化（核心）
# ============================================================

def visualize_lut_mapping(cube):
    """
    显示：
    原始 RGB 坐标 → 映射后 RGB'
    点的颜色 = 原始 RGB
    """

    size = cube.shape[0]

    # 原始 RGB 网格 (0~1)
    r = np.linspace(0, 1, size)
    g = np.linspace(0, 1, size)
    b = np.linspace(0, 1, size)

    R, G, B = np.meshgrid(r, g, b, indexing='ij')

    # 展平
    Rf = R.flatten()
    Gf = G.flatten()
    Bf = B.flatten()

    # 映射后的 RGB'
    mapped = cube.reshape(-1, 3)
    Rm = mapped[:, 0]
    Gm = mapped[:, 1]
    Bm = mapped[:, 2]

    # 使用原始 RGB 作为颜色
    colors = np.stack([Rf, Gf, Bf], axis=1)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(
        Rm, Gm, Bm,
        c=colors,
        s=20
    )

    ax.set_title("3D LUT Mapping Visualization")
    ax.set_xlabel("Mapped R'")
    ax.set_ylabel("Mapped G'")
    ax.set_zlabel("Mapped B'")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_zlim(0, 1)

    plt.show()


# ============================================================
# 主函数
# ============================================================

def main(icc_path):
    with open(icc_path, "rb") as f:
        data = f.read()

    tags = parse_tag_table(data)

    if "A2B0" not in tags:
        print("No A2B0 tag found.")
        return
    AtoB_tags = ["A2B0", # 感知渲染（Perceptual） 会把颜色压缩或扩展，使得变换后看起来自然平滑。
                 "A2B1", # 色度渲染（Colorimetric） 保持原始的色彩和亮度，重点保留准确的色彩匹配。
                 "A2B2"] # 饱和度渲染（Saturation） 则增强色彩的鲜艳度。
    off, length = tags["A2B0"]
    tag_type = data[off:off+4]

    if tag_type != b"mAB ":
        print("A2B0 is not mAB type.")
        return

    cube, grid = parse_mab(data, off)

    print("CLUT grid:", grid)
    print("Cube shape:", cube.shape)

    visualize_1d(cube)
    visualize_2d(cube)
    visualize_lut_mapping(cube)


# ============================================================

if __name__ == "__main__":

    filepath=r"D:\Users\www_0\AppData\Roaming\baidu\BaiduNetdisk\module\ImageViewer\sRGB.icc"
    main(filepath)
    # from icc_extend import load_custom_icc
    # load_custom_icc(filepath)

    