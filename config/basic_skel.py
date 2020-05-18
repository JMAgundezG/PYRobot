#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________

from PYRobot.utils import utils
import copy

eths_available = utils.get_all_ip_eths()
ethernet = utils.get_interface()
ip = utils.get_ip_address(ethernet)
host = utils.get_host_name()

comunications_model=["BR","MQ","MC"]

Component_Skel={
"_etc":{
    "name":None,
    "host":None,
    "model":None,
    "robot":None,
    "mode":"public",
    "sys":False,
    "ethernet":"NO_ETH",
    "ip":"0.0.0.0",
    "KEY":"key:user",
    "cls":None,
    "port":4040,
    "MQTT_port":1883,
    "MQTT_uri":None,
    "BROADCAST_port":9999,
    "MULTICAST_port":10000,
    "DISCOVERY_port":9000,
    "def_worker":True,
    "frec":0.2,
    "logging_level":50,
    "_COMP":None,
    "_INTERFACES":[],
    "_CLS_INTERFACES":[],
    "_PROXYS":[],
    "_SUS":[],
    "_EVENTS":[],
    "_TOPICS":[],
    "_EVENTS_":{},
    "_REQUEST_":[]
    },
"_PROC":{
    "status":None,
    "info":None,
    "warnings":[],
    "workers":[],
    "PUB":None,
    "SUS":None,
    "AVAILABLE_TOPICS":[]
    },
"DOCS":{}
}

_OPTIONS=[k for k in Component_Skel["_etc"] if k[0]=="_" ]

def update_skel_dict(skel, mydict):
    #todo si son listas o dict actualizar y no reescribir
    sal=copy.deepcopy(skel)
    for k,v in mydict.items():
        if k in sal["_etc"]:
            sal["_etc"][k]=v
        else:
            sal[k]=v
    return sal

def add_skel_config(skel, config):
    sal=copy.deepcopy(skel)
    for k,v in config.items():
        if k in sal["_etc"]:
            if sal["_etc"][k] is None:
                sal["_etc"][k]=v
            if type(sal["_etc"][k])==list:
                if type(v)!=list:
                    v=[v] 
                if len(v)>0:
                    sal["_etc"][k].extend(v)
            if type(sal["_etc"][k])==dict:
                sal["_etc"][k].update(v)    
            #sal["_etc"][k]=v
        else:
            sal[k]=v if k not in sal else False
    return sal
