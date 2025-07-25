#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: Epichide
# @Email: no email
# @Time: 2025/7/17 20:41
# @File: color_utils.py
# @Software: PyCharm


# import colour
# from colour.colorimetry import CCS_ILLUMINANTS
# from colour.models import xy_to_XYZ, xy_to_xyY, xyY_to_XYZ
import numpy as np
# from colour.models.rgb import RGB_COLOURSPACES, RGB_to_XYZ, XYZ_to_RGB

#
# White_ILLUMINANTS_XYZ={
#      "A":[1.0985,1,0.35585],
#     "B":[0.99072,1,0.85223],
#     "C":[0.98074,1,1.18232],
#     "D50":[0.96422,1,0.82521],
#     "D55":[0.95682,1,0.92149],
#     "D65":[0.95047,1,1.08883],
#     "D75":[0.94972,1,1.22638],
#     "E":[1,1,1],
#     "FL2":[0.99186,1,0.67393],
#     "FL7":[0.95041,1,1.08747],
#     "FL11":[1.00962,1,0.6435],
# }

White_ILLUMINANTS_xy={
     "A":[0.44758,0.40745],
    "B":[0.34842,0.35161],
    "C":[0.31006,0.31616],
    "D50":[0.34567,0.3585],
    "D55":[0.33242,0.34743],
    "D60":[0.32168,0.33767],
    "D63":[0.314,0.351],
    "D65":[0.31272,0.32903],
    "D75":[0.29902,0.31485],
    "D93":[0.28315,0.29711],
    "E":[0.33333,0.33333],
    "F1":[0.3131,0.33727],
    "F2":[0.37208,0.37529],
    "F3":[0.4091,0.3943],
    "F4":[0.44018,0.40329],
    "F5":[0.31379,0.34531],
    "F6":[0.3779,0.38835],
    "F7":[0.31292,0.32933],
    "F8":[0.34588,0.35875],
    "F9":[0.37417,0.37281],
    "F10":[0.34609,0.35986],
    "F11":[0.38052,0.37713],
    "F12":[0.43695,0.40441],
    "LED-B1":[0.456,0.4078],
    "LED-B2":[0.4357,0.4012],
    "LED-B3":[0.3756,0.3723],
    "LED-B4":[0.3422,0.3502],
    "LED-B5":[0.3118,0.3236],
    "LED-BH1":[0.4474,0.4066],
    "LED-RGB1":[0.4557,0.4211],
    "LED-V1":[0.456,0.4548],
    "LED-V2":[0.3781,0.3775],
}

RGB_xy={
    "sRGB":[
        [0.640,0.300,0.150],
        [0.330,0.600,0.060],

    ],
    "Rec.709":[
        [0.640, 0.300, 0.150],
        [0.330, 0.600, 0.060],
    ],
    "P3-D65":[#P3-D65 (Display)
        [0.680,0.265,0.150],
        [0.320,0.690,0.060],
    ],
    "P3-DCI":[
        [0.680,0.265,0.150],
        [0.320,0.690,0.060],
    ],
    "P3-D60":[
        [0.680, 0.265, 0.150],
        [0.320, 0.690, 0.060],
    ],
    "SMPTE-C":[
        [0.630,0.310,0.155],
        [0.340,0.595,0.070],
    ],
    "Rec.2020":[
        [0.708,0.170,0.131],
        [0.292,0.797,0.046],
    ],
    "AdobeRGB":[
        [0.640,0.210,0.150],
        [0.330,0.710,0.060]
    ],

}

Gmaut_Illuminant={
    # P3:https://en.wikipedia.org/wiki/DCI-P3
    "sRGB":"D65",
    "Rec.709":"D65",
    "P3-D65":"D65",#P3-D65 (Display)
    "P3-DCI":"D63",#P3-DCI (Theater)
    "SMPTE-C":"D65",
    "Rec.2020":"D65",
    "P3-D60":"D60",#P3-D60 (ACES Cinema)
    "AdobeRGB":"D65",
}

# ACES2065-1
# ACES
# ACEScct
# Adobe RGB (1998)
# Adobe Wide Gamut RGB
# Display P3
# Rec.2020
# ITU-R BT.709
# P3-D65
# DCI-P3
# DCI-P3+

