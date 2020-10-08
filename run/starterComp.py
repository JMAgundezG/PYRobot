#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ____________developed by paco andres____________________
import sys
import os
import time
import copy
import importlib
from PYRobot.libs.server import Start_Server
from PYRobot.libs.proxy import Proxy
import PYRobot.utils.utils as utils
import PYRobot.utils.utils_mqtt as utils_mqtt
from PYRobot.botlogging.coloramadefs import P_Log


robots_dir=utils.get_PYRobots_dir()


def find_MQTT(mosquito_uri):

    if utils.mqtt_alive(mosquito_uri):
        #P_Log("[FY] BROKER MQTT Located on {} [[FG]OK[FY]]".format(mosquito_uri))
        pass
    else:
        P_Log("[FY] BROKER MQTT local NOT Located [[FY]ERROR[FW]]")
        mosquito_uri="0.0.0.0:0"
    return mosquito_uri

class Comp_Starter(object):
    def __init__(self,comp):
        self.robot=comp["_etc"]["robot"]
        self.robot_name=comp["_etc"]["name"]
        self.component=comp
        #broadcast_port=comp["_etc"]["BROADCAST_port"]
        eth,ip=utils.set_eth_ip(self.component["_etc"]["ethernet"])
        self.component["_etc"]["ip"]=ip
        self.component["_etc"]["ethernet"]=eth
        #mqtt si hay topics
        #self.Get_MQTT()

        module,cls=self.component["_etc"]["cls"].split("::")
        mod = importlib.import_module(module)
        self.component["_etc"]["cls"]=getattr(mod,cls)
        interfaces=self.component["_etc"]["_INTERFACES"]
        self.component["_etc"]["_INTERFACES"]=[]
        
        for interface in interfaces:
            module,cls=interface.split("::")
            mod = importlib.import_module(module)
            self.component["_etc"]["_INTERFACES"].append(getattr(mod,cls))
        numports=len(self.component["_etc"]["_INTERFACES"])+1
        port=self.component["_etc"]["port"]
        self.component["_etc"]["port"]=utils.get_free_ports(ip,port,numports)
        
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
        time.sleep(0.1)

    
