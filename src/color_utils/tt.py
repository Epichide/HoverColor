from PIL import Image, ImageCms
import io
import os

if __name__ == "__main__":

    image_path = r"D:\material\DATA\icc\wide-gamut-tests-master\wide-gamut-tests-master\P3-sRGB-blue.jpg"

    src_default_icc_path = r"D:\Users\www_0\AppData\Roaming\baidu\BaiduNetdisk\module\ImageViewer\sRGB.icc"

    dst_icc_path = r"D:\material\DATA\icc\profiles\DisplayP3-v4.icc"

    # 1️⃣ 打开图片
    img = Image.open(image_path)

    # 2️⃣ 读取嵌入 ICC
    icc_bytes = img.info.get("icc_profile")

    if icc_bytes:
        print("使用图片内嵌 ICC")
        src_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc_bytes))
    else:
        print("图片无嵌入 ICC，使用默认 ICC")
        src_profile = ImageCms.getOpenProfile(src_default_icc_path)

    # 3️⃣ 目标 ICC
    dst_profile = ImageCms.getOpenProfile(dst_icc_path)

    # 4️⃣ 构建 transform
    transform = ImageCms.buildTransform(
        src_profile,
        dst_profile,
        img.mode,
        img.mode
    )

    # 5️⃣ 应用变换
    converted_img = ImageCms.applyTransform(img, transform)

    # 6️⃣ 保存输出
    output_path = "converted.jpg"
    converted_img.save(output_path, icc_profile=open(dst_icc_path, "rb").read())

    print("转换完成:", output_path)