import os
try:
    from .iccinspector import iccProfile,get_plot_xy
    from .color_utils import *
    from .iccinspector_builtin import load_icc, save_icc, show_icc, show_result, warp_file
except:
    from iccinspector import iccProfile,get_plot_xy
    from color_utils import *
    from iccinspector_builtin import load_icc, save_icc, show_icc, show_result, warp_file
import numpy as np
import matplotlib.pyplot as plt
import cv2

def imread(path):
    """
    读取图像文件，返回RGB格式的数组
    :param path: 图像文件路径（支持中文路径）
    :return: RGB格式的数组，范围[0,1]；若读取失败返回None
    """
    try:
        # 1. 以二进制方式读取文件，解决中文路径问题
        # np.fromfile 读取文件为numpy数组，dtype=np.uint8保证读取为8位无符号整数
        img_buffer = np.fromfile(path, dtype=np.uint8)
        
        # 2. 解码二进制数据为BGR格式的图像数组（OpenCV默认解码格式）
        img_bgr = cv2.imdecode(img_buffer, cv2.IMREAD_COLOR)
        
        # 检查图像是否读取成功
        if img_bgr is None:
            raise ValueError(f"无法读取图像文件：{path}")
        
        # 3. 将BGR格式转换为RGB格式（符合常规RGB图像认知）
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        # 4. 将像素值从[0,255]归一化到[0,1]，并转换为float类型
        img_rgb_normalized = img_rgb.astype(np.float32) / 255.0
        
        return img_rgb_normalized
    
    except Exception as e:
        print(f"读取图像时出错：{e}")
        return None
    
def trans_rgb_to_rgb(rgb,gamut_src,gamut_dst):
    """
    转换RGB颜色到目标色域
    :param rgb: 输入RGB颜色，范围[0,1]
    :param gamut_src: 源色域，"sRGB"或"AdobeRGB" 或者 ICC颜色文件
    :param gamut_dst: 目标色域，"sRGB"或"AdobeRGB" 或者 ICC颜色文件
    :return: 转换后的RGB颜色，范围[0,1]
    """
    if os.path.exists(gamut_src):
        load_custom_icc(gamut_src,IS_update_custom=False)
    if os.path.exists(gamut_dst):
        load_custom_icc(gamut_dst,IS_update_custom=False)
    xyz_src,src_white =color_RGB_to_XYZ(rgb,gamut_src)
    tar_white =get_white_point_XYZ(gamut_dst)
    xyz_dst= color_XYZ_to_XYZ(xyz_src,src_white,tar_white)
    rgb_dst = color_XYZ_to_RGB(xyz_dst,gamut_dst)
    return rgb_dst
    
    



