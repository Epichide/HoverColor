#!/usr/bin/python3
# --*-- coding: utf-8 --*--
# @Author: Epichide
# @Email: no email
# @Time: 2025/8/11 22:49
# @File: file_utils.py
# @Software: PyCharm

import os,sys


def _get_file(relative_path):
    if getattr(sys, 'frozen', False):
        # 打包后环境：使用可执行文件所在目录
        base_path = os.path.join(os.path.dirname(sys.executable))
        return os.path.abspath(os.path.join(base_path, "src", relative_path))
    else:
        # 正常环境：使用当前文件所在目录, exe/interval/
        base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(base_path, "../",relative_path))