def color_xyY_to_XYZ(xyY):
    '''将xyY转换为XYZ.'''
    xyY = np.asarray(xyY)
    x, y, Y = (xyY[..., i] for i in range(3))
    y=y.clip(1e-3, 1)  # 防止除以0
    Y_y = Y / y
    X = x * Y_y
    Z = (1 - x - y) * Y_y
    XYZ = np.stack((X, Y, Z), axis=-1)
    return XYZ
def color_XYZ_to_xyY(XYZ):
    '''将XYZ转换为xyY.'''
    XYZ = np.asarray(XYZ)
    S=np.sum(XYZ, axis=-1,).clip(1e-10, None)  # 防止除以0
    x= XYZ[..., 0] / S
    y= XYZ[..., 1] / S
    Y= XYZ[..., 1]
    xyY=np.stack((x, y, Y), axis=-1)
    return xyY
def white_xy2XYZ(xy):
    # Y default is 1.0
    z=1-xy[0]-xy[1]
    XYZ=[xy[0]/xy[1],1.0,z/xy[1]]
    return XYZ
def get_white_point_XYZ(illuminant="D65"):
    if illuminant=="E":return [1.0,1.0,1.0]
    white_xy=White_ILLUMINANTS_xy[illuminant]
    white_XYZ=white_xy2XYZ(white_xy)
    return  white_XYZ
    # return WhiteILLUMINANTS[illuminant]
def get_white_point_XYZ_colour(illuminant="D65"):
    illuminant = CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer'][illuminant]
    return xyY_to_XYZ(xy_to_xyY(illuminant))

def compare_white_point_XYZ():
    for illuminant in White_ILLUMINANTS_xy:
        xyz=get_white_point_XYZ(illuminant)
        xyz2=get_white_point_XYZ_colour(illuminant)
        # print(xyz,xyz2)
def range01(RGB):
    RGB=np.array(RGB)
    if (RGB>10).any() :
        RGB=RGB/255
    return RGB
def get_RGB_xyz(gamut="sRGB"):
    # primary RGB' xyz value
    rgb_xy=np.array(RGB_xy[gamut])
    rgb_z=1-rgb_xy[0]-rgb_xy[1]
    rgb_xyz=np.vstack([rgb_xy,rgb_z])
    return rgb_xyz

RGB2XYZ_M_CACHE={}
def get_RGB2XYZ_M(gamut="sRGB"):
    assert  gamut in RGB_xy, gamut+" gamut is not support"
    global RGB2XYZ_M_CACHE
    if gamut in RGB2XYZ_M_CACHE:
        return RGB2XYZ_M_CACHE[gamut]
    rgb_xyz=get_RGB_xyz(gamut)
    rgb_xyz_inv=np.matrix(rgb_xyz).I
    W_XYZ=np.array(get_white_point_XYZ(Gmaut_Illuminant[gamut])).T
    S_RGB=np.dot(rgb_xyz_inv,W_XYZ)
    M=rgb_xyz.copy()
    M[:,0]*=S_RGB[0,0]
    M[:,1]*=S_RGB[0,1]
    M[:,2]*=S_RGB[0,2]
    RGB2XYZ_M_CACHE[gamut]=M
    return M

def get_RGB2XYZ_M_colour(gamut="sRGB"):
    # print(RGB_COLOURSPACES.keys())
    # if gamut=="P3-D65":
    #     gamut="display p3"
    gamut_space = RGB_COLOURSPACES[gamut]
    gamut_space.matrix_RGB_to_XYZ
    M=(gamut_space.matrix_RGB_to_XYZ)
    return M

def compare_RGB2XYZ_M():
    gamuts=["P3-D65","sRGB"]
    for gamut in gamuts:
        M1=get_RGB2XYZ_M(gamut)
        M2=get_RGB2XYZ_M_colour(gamut)
        print("=========")
        print(M1,"\n",M2)
        print("=========")

