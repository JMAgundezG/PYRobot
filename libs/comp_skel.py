#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________

from PYRobot.libs import utils

eths_available = utils.get_all_ip_eths()
ethernet = utils.get_interface()
ip = utils.get_ip_address(ethernet)
host = utils.get_host_name()
broadcast_port=9999


General_Skel={
    "robot":None,
    "model":None,
    "sys":False,
    "KEY":"key:user",
    "port":4040,
    "MQTT_port":1883,
    "MQTT_uri":"0.0.0.0:0",
    "broadcast_port":9999,
    "logging_level":20
}

Component_Skel={
"_etc":{
    "name":"Noname",
    "host":host,
    "model":None,
    "robot":"PYRobot",
    "mode":"public",
    "sys":False,
    "ethernet":ethernet,
    "ip":"0.0.0.0",
    "KEY":"key:user",
    "dir_comp":"",
    "component":None,
    "cls":None,
    "port":4040,
    "MQTT_port":1883,
    "MQTT_uri":None,
    "EMIT_port":10000,
    "broadcast_port":broadcast_port,
    "def_worker":True,
    "frec":0.2,
    "public_sync":False,
    "running":"stop",
    "logging_level":50,
    "_INTERFACES":[],
    "_REQ":{},
    "_PUB":[],
    "_SUB":{},
    "_PUB_EVENTS":{},
    "_SUB_EVENTS":{},
    "_EMIT":[],
    "_RECEIVE":{},
    "_EMIT_EVENTS":{},
    "_RECEIVE_EVENTS":{}
    },
"_PROC":{
    "status":None,
    "requires":"WAITTING",
    "pid":None,
    "info":None,
    "warnings":[],
    "workers":[],
    "PUB":None,
    "SUB":None,
    "EMIT":None,
    "RECEIVE":None,
    "CONTROL":None
    },
"DOCS":{}
}

_OPTIONS=[k for k in Component_Skel["_etc"] if k[0]=="_" ]+["_LOCAL_CONFIG"]