def update_custom_icc_cache_proj(gamut_profile_info:dict={},skip_lab_proj=False,IS_update_custom=True):
    """
    更新自定义ICC缓存投影到文件

    Args:
        gamut_profile_info (dict, optional): _description_. Defaults to {}.
        skip_lab_proj (bool, optional): _description_. Defaults to False.
        IS_update_custom (bool, optional): _description_. Defaults to True.
    """
    if not gamut_profile_info :return
    White_ILLUMINANTS_xy["CUSTOM"] = gamut_profile_info["WP xy"][:2]
    white_XYZ=get_white_point_XYZ(White_ILLUMINANTS_xy["CUSTOM"])
    global RGB2XYZ_M_CACHE
    global Degamma_func_CACHE
    global Gamma_func_CACHE
    if IS_update_custom:
        RGB2XYZ_M_CACHE["CUSTOM"] = gamut_profile_info["WP RGB2XYZ_matrix"],white_XYZ
        RGB2XYZ_M_CACHE["CUSTOM-INV"] = gamut_profile_info["WP XYZ2RGB_matrix"],white_XYZ
        x,y, degamma_func, gamma_func = get_plot_xy(
            curvetype=gamut_profile_info["TRC Type"],
            _funcid=gamut_profile_info["TRC FuncID"],
            parameters=gamut_profile_info["TRC Parameters"],
        )
        Degamma_func_CACHE["CUSTOM"] = degamma_func
        Gamma_func_CACHE["CUSTOM"] = gamma_func
    # print(RGB2XYZ_M_CACHE["CUSTOM"])
    # print(RGB2XYZ_M_CACHE["CUSTOM-INV"])
    # generate canvas img
    # 简易进度条对话框
    if skip_lab_proj: return
    from PyQt5.QtWidgets import QDialog, QProgressBar, QVBoxLayout, QLabel, QApplication
    from PyQt5.QtCore import Qt, QEventLoop, QTimer
    from src.Lab import create_lab_proj_cus
    from src.XYZ import create_xyz_proj_cus
    app = QApplication.instance() or QApplication([])
    progress_dialog = QDialog()
    progress_dialog.setWindowFlags(progress_dialog.windowFlags() | Qt.WindowStaysOnTopHint)
    progress_dialog.setWindowTitle("处理中")
    progress_dialog.setFixedSize(300, 80)
    progress_dialog.setWindowModality(Qt.ApplicationModal)

    # 布局和控件
    layout = QVBoxLayout(progress_dialog)
    layout.addWidget(QLabel("生成投影图，请稍候..."))

    progress_bar = QProgressBar()
    progress_bar.setRange(0, 100)
    progress_bar.setValue(0)
    layout.addWidget(progress_bar)

    progress_dialog.show()
    app.processEvents()  # 刷新界面显示

    # 第一个任务
    progress_bar.setValue(30)
    app.processEvents()  # 刷新界面显示
    create_lab_proj_cus(gamut="CUSTOM")
    # 第二个任务
    progress_bar.setValue(70)
    app.processEvents()
    create_xyz_proj_cus(gamut="CUSTOM")
    # 完成
    progress_bar.setValue(100)
    progress_dialog.close()

def _get_gamut_info(ddict):
    gamut_TRC_info = {}
    gamut_profile_info = {}
    if ddict["ProfileDeviceClass"][0] in ["mntr","spac"]:# 显示器和色彩空间
        RGB, linearRGB = ddict["TRC"]["xy"]
        function_str = ddict["TRC"]["function"]
        parameters = ddict["TRC"]["parameters"]
        curvetype = ddict["TRC"]["curvetype"]
        funcid = ddict["TRC"]["funcid"]

        
        # profile_info
        gamut_TRC_info = {
            "TRC-degamma": (RGB, linearRGB),
            "TRC-gamma": (linearRGB, RGB)
        }
        gamut_profile_info = {
            "icc_file": ddict["icc_file"],
            "Gamut Type": "icc",
            "WP illuminant": ddict["WP_Illuminant"],  # White point
            "WP xy": ddict["WP_xyY"],
            "WP XYZ_Y1": ddict["WP_XYZ"],
            # the media white point of a Display class profile ;
            # media white point
            # https://www.color.org/whyd50.xalter
            "WP RGB2XYZ_matrix": np.round(ddict["WP_RGB2XYZ_matix"], 4),
            "WP XYZ2RGB_matrix": np.round(ddict["WP_XYZ2RGB_matrix"], 4),
            "TRC Function": function_str,
            "TRC Parameters": parameters,
            "TRC Type": curvetype,
            "TRC FuncID": funcid,
            # PCS info
            "PCS Illuminant": ddict["PCS_Illuminant"],
            "PCS xy": ddict["PCS_xyY"],
            "PCS XYZ_Y1": ddict["PCS_XYZ"],
        }
    return gamut_profile_info,gamut_TRC_info
    