#------- linear RGB - RGB -----------
#------------------------------------
def color_RGB_to_linearRGB(RGB,gamut="sRGB"):
    """
    ref : https://entropymine.com/imageworsener/srgbformula/
    :param RGB:
    :param gamut:
    :return:
    """
    RGB=range01(RGB)
    if gamut in ["sRGB","P3-D65"]:
        linearRGB=np.where(RGB<0.040448,RGB/12.92,((RGB+0.055)/1.055)**2.4)
    elif gamut in ["AdobeRGB"]:
        linearRGB = np.where(RGB < 0.0556, RGB / 32, RGB**2.2)
    elif gamut in ["P3-DCI"]:
        linearRGB = RGB**2.6
    elif gamut in ["Rec.709", "Rec.2020"]:
        alpha = 1.09929682680944
        beta = 0.018053968510807
        beta_dash = beta * 4.5  # 0.0812428583
        linearRGB = np.where(
            RGB < beta_dash,
            RGB / 4.5,
            ((RGB + (alpha - 1)) / alpha) ** (1 / 0.45)
        )
    else:
        linearRGB = RGB
    return linearRGB

def plot_gamma_curve():
    RGB = np.arange(0, 1, 0.01)
    linearRGB = np.where(RGB < 0.040448, RGB / 12.92, ((RGB + 0.055) / 1.055) ** 2.4)
    import matplotlib.pyplot as plt
    plt.plot(RGB, linearRGB)
    plt.show()

def color_linearRGB_to_RGB(linearRGB,gamut="sRGB"):
    if gamut in ["sRGB", "P3-D65"]:
        RGB=np.where(linearRGB<0.00313,linearRGB*12.92,1.055*linearRGB**(1/2.4)-0.055)
    elif gamut in ["AdobeRGB"]:
        RGB=np.where(linearRGB<0.00174,linearRGB*32,linearRGB**(1/2.2))
    elif gamut in ["P3-DCI"]:
        RGB = linearRGB**(1/2.6)
    elif gamut in ["Rec.709", "Rec.2020"]:
        alpha = 1.09929682680944
        beta = 0.018053968510807
        RGB = np.where(
            linearRGB < beta,
            linearRGB * 4.5,
            alpha * (linearRGB ** 0.45) - (alpha - 1)
        )
    else:
        RGB=linearRGB
    return RGB
def matric_transform(M,vec):
    return np.einsum("...ij,...j->...i", np.array(M, dtype=np.float32), np.array(vec, dtype=np.float32))

#------- RGB - XYZ -----------
#------------------------------------
def color_RGB_to_XYZ(RGB,gamut="sRGB"):
    RGB=range01(RGB)
    linearRGB=color_RGB_to_linearRGB(RGB,gamut)
    M=get_RGB2XYZ_M(gamut)
    # print("linearRGB",linearRGB)
    XYZ=matric_transform(M,linearRGB)
    return XYZ

def color_XYZ_to_RGB(XYZ,gamut="sRGB"):
    global RGB2XYZ_M_CACHE
    if gamut+"-INV" in RGB2XYZ_M_CACHE:
        Minv=RGB2XYZ_M_CACHE[gamut+"-INV"]
    else:
        M = get_RGB2XYZ_M(gamut)
        Minv=np.linalg.inv(M)
        RGB2XYZ_M_CACHE[gamut + "-INV"] = Minv
    linearRGB =matric_transform(Minv,XYZ)
    # print("linearRGB",linearRGB)
    RGB= color_linearRGB_to_RGB(linearRGB,gamut)
    # RGB=color_RGB_to_linearRGB(linearRGB,gamut)
    return RGB


def test_RGB_to_XYZ():
    # test srgb
    # test P3-D65

    for gamut in ["P3-D65","sRGB"]:
        rgb = [0, 0.5, 0.3]
        xyz1 = color_RGB_to_XYZ(rgb,gamut)
        cspace = RGB_COLOURSPACES[gamut]
        xyz2 = colour.RGB_to_XYZ(
            rgb,
            cspace.whitepoint,
            CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['D65'],
            cspace.matrix_RGB_to_XYZ,
            cctf_decoding=cspace.cctf_decoding
        )
        print(xyz1,xyz2)


