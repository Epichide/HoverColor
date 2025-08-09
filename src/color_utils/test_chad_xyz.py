#!/usr/bin/env python
# -*- coding: utf-8 -*-
import colour
import array
import sys
import struct
import numpy
import numpy as np

import iccinspector
import argparse

from src.color_utils.color_utils import CAM_dict, get_white_point_XYZ

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            prog="Apple Adapted Primaries"
        )
        parser.add_argument(
            "iccfile",
            type=argparse.FileType("rb"),
            nargs="?",
        default = "Display P3.css"
        )

        args = parser.parse_args()

        numpy.set_printoptions(15)

        with args.iccfile as f:
            s = memoryview(f.read())

            iccFile = iccinspector.iccProfile()
            iccFile.read(s)
            illuminant_XYZ= iccFile._pcsilluminant.pcsilluminant.XYZ

            chad = iccFile.tags["tag"][
                numpy.where(iccFile.tags["signature"] == "chad")
            ][0]

            CAT_D65_to_D50 = numpy.reshape(chad.type.value, (3, 3))

            rXYZ = iccFile.tags["tag"][
                numpy.where(iccFile.tags["signature"] == "rXYZ")
            ][0]
            gXYZ = iccFile.tags["tag"][
                numpy.where(iccFile.tags["signature"] == "gXYZ")
            ][0]
            bXYZ = iccFile.tags["tag"][
                numpy.where(iccFile.tags["signature"] == "bXYZ")
            ][0]

            AppleP3D50toXYZ = numpy.transpose(
                [
                    rXYZ.type.value[0].XYZ,
                    gXYZ.type.value[0].XYZ,
                    bXYZ.type.value[0].XYZ
                ]
            )

            adapted_XYZ = numpy.matmul(
                numpy.linalg.inv(CAT_D65_to_D50),
                AppleP3D50toXYZ
            )
            print(
                "The xyY coordinates adapted via the `chad` tag: \n{}".format(
                    colour.XYZ_to_xyY(adapted_XYZ.T)
                )
            )
            print(
                "The XYZ coordinates adapted via the `chad` tag: \n{}".format(
                    (adapted_XYZ.T)
                )
            )
            method="BFD"
            M = CAM_dict[method]

            M_inv = np.linalg.inv(M)
            W_XYZ_from_cone = np.dot(M, illuminant_XYZ)
            scale = np.dot(M,np.dot(CAT_D65_to_D50,M_inv))
            scale  =np.array([
                scale[0, 0],
                scale[1, 1],
                scale[2, 2]
            ])

            W_XYZ_to_cone =W_XYZ_from_cone/scale
            W_XYZ_to=np.dot(M_inv, W_XYZ_to_cone)


            print("src white point XYZ: ", W_XYZ_to)

    except Exception as ex:
        raise ex