def load_custom_icc(icc_file,IS_update_custom=False):
    """ 
    desc :  加载自定义ICC文件,并解析其色域信息,存储在全局变量中.ddict

    Args:
        icc_file (_type_): _description_
    Returns:
        _type_: 3个字典, gamut_profile_info,gamut_TRC_info,gamut_info.
    Raises:
        FileNotFoundError: _description_
        Exception: _description_
    """
    global UPDATE_TIME_CACHE
    global CUSTOM_GAMUT_CACHE
    if not os.path.exists(icc_file):
        raise FileNotFoundError(f"ICC 文件不存在: {icc_file}")
    try:
        last_mod_time = os.path.getmtime(icc_file)  # 获取ICC文件的最后修改时间
        if icc_file in UPDATE_TIME_CACHE and last_mod_time == UPDATE_TIME_CACHE[icc_file]:
            print(f"ICC 文件 {icc_file} 未修改，无需更新")
            ddict = CUSTOM_GAMUT_CACHE[icc_file]
        else:
            with open(icc_file, 'rb') as f:
                # 读取文件内容到内存视图
                s = memoryview(f.read())
            testField = iccProfile()
            testField.read(s)
            ddict = testField.get_info()
            ddict["icc_file"] = icc_file
            ddict["ProfileName"] = os.path.basename(icc_file)
    except Exception as e:
        print(f"解析 ICC 失败: {e}")
        raise Exception(f"解析 ICC 失败: {e}")
    
    gamut_profile_info,gamut_TRC_info = _get_gamut_info(ddict)
    
    # == store custom gamut data in color_utils' global variables
    if IS_update_custom:
        keys=[icc_file,"CUSTOM"]
    else:
        keys=[icc_file]
    for keyname in keys:
        White_ILLUMINANTS_xy[keyname] = gamut_profile_info["WP xy"][:2]
        global RGB2XYZ_M_CACHE
        global Degamma_func_CACHE
        global Gamma_func_CACHE
        
        UPDATE_TIME_CACHE[keyname] = last_mod_time
        CUSTOM_GAMUT_CACHE[keyname] = ddict
        RGB2XYZ_M_CACHE[keyname] = gamut_profile_info["WP RGB2XYZ_matrix"],ddict["WP_Illuminant"]
        RGB2XYZ_M_CACHE[keyname+"INV"] = gamut_profile_info["WP XYZ2RGB_matrix"],ddict["WP_Illuminant"]
        x, y, degamma_func, gamma_func = get_plot_xy(
            curvetype=gamut_profile_info["TRC Type"],
            _funcid=gamut_profile_info["TRC FuncID"],
            parameters=gamut_profile_info["TRC Parameters"],
        )
        Degamma_func_CACHE[keyname] = degamma_func
        Gamma_func_CACHE[keyname] = gamma_func
    return gamut_profile_info,gamut_TRC_info,ddict

if __name__ == "__main__":
    icc_file = r"resource\profile\custom_icc.icc"
    default_img_icc=r"D:\Note\CODE\HoverColor\src\resource\icc\sRGB.icc"
    default_monitor_icc=r"D:\Note\CODE\HoverColor\src\resource\icc\sRGB.icc"
    imgfile=r"D:\Note\CODE\HoverColor\src\icon\icon.png"
    prf=load_icc(r"D:\Note\CODE\HoverColor\src\icon\icon.png")
    if prf :
        img_icc=save_icc(prf,warp_file(os.path.dirname(os.path.abspath(__file__)),"profiles/extracted.icc"))
        default_img_icc=img_icc
        # show_icc(prf)
        # print(prf.profile.__dir__())
        print("提取到ICC Profile,保存到:",img_icc)
    else:
        print("未提取到ICC Profile","默认使用:",default_img_icc)
    src_img = imread(imgfile)
    if src_img is None:
        print("读取图像失败")
        exit(1)
    dst_img = trans_rgb_to_rgb(src_img,default_img_icc,default_monitor_icc)
    if dst_img is None:
        print("转换图像失败")
        exit(1)
        
    # show
    f,ax=plt.subplots(1,2)
    ax[0].imshow(src_img)
    ax[0].set_title("src")
    ax[1].imshow(dst_img)
    ax[1].set_title("dst")
    plt.imshow(src_img)
    plt.title("Original Image")
    plt.axis("off")
    
    plt.subplot(1,2,2)
    plt.imshow(dst_img)
    plt.title("Transformed Image")
    plt.axis("off")
    
        
    
    
        
