import colour

# 加载ICC
profile = colour.io.read_ICC_profile(r"D:\Note\CODE\HoverColor\src\resource\icc\sRGB.icc")

# 基础信息
print("ICC名称:", profile.description)
print("制造商:", profile.manufacturer)
print("设备类型:", profile.device_class)

# 核心色彩转换Tag（你自研转换需要的全部数据）
white_point = profile.media_white_point  # wtpt 白点
r_xyz = profile.red_matrix
g_xyz = profile.green_matrix
b_xyz = profile.blue_matrix

# TRC Gamma曲线
red_trc = profile.red_tone_reproduction_curve
green_trc = profile.green_tone_reproduction_curve
blue_trc = profile.blue_tone_reproduction_curve

# 正向、反向3DLUT
if hasattr(profile, "A2B0"):
    print("A2B0 LUT维度", profile.A2B0.dimensions)
if hasattr(profile, "B2A0"):
    print("B2A0 LUT维度", profile.B2A0.dimensions)