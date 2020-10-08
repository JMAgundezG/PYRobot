#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
____________
Author: - Paco Andres
Collaborators: - Cristian Vazquez
               - Jose Manuel Agundez
____________

"""
from colorama import Cursor, Fore, Back, Style
import re

STYLE = re.compile("[[][FBS][A-Z][]]")
print(Style.RESET_ALL)

color = {"[FR]": Fore.RED,
         "[FY]": Fore.YELLOW,
         "[FB]": Fore.BLUE,
         "[FG]": Fore.GREEN,
         "[FM]": Fore.MAGENTA,
         "[FC]": Fore.CYAN,
         "[FW]": Fore.WHITE,
         "[FN]": Fore.BLACK,
         "[FS]": Fore.RESET,
         "[BB]": Back.BLUE,
         "[BR]": Back.RED,
         "[BG]": Back.GREEN,
         "[BY]": Back.YELLOW,
         "[BM]": Back.MAGENTA,
         "[BC]": Back.CYAN,
         "[BW]": Back.WHITE,
         "[BS]": Back.RESET,
         "[SD]": Style.DIM,
         "[SN]": Style.NORMAL,
         "[SB]": Style.BRIGHT,
         "[SR]": Style.RESET_ALL
         }


def pos(x, y):
    return Cursor.POS(x, y)


def up(n):
    return Cursor.UP(n)


def down(n):
    return Cursor.DOWN(n)


def forward(n):
    return Cursor.FORDWARD(n)


def back(n):
    return Cursor.BACK(n)


def log_color(message):
    colors = [s for s in STYLE.findall(message) if s in color]
    for s in colors:
        message = message.replace(s, color[s])
    return message + Style.RESET_ALL


def raw_log_color(message):
    colors = [s for s in STYLE.findall(message) if s in color]
    for s in colors:
        message = message.replace(s, "")
    return message


def p_log(message, ln=True):
    if ln:
        print(log_color(message))
    else:
        print(log_color(message), end="")


def c_err(condition, message):
    try:
        assert not condition
    except AssertionError:
        p_log("[FR][ERROR][FY] Critical: [FW]{}".format(message))
        exit()
    except BaseException:
        p_log("[FR] Error not evaluable: {}".format(message))
