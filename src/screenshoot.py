#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: leya
# @Email: no email
# @Time: 2024/11/14 1:40
# @File: screenshoot.py
# @Software: PyCharm
from PyQt5.QtGui import QScreen
from PyQt5.QtWidgets import QApplication


def getAverageColor(x,y):
    window=int(QApplication.desktop().winId())
    screenshoot=QApplication.primaryScreen().grabWindow(window,x-2,y-2,5,5)
    # screenshoot.save('shot.jpg', 'jpg')
    image=screenshoot.toImage()
    color=image.pixelColor(2,2)
    r,g,b=color.red(),color.green(),color.blue()
    return (r,g,b),screenshoot