# --------- XYZ - LMS/ρ, γ,  β ---------
M_dict={
        "HPE-Eq" : np.array([
        [0.38971, 0.68898, -0.07868],
        [-0.22981, 1.18340, 0.04641],
        [0.00000, 0.00000, 1]]),

    "HPE-D65" : np.array([
        [0.40024, 0.70760, -0.08081],
        [-0.22630, 1.16532, 0.04570],
        [0.00000, 0.00000, 0.91822]]),

    "SHARP": np.array([
        [1.2694, -0.0988, -0.1706],
        [-0.8364, 1.8006, 0.0357],
        [0.0297, -0.0315, 1.0018]]),

    "CMCCAT2000" :np.array([[0.7982, 0.3389, -0.1371],
                                      [-0.5918, 1.5512, 0.0406],
                                      [0.0008, 0.2390, 0.9753]]),

    "BFD": np.array([
        [0.8951, 0.2664, -0.1614],
        [-0.7502, 1.7135, 0.0367],
        [0.0389, -0.0685, 1.0296]]),

    "CAT97s": np.array([[0.8562, 0.3372, -0.1934],
                                       [-0.8360, 1.8327, 0.0033],
                                       [0.0357, -0.0469, 1.0112]]),

    "CAT02": np.array([
        [0.7328, 0.4296, -0.1624],
        [-0.7036, 1.6975, 0.0061],
        [0.0030, 0.0136, 0.9834]]),

    "CAM16" : np.array([
        [0.401288, 0.650173, -0.051461],
        [-0.7036, 1.6975, 0.0061],
        [0.0030, 0.0136, 0.9834]]),
    "UCLLMS":np.array([ # https://www.strollswithmydog.com/cone-fundamental-lms-color-space/#footnote
        [0.2106,0.8551,-0.0397],
        [-0.4171,1.1773,0.0786],
        [0,0,0.5168]]),
    "BT2020":np.array([
        [0.3592,0.6976,-0.0358],
        [-0.1922,1.1004,0.0755],
        [0.0070,0.0749,0.08434]]),
    "CIELMS":#https://engineering.purdue.edu/~bouman/grad-labs/Colorimetry/pdf/lab.pdf
        np.array([
        [0.2430,0.8560,-0.0440],
        [-0.3910,1.1650,0.0870],
        [0.01,-0.008,0.5630]]),

    "Vos":np.array([
        [0.15514,0.8560,-0.0440],
        [-0.15514,0.45684,0.03286],
        [0,0,0.01608]]),

}
def color_XYZ_to_LMS(XYZ,method="HPE-Eq"):
    #"method" : HPE-Eq,HPE-D65,BFD,SHARP,CAT90s,CAT20,CAM16
    M=M_dict[method]
    LMS=matric_transform(M,XYZ)
    return  LMS

# ---- XYZ - Lab
def color_XYZ_to_Lab(XYZ,whitpoint="D65"):
    def ffunc(v):
        epsilion=(6/29)**3
        kappa=1/3*(29/6)**2
        return  np.where(v>epsilion,v**(1/3),kappa*v+16/116)
        # return np.where(
        #     v > (24 / 116) ** 3,
        #     np.power(v, 1 / 3),
        #     (841 / 108) * v + 16 / 116,
        # )

    XYZ=np.array(XYZ)
    W_XYZ=get_white_point_XYZ(whitpoint)

    xyz=np.empty_like(XYZ)
    xyz[...,0]=XYZ[...,0]/W_XYZ[0]
    xyz[...,1]=XYZ[...,1]/W_XYZ[1]
    xyz[...,2]=XYZ[...,2]/W_XYZ[2]
    fxyz=ffunc(xyz)
    Lab=np.empty_like(fxyz)
    Lab[...,0]=116*fxyz[...,1]-16
    Lab[...,1]=500*(fxyz[...,0]-fxyz[...,1])
    Lab[...,2]=200*(fxyz[...,1]-fxyz[...,2])
    return  Lab

def color_RGB_to_Lab(RGB,gamut="sRGB"):
    white_point = Gmaut_Illuminant[gamut]
    # white_point="D65"

    XYZ=color_RGB_to_XYZ(RGB,gamut)
    # print("XYZ",XYZ)
    Lab=color_XYZ_to_Lab(XYZ,whitpoint=white_point)
    return  Lab
