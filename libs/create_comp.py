#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ____________developed by paco andres____________________
import sys
import os
import time
import copy
from PYRobot.libs.proxy import Proxy
import PYRobot.libs.config_comp as conf
import PYRobot.libs.utils as utils
from PYRobot.libs.botlogging.coloramadefs import P_Log
import PYRobot.libs.parser as parser


robots_dir=utils.get_PYRobots_dir()
dir_comp="components/"



def Get_General(robot_dir):
    dir_etc=robots_dir+robot_dir+"/etc/"
    general=conf.get_conf(dir_etc+"general.json")
    return general

def Get_Instances(dir_etc):
    instances=conf.get_conf(dir_etc+"/instances.json")
    print(instances)
    try:
        return instances
    except:
        P_Log("[FR] [ERROR][FW] {} Not found in {}/instances".format(component,dir_etc))
        exit()

class Comp_Create(object):
    def __init__(self,model,general,comp,config_comp):
        self.model=model
        self.general=general
        self.component=comp
        self.instance,errors=parser.instance_check(config_comp)
        if len(errors)==0:
            P_Log("[FY] component syntactic checking [FG] [OK]")
        else:
            for err in errors:
                P_Log("[FR] [ERROR][FY] Syntactic  in {}-->{}".format(err[0],err[1]))
            exit()
        self.component=conf.Create_skel(self.model,self.component,self.general,self.instance)
        self.robot=self.component["_etc"]["robot"]

    def Get_Component(self):
        return self.component




    