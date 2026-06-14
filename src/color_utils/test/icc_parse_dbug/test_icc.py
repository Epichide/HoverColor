from PIL import ImageCms
import lcms2

# 打开ICC配置文件
profile = ImageCms.getOpenProfile(r"D:\Note\CODE\HoverColor\src\resource\icc\sRGB.icc")
lcms_handle = profile.profile

# 获取ICC配置基本头部信息
print("配置文件大小:", lcms2.ICCProfileGetSize(lcms_handle))
print("设备类:", lcms2.ICCProfileGetDeviceClass(lcms_handle))
print("色彩空间:", lcms2.ICCProfileGetColorSpace(lcms_handle))
print("PCS空间:", lcms2.ICCProfileGetPCS(lcms_handle))

# 遍历读取所有Tag签名
tag_count = lcms2.ICCProfileGetTagCount(lcms_handle)
print(f"ICC总Tag数量：{tag_count}")

for i in range(tag_count):
    tag_sig = lcms2.ICCProfileGetTagSignature(lcms_handle, i)
    print(f"Tag{i} 签名: {tag_sig.decode('ascii')}")
    
    # 获取Tag原始二进制数据
    tag_data = lcms2.ICCProfileReadTag(lcms_handle, tag_sig)
    # 可自行解析Tag二进制结构：rXYZ、gXYZ、bXYZ、wtpt、rTRC、gTRC、bTRC、A2B0、B2A0等