def color_Lab_to_RGB(Lab,gamut="sRGB"):
    white_point=Gmaut_Illuminant[gamut]
    # white_point="D65"
    XYZ=color_Lab_to_XYZ(Lab,whitpoint=white_point)
    # print("XYZ",XYZ)
    RGB=color_XYZ_to_RGB(XYZ,gamut)
    return  RGB
def color_Lab_to_XYZ(Lab, whitpoint="D65"):
    def ffunc(v):
        delta = (6 / 29)
        return np.where(v > delta, v ** 3, 3*delta**2*(v-4/29) )


    Lab = np.array(Lab)
    W_XYZ = get_white_point_XYZ(whitpoint)
    fxyz=np.empty_like(Lab)

    fxyz[..., 1] = (Lab[..., 0]+16) / 116
    fxyz[..., 0] = fxyz[..., 1]+(Lab[..., 1] /500.0)
    fxyz[..., 2] = fxyz[..., 1]-(Lab[..., 2] / 200.0)

    xyz = ffunc(fxyz)
    XYZ=np.empty_like(xyz)

    XYZ[..., 0] = xyz[..., 0] *W_XYZ[0]
    XYZ[..., 1] = xyz[..., 1] *W_XYZ[1]
    XYZ[..., 2] = xyz[..., 2] *W_XYZ[2]

    return XYZ

def test_XYZ_to_Lab():
    XYZ=[0.3,0.5,0.7]
    Lab1=color_XYZ_to_Lab(XYZ)
    Lab2=colour.XYZ_to_Lab(XYZ)
    print(Lab1,Lab2)
    XYZ1=color_Lab_to_XYZ(Lab1)
    XYZ2=colour.Lab_to_XYZ(Lab2)
    print(XYZ1,XYZ2)

def get_XYZD65_to_AC1C2_M(xyz_illuminant="D65"):
    M1=np.array([
        [1.0503,0.0271,-0.0233],
        [0.0391,0.973,-0.00927],
        [-0.00241,0.00266,0.018]
    ])
    M2=np.array([
        [0,1,0],
        [1,-1,0],
        [0,0.4,-0.4]
    ])
    M=np.dot(M2,M1)
    print(M)
    return M
