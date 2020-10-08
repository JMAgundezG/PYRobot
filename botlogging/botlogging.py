#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
____________
Author: - Paco Andres
Collaborators: - Cristian Vazquez
               - Jose Manuel Agundez
____________

"""

from PYRobot.botlogging.coloramadefs import *
import enum


class LogLevel(enum.Enum):
    """
    Level of logging.
    It can be: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """

    DEBUG = 40
    INFO = 30
    WARNING = 20
    ERROR = 10
    CRITICAL = 0


class Logging(object):
    """
    Custom class that is used as a logger.

    """

    def __init__(self, level: int = 20):
        """
        Constructor of the Logger class
        Params:
            - Level: [Int] (Default = 20) Level of the logger.
        """
        self._etc["LOG_LEVEL"] = level
        self._log_cache = []

    def level_reconfigure(self, level: int = 20):
        """
        Reconfiguration of the Logger object
        Params:
            - Level: [Int] (Default = 20) New level of the logger.
        """

        if level not in LogLevel:
            self.l_warning("Level cannot be changed to {}".format(level))
        else:
            self._etc["LOG_LEVEL"] = level
            for men in self._log_cache:
                if men[0] == LogLevel.DEBUG:
                    self.l_debug(men[1])
                if men[0] == LogLevel.WARNING:
                    self.l_warning(men[1])
                if men[0] == LogLevel.INFO:
                    self.l_info(men[1])
            self._log_cache = []

    def l_debug(self, men):
        if self._etc["LOG_LEVEL"] >= LogLevel.DEBUG:
            print(log_color("[[FG]Debug[SR]] <" + self._etc["name"] + ">::" + str(men)))
        else:
            self._log_cache.append((LogLevel.DEBUG, men))

    def l_warning(self, men):
        if self._etc["LOG_LEVEL"] >= LogLevel.WARNING:
            print(log_color("[[FY]Warning[SR]] <" + self._etc["name"] + ">::" + str(men)))
        else:
            self._log_cache.append((LogLevel.WARNING, men))

    def l_info(self, men):
        if self._etc["LOG_LEVEL"] >= LogLevel.INFO:
            print(log_color("[[FC]Info[SR]] <" + self._etc["name"] + ">::" + str(men)))
        else:
            self._log_cache.append((LogLevel.INFO, men))

    def l_error(self, men):
        if self._etc["LOG_LEVEL"] >= LogLevel.ERROR:
            print(log_color("[[FR]ERROR[SR]] <" + self._etc["name"] + ">::" + str(men)))
            self._PROC["status"] = "ERROR"

    def l_critical(self, men):
        if self._etc["LOG_LEVEL"] >= LogLevel.CRITICAL:
            print(log_color("[[FR]CRITICAL[SR]]:<" + self._etc["name"] + "> " + str(men)))
            self._PROC["status"] = "ERROR"

    def l_print(self, men, handler=False):
        if handler:
            print(log_color("[FG]<" + self._etc["name"] + "> [SR]" + str(men)))
        else:
            print(log_color(str(men)))

    def l_def(self, men, handler=False):
        if handler:
            print(log_color("[FG]<" + self._etc["name"] + "> [SR]" + str(men)))
        else:
            print(log_color(str(men)))
