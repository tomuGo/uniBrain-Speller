#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

from PyInstaller.__main__ import run
# -F:打包成一个EXE文件
# -w:不带console输出控制台，window窗体格式
# --paths：依赖包路径
# --icon：图标
# --noupx：不用upx压缩
# --clean：清理掉临时文件

if __name__ == '__main__':
        opts = [

                '-n', 'uniBrain-Speller',
                '--clean',
                '-D', '--add-data=..\\GraphicUserInterface\\images;GraphicUserInterface\\images',
                '-D', '--add-data=..\\GraphicUserInterface\\keyboard_list;GraphicUserInterface\\keyboard_list',
                '-D', '--add-data=..\\CommonSystem\\config.pkl;CommonSystem',
                '--paths', 'D:\\Workspace\\uniBrain-Speller\\venv\\Lib\\site-packages',
                '-D', '--add-data=D:\\Workspace\\uniBrain-Speller\\venv\\Lib\\site-packages\\psychopy;psychopy',
                '-D', '--add-data=D:\\Workspace\\uniBrain-Speller\\venv\\Lib\\site-packages\\tables;tables',
                # "--collect -binaries pywin32",
                "..\\GraphicUserInterface\\main_ui.py"
        ]
        run(opts)