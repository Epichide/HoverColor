#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: Epichide
# @Email: no email
# @Time: 2025/8/6 20:13
# @File: icc.py
# @Software: PyCharm
import io

from PIL import Image, ImageCms

def show_result(result, space=0):
    for k, v in result.items():
        if isinstance(v, dict):
            print("  " * space, k, ":")
            show_result(v, space + 1)
        elif isinstance(v, list):
            print("  " * space, k, ":", v)
        else:
            print("  " * space, k, ":", v)
def show_icc(prf: ImageCms.ImageCmsProfile):
    show_firsts = ['creation_date', 'copyright', 'manufacturer',
                   'model', 'profile_description', 'viewing_condition', 'version',
                   'header_manufacturer', 'header_model', 'device_class',
                   'connection_space', 'xcolor_space', 'technology', ]
    show_seconds = ['icc_version', 'attributes', 'header_flags', 'profile_id', 'is_matrix_shaper',
                   'colorimetric_intent', 'perceptual_rendering_intent_gamut', 'saturation_rendering_intent_gamut',
                  'colorant_table', 'colorant_table_out', 'intent_supported',
                   'clut', 'icc_measurement_condition', 'icc_viewing_condition','is_intent_supported', 'rendering_intent', 'target', 'screening_description' ]
    show_lasts=[ 'red_colorant', 'green_colorant', 'blue_colorant', 'red_primary', 'green_primary', 'blue_primary',
                   'media_white_point_temperature', 'media_white_point', 'media_black_point', 'luminance',
                   'chromatic_adaptation', 'chromaticity']
    info_dict={}
    for att in prf.profile.__dir__():
        if "__" in att: continue
        if att in show_firsts: continue
        if att in show_lasts: continue
        if att in show_seconds: continue
        show_seconds.append(att)
    def show_att(att,ddict={}):
        try:
            if not hasattr(prf.profile, att): return
            value = prf.profile.__getattribute__(att)
            if "is_intent_supported"==att:
                return

            if att == "device_class":
                # 定义Profile的类型，如'scnr'(扫描仪)、'mntr'(显示器)、'prtr'(打印机)等
                device_classes = {'scnr': 'Scanner', 'mntr': 'Monitor', 'prtr': 'Printer'}
                if value.lower() in device_classes:
                    value += " (" + device_classes[value.lower()] + ")"
            if isinstance(value, dict):
                show_result({att: value})
            else:
                if isinstance(value, str) and '\x00' in value[0]:
                    value="----"
                print(att, ":", value)
                ddict[att]=value
        except Exception as ex:
            ddict[att] = "ERROR"
            print(att, ":", "ERROR")
    info_dict["first"]={}
    info_dict["second"]={}
    info_dict["basic"]={}
    for att in show_firsts:
        show_att(att,info_dict["first"])
    print("="*30)
    for att in show_seconds:
        show_att(att,info_dict["second"])
    print("="*30)
    for att in show_lasts:
        show_att(att,info_dict["basic"])
    return info_dict

def load_icc(icc_path):
    if icc_path.endswith('.icc') or icc_path.endswith('.icm') :
        prf = ImageCms.getOpenProfile(icc_path)
    else:
        image = Image.open(icc_path)
        icc = image.info.get('icc_profile')
        f = io.BytesIO(icc)
        prf = ImageCms.ImageCmsProfile(f)
    # save icc profile
    bb=prf.tobytes()
    with open("extracted.icc","wb") as f:
        f.write(bb)
    return prf

if __name__ == '__main__':
    # imgi=imread("glossy.png")
    # # Creating sRGB profile
    # prf = ImageCms.getOpenProfile(r"Display P3.icc")
    # img = Image.fromarray(imgi)
    # img.save("dispalyP3.jpg", icc_profile=profile.tobytes())
    # profile = ImageCms.getOpenProfile(r"E:\code\15-flashlight\huawei.icc")
    # img = Image.fromarray(imgi)
    # img.save("huawei.jpg", icc_profile=profile.tobytes())
    # image = Image.open("huawei.jpg")
    # icc = image.info.get('icc_profile')
    # f = io.BytesIO(icc)
    # prf = ImageCms.ImageCmsProfile(f)
    prf=load_icc(r"ip16-IMG_0122.JPG")
    show_icc(prf)
    print(prf.profile.__dir__())