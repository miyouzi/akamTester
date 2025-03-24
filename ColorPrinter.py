#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2025/03/25
# @Author  : Miyouzi & oldip
# @File    : ColorPrinter.py
# @Software: PyCharm

import ctypes, subprocess, platform, os
from termcolor import cprint
import sys
import threading

print_lock = threading.Lock()

def color_print(msg, status=0):
    with print_lock:
        # status 三个设定值, 0 为一般输出, 1 为错误输出, 2 为成功输出
        green = False

        def succeed_or_failed_print():
            check_tty = subprocess.Popen('tty', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            check_tty_return_str = check_tty.stdout.read().decode("utf-8").strip()
            if 'Windows' in platform.system() and check_tty_return_str in ('/dev/cons0', ''):
                clr = Color()
                if green:
                    clr.print_green_text(msg)
                else:
                    clr.print_red_text(msg)
            else:
                if green:
                    cprint(msg, 'green', attrs=['bold'], flush=True)
                else:
                    cprint(msg, 'red', attrs=['bold'], flush=True)

        if status == 0:
            print(msg, flush=True)
        elif status == 1:
            # 为 1 错误输出
            green = False
            succeed_or_failed_print()
        else:
            # 为 2 成功输出
            green = True
            succeed_or_failed_print()


# 用於Win下染色輸出，代碼來自 https://blog.csdn.net/five3/article/details/7630295
class Color:
    ''' See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winprog/winprog/windows_api_reference.asp
    for information on Windows APIs.'''

    def __init__(self):
        self.FOREGROUND_RED = 0x04
        self.FOREGROUND_GREEN = 0x02
        self.FOREGROUND_BLUE = 0x01
        self.FOREGROUND_INTENSITY = 0x08
        STD_OUTPUT_HANDLE = -11
        self.handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    def set_cmd_color(self, color):
        """(color) -> bit
        Example: set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_INTENSITY)
        """
        bool = ctypes.windll.kernel32.SetConsoleTextAttribute(self.handle, color)
        return bool

    def reset_color(self):
        self.set_cmd_color(self.FOREGROUND_RED | self.FOREGROUND_GREEN | self.FOREGROUND_BLUE)

    def print_red_text(self, print_text):
        self.set_cmd_color(self.FOREGROUND_RED | self.FOREGROUND_INTENSITY)
        print(print_text, flush=True)
        self.reset_color()

    def print_green_text(self, print_text):
        self.set_cmd_color(self.FOREGROUND_GREEN | self.FOREGROUND_INTENSITY)
        print(print_text, flush=True)
        self.reset_color()
