#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ____________developed by paco andres____________________
import sys
import os
import time
import copy
import importlib
from PYRobot.libs.server import Run_Server,Start_Server
from PYRobot.libs.proxy import Proxy
import PYRobot.libs.config_comp as conf
import PYRobot.libs.utils as utils
import PYRobot.libs.utils_mqtt as utils_mqtt
from PYRobot.libs.botlogging.coloramadefs import P_Log
import PYRobot.libs.parser as parser


robots_dir=utils.get_PYRobots_dir()

def find_MQTT(mosquito_uri):

    if utils.mqtt_alive(mosquito_uri):
        #P_Log("[FY] BROKER MQTT Located on {} [[FG]OK[FY]]".format(mosquito_uri))
        pass
    else:
        P_Log("[FY] BROKER MQTT local NOT Located [[FY]ERROR[FW]]")
        mosquito_uri="0.0.0.0:0"
    return mosquito_uri


def Get_General(robot_dir):
    dir_etc=robots_dir+robot_dir+"/etc/"
    general=conf.get_conf(dir_etc+"general.json")
    return general

def Get_Instance(robot_dir,component):
    dir_etc=robots_dir+robot_dir+"/etc/"
    instances=conf.get_conf(dir_etc+"instances.json")
    try:
        return instances[component]
    except:
        P_Log("[FR] [ERROR][FW] {} Not found in {}/instances".format(component,robot_dir))
        exit()

class Comp_Starter(object):
    def __init__(self,comp):
        self.robot=comp["_etc"]["robot"]
        self.robot_name=comp["_etc"]["name"]
        self.component=comp
        broadcast_port=comp["_etc"]["broadcast_port"]
        ethernets=conf.get_ethernets()
        if self.component["_etc"]["ethernet"] in ethernets:
            self.component["_etc"]["ip"]=ethernets[self.component["_etc"]["ethernet"]]
        else:
            self.component["_etc"]["ethernet"]=list(ethernets)[0]
            self.component["_etc"]["ip"]=list(ethernets.values())[0]
        #mqtt si hay topics
        self.Get_MQTT()

        module,cls=self.component["_etc"]["cls"].split("::")
        mod = importlib.import_module(module)
        self.component["_etc"]["cls"]=getattr(mod,cls)
        interfaces=self.component["_etc"]["_INTERFACES"]
        self.component["_etc"]["_INTERFACES"]=[]
        
        for interface in interfaces:
            module,cls=interface.split("::")
            mod = importlib.import_module(module)
            self.component["_etc"]["_INTERFACES"].append(getattr(mod,cls))
        #print(self.component)
        
        
    def Get_MQTT(self):
        MQTT="{}:{}".format(self.component["_etc"]["ip"],
                self.component["_etc"]["MQTT_port"])
        MQTT_uri=find_MQTT(MQTT)
        if MQTT_uri!="0.0.0.0:0":
            self.component["_etc"]["MQTT_uri"]=MQTT_uri
        else:
            P_Log("[Warning] Broker {} not available".format(MQTT))
            self.component["_etc"]["MQTT_uri"]=MQTT_uri

    def start(self):
        
        Start_Server(self.component)
        time.sleep(0.3)

    def run(self):
        Run_Server(self.component)
        #time.sleep(0.3)

    