def color_space_transform(input_color, fromSpace2toSpace):
    """
    Transforms inputs between different color spaces
    """
    dim = input_color.shape

    # Assume D65 standard illuminant
    reference_illuminant = np.array([[[0.950428545]], [[1.000000000]], [[1.088900371]]]).astype(np.float32)
    inv_reference_illuminant = np.array([[[1.052156925]], [[1.000000000]], [[0.918357670]]]).astype(np.float32)

    if fromSpace2toSpace == "srgb2linrgb":
        transformed_color=color_RGB_to_linearRGB(input_color,gamut="sRGB")
    elif "linrgb2srgb" == fromSpace2toSpace:
        transformed_color = color_linearRGB_to_RGB(input_color, gamut="sRGB")
    elif fromSpace2toSpace == "linrgb2xyz" or fromSpace2toSpace == "xyz2linrgb":
        color_RGB_to_XYZ()
        # Assumes D65 standard illuminant
        if fromSpace2toSpace == "linrgb2xyz":
            a11 = 10135552 / 24577794
            a12 = 8788810  / 24577794
            a13 = 4435075  / 24577794
            a21 = 2613072  / 12288897
            a22 = 8788810  / 12288897
            a23 = 887015   / 12288897
            a31 = 1425312  / 73733382
            a32 = 8788810  / 73733382
            a33 = 70074185 / 73733382
        else:
            # Constants found by taking the inverse of the matrix
            # defined by the constants for linrgb2xyz
            a11 = 3.241003275
            a12 = -1.537398934
            a13 = -0.498615861
            a21 = -0.969224334
            a22 = 1.875930071
            a23 = 0.041554224
            a31 = 0.055639423
            a32 = -0.204011202
            a33 = 1.057148933
        A = np.array([[a11, a12, a13],
                      [a21, a22, a23],
                      [a31, a32, a33]]).astype(np.float32)

        input_color = np.transpose(input_color, (2, 0, 1)) # C(H*W)
        transformed_color = np.matmul(A, input_color)
        transformed_color = np.transpose(transformed_color, (1, 2, 0))

    elif fromSpace2toSpace == "xyz2ycxcz":
        input_color = np.multiply(input_color, inv_reference_illuminant)
        y = 116 * input_color[1:2, :, :] - 16
        cx = 500 * (input_color[0:1, :, :] - input_color[1:2, :, :])
        cz = 200 * (input_color[1:2, :, :] - input_color[2:3, :, :])
        transformed_color = np.concatenate((y, cx, cz), 0)

    elif fromSpace2toSpace == "ycxcz2xyz":
        y = (input_color[0:1, :, :] + 16) / 116
        cx = input_color[1:2, :, :] / 500
        cz = input_color[2:3, :, :] / 200

        x = y + cx
        z = y - cz
        transformed_color = np.concatenate((x, y, z), 0)

        transformed_color = np.multiply(transformed_color, reference_illuminant)

    elif fromSpace2toSpace == "xyz2lab":
        input_color = np.multiply(input_color, inv_reference_illuminant)
        delta = 6 / 29
        delta_square = delta * delta
        delta_cube = delta * delta_square
        factor = 1 / (3 * delta_square)

        input_color = np.where(input_color > delta_cube, np.power(input_color, 1 / 3), (factor * input_color + 4 / 29))

        l = 116 * input_color[1:2, :, :] - 16
        a = 500 * (input_color[0:1,:, :] - input_color[1:2, :, :])
        b = 200 * (input_color[1:2, :, :] - input_color[2:3, :, :])

        transformed_color = np.concatenate((l, a, b), 0)

    elif fromSpace2toSpace == "lab2xyz":
        y = (input_color[0:1, :, :] + 16) / 116
        a =  input_color[1:2, :, :] / 500
        b =  input_color[2:3, :, :] / 200

        x = y + a
        z = y - b

        xyz = np.concatenate((x, y, z), 0)
        delta = 6 / 29
        factor = 3 * delta * delta
        xyz = np.where(xyz > delta,  xyz ** 3, factor * (xyz - 4 / 29))

        transformed_color = np.multiply(xyz, reference_illuminant)

    elif fromSpace2toSpace == "srgb2xyz":
        transformed_color = color_space_transform(input_color, 'srgb2linrgb')
        transformed_color = color_space_transform(transformed_color,'linrgb2xyz')
    elif fromSpace2toSpace == "srgb2ycxcz":
        transformed_color = color_space_transform(input_color, 'srgb2linrgb')
        transformed_color = color_space_transform(transformed_color, 'linrgb2xyz')
        transformed_color = color_space_transform(transformed_color, 'xyz2ycxcz')
    elif fromSpace2toSpace == "linrgb2ycxcz":
        transformed_color = color_space_transform(input_color, 'linrgb2xyz')
        transformed_color = color_space_transform(transformed_color, 'xyz2ycxcz')
    elif fromSpace2toSpace == "srgb2lab":
        transformed_color = color_space_transform(input_color, 'srgb2linrgb')
        transformed_color = color_space_transform(transformed_color, 'linrgb2xyz')
        transformed_color = color_space_transform(transformed_color, 'xyz2lab')
    elif fromSpace2toSpace == "linrgb2lab":
        transformed_color = color_space_transform(input_color, 'linrgb2xyz')
        transformed_color = color_space_transform(transformed_color, 'xyz2lab')
    elif fromSpace2toSpace == "ycxcz2linrgb":
        transformed_color = color_space_transform(input_color, 'ycxcz2xyz')
        transformed_color = color_space_transform(transformed_color, 'xyz2linrgb')
    elif fromSpace2toSpace == "lab2srgb":
        transformed_color = color_space_transform(input_color, 'lab2xyz')
        transformed_color = color_space_transform(transformed_color, 'xyz2linrgb')
        transformed_color = color_space_transform(transformed_color, 'linrgb2srgb')
    elif fromSpace2toSpace == "ycxcz2lab":
        transformed_color = color_space_transform(input_color, 'ycxcz2xyz')
        transformed_color = color_space_transform(transformed_color, 'xyz2lab')
    else:
        sys.exit('Error: The color transform %s is not defined!' % fromSpace2toSpace)

    return transformed_color


def color_RGB_to_HSV(rgb):
    """
    将RGB颜色转换为HSV颜色
    RGB值范围为[0, 1]
    HSV中H范围为[0, 1], S和V范围为[0, 1]

    参数:
        rgb: numpy数组，形状可以是(3,)单个像素或(n, m, 3)图像

    返回:
        hsv: numpy数组，与输入形状相同
    """
    rgb = np.asarray(rgb, dtype=np.float64)
    orig_shape = rgb.shape

    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    max_val = np.max(rgb, axis=-1)
    min_val = np.min(rgb, axis=-1)
    delta = max_val - min_val

    hsv = np.zeros_like(rgb)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    # 计算明度V
    v[v>=0] = max_val

    # 计算饱和度S
    mask = max_val != 0
    s[mask] = delta[mask] / max_val[mask]

    # 计算色相H（范围[0,1]）
    mask = delta != 0  # 非灰色区域

    # 红色为主色调
    r_mask = (r == max_val) & mask
    h[r_mask] = (g[r_mask] - b[r_mask]) / delta[r_mask]

    # 绿色为主色调
    g_mask = (g == max_val) & mask
    h[g_mask] = 2.0 + (b[g_mask] - r[g_mask]) / delta[g_mask]

    # 蓝色为主色调
    b_mask = (b == max_val) & mask
    h[b_mask] = 4.0 + (r[b_mask] - g[b_mask]) / delta[b_mask]

    # 将H从[0,6)范围转换为[0,1)
    h[v>=0] /= 6.0
    # 处理负数情况，确保在[0,1)范围内
    h[h < 0] += 1.0

    return hsv.reshape(orig_shape)



def color_HSV_to_RGB(hsv):
    """
    将HSV颜色转换为RGB颜色
    HSV中H范围为[0,1], S和V范围为[0, 1]
    RGB值范围为[0, 1]

    参数:
        hsv: numpy数组，形状可以是(3,)单个像素或(n, m, 3)图像

    返回:
        rgb: numpy数组，与输入形状相同 0-1
    """
    hsv = np.asarray(hsv, dtype=np.float64)
    orig_shape = hsv.shape
    # 统一为二维 (N,3)


    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    i = np.floor(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)

    rgb = np.zeros_like(hsv)
    r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]
    r[i==0]=v[i==0]
    g[i==0]=t[i==0]
    b[i==0]=p[i==0]

    r[i == 1] = q[i == 1]
    g[i == 1] = v[i == 1]
    b[i == 1] = p[i == 1]

    r[i == 2] = p[i == 2]
    g[i == 2] = v[i == 2]
    b[i == 2] = t[i == 2]

    r[i == 3] = p[i == 3]
    g[i == 3] = q[i == 3]
    b[i == 3] = v[i == 3]

    r[i == 4] = t[i == 4]
    g[i == 4] = p[i == 4]
    b[i == 4] = v[i == 4]

    r[i == 5] = v[i == 5]
    g[i == 5] = p[i == 5]
    b[i == 5] = q[i == 5]


    return rgb.reshape(orig_shape)


if __name__ == '__main__':
    # get_XYZD65_to_AC1C2_M()
    print(np.round(np.matrix(get_RGB2XYZ_M(gamut="sRGB")).I,3))
    # print(np.round(get_RGB2XYZ_M(gamut="P3-D65"),8))
    # print(np.round(get_RGB2XYZ_M(gamut="sRGB"),8))
    # lab= color_RGB_to_Lab([55,95,180],gamut="P3-D65")
    # print(color_Lab_to_RGB(lab, gamut="P3-D65")*255)
    # print(color_Lab_to_RGB(lab, gamut="sRGB")*255)

    # lab = color_RGB_to_Lab(np.array([100, 20, 80])/255,gamut="P3-DCI") #24.12231082  46.83461498 -16.35073021
    # lab=np.array([50, -300, -300])
    # rgb =color_Lab_to_RGB(lab,gamut= "P3-DCI")
    # lab2 = color_RGB_to_Lab(rgb,gamut="P3-DCI")
    #
    # print(lab,lab2)
    # print(rgb*255)