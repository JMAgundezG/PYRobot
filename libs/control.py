#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________

from gevent import monkey
monkey.patch_all(thread=False)
import time
import os
import threading
from threading import Thread
from termcolor import colored
from PYRobot.botlogging import botlogging
from PYRobot.libs.discovery_comp import discovery
import PYRobot.utils as utils
from PYRobot.libs.proxy import Proxy
from PYRobot.utils.utils_mqtt import mqtt_alive
from PYRobot.utils.utils import show_PROC
from PYRobot.libs.publication import Publication
from PYRobot.libs.suscription import Suscriptions
import copy
import types
import json

RETRYS=10
ATTEMPS=20

Pub_def_skel="""
def {0}_PUB(self,val=None):
    if val is not None:
        self.{0}=val
    return self.{0}    
"""

Pub_topic_skel="""
def {0}_PUB(self,val=None):
    if val is not None:
        self.{0}=val
    self._PROC["PUB"].Pub("{0}",self.{0})
    return self.{0}    
"""

Pub_event_skel="""
def {0}_PUB(self):
    self.{0}=[k for k,v in self._etc["{1}"]["{0}"].items() if self._event_check(v)==True]
    self._PROC["PUB"].Pub("{0}",self.{0})
    #print(self.{0})
"""

def create_fuction(obj,skel):
    fun_name=skel.split("(")[0]
    fun_name=fun_name.split("def ")[1]
    #fun_name=fun_name.replace("def ","").replace("\n","")
    #print(skel)
    exec(skel)
    #print("[{}]".format(fun_name))
    obj.__dict__[fun_name] = types.MethodType(eval(fun_name), obj)
     
def threaded(fn,prefix=""):
    """To use as decorator to make a function call threaded."""

    def wrapper(*args, **kwargs):
        if prefix!="":
            name=prefix+"_"+fn.__name__
        else:
            name=fn.__name__
        thread = Thread(target=fn, args=args,name=name, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

def server_PUB_SUS(obj):
    name=obj._etc["name"]
    #loading topics and events
    uri=obj._etc["MQTT_uri"]
    broadcast_port=obj._etc["BROADCAST_port"]
    #creamos servicios de publicacion suscripcion
    obj._PROC["PUB"]=Publication(name,uri,broadcast_port)
    obj._PROC["SUS"]=Suscriptions(name,uri,broadcast_port,obj._Handler_Mqtt,obj._Handler_Broadcast)

def prepare_topics_suscriptors(obj):
    name=obj._etc["name"]
    #creamos servicios de publicacion suscripcion
    #cargamos topics
    obj._PROC["PUB"].add_topics("TOPICS",*obj._etc["_TOPICS"])
    obj._PROC["PUB"].add_topics("EVENTS",*obj._etc["_EVENTS"])
    
    #actualizamos los _TOPICS _EVENTS quitando el comunicator
    obj._etc["_TOPICS"]=[x.split("::")[1] for x in obj._etc["_TOPICS"]]
    obj._etc["_EVENTS"]={k.split("::")[1]:v for k,v in obj._etc["_EVENTS"].items()}
    
    # creamos funciones de publicacion
    #print(obj._etc)
    topics=obj._etc["_TOPICS"]
    events=list(obj._etc["_EVENTS"])
    for topic in topics:
        create_fuction(obj,Pub_topic_skel.format(topic))
    for event in events:
        create_fuction(obj,Pub_event_skel.format(event,"_EVENTS"))
    available_topics=[x for x in obj._PROC["AVAILABLE_TOPICS"] if x not in topics+events]
    for topic in available_topics:
        create_fuction(obj,Pub_def_skel.format(topic))
    del(obj._PROC["AVAILABLE_TOPICS"])

    #conectar subcriptores
    obj._PROC["SUS"].add_suscribers(**obj._etc["_SUS"])
 
def _first_val_suscriptors(obj):
    #print("first vals ",obj._etc["name"])
    suscribers=obj._PROC["SUS"].get_suscribers()
    robot=obj._etc["robot"]
    first=obj._PROC["SUS"].get_first()
    attemps=ATTEMPS
    while len(first)>0 and attemps>0:
        publicators=obj.dsc_get(robot+"/*/Topics")
        if len(publicators)>0:
            vals={t:v for t,v in publicators.items() if t in first}
            first=[t for t in first if t not in publicators]
            #print("suscribers",suscribers)
            #print("publicators",publicators)
            #print("first",first)
            #print("vals",vals)
            for k,v in vals.items():
                setattr(obj,suscribers[k],v)                
                #print("new first",first)
            obj._PROC["SUS"].first=first
        first=obj._PROC["SUS"].get_first()
        time.sleep(0.2)
        attemps=attemps-1
    if len(first)==0:
        obj.L_info("Suscriptors initialized")
    else:
        obj.L_info("Suscriptors {} not initialized".format(first))
        
def get_conectors(obj):
    request=obj._etc["_REQUEST_"]
    proxys=obj._etc["_PROXYS"]
    attemps=ATTEMPS
    while attemps>0:
        available_interfaces=obj.dsc_get(obj._etc["robot"]+"/*/InterfacesOK")
        PROXYS={a:available_interfaces[prox] for a,prox in proxys.items() if prox in available_interfaces}
        if len(PROXYS)==len(proxys):
            attemps=0
        else:
            attemps=attemps-1
            if attemps%5==0:
                obj.L_print("Component waiting for PROXYS {}".format(proxys),True)
        time.sleep(0.3)
    PROXYS={attr:Proxy(uri) for attr,uri in PROXYS.items() if Proxy(uri)}
    proxys={attr:prox for attr,prox in proxys.items() if attr in PROXYS}
    for attr,Prox in PROXYS.items():
        setattr(obj,attr,Prox)
    obj._etc["_PROXYS"]=proxys
    errors=[x for x in request if x not in PROXYS]    
    if len(errors)>0:
        obj.L_error("_REQUEST_ {} not satified".format(errors))
        return False
    if len(proxys)!=len(PROXYS):
        obj.L_warning("{} have not conneted".format([x for x in proxys if x not in PROXYS]))
    obj._PROC["status"]="OK"

# Class control component
class Control(botlogging.Logging,discovery):
    """ This class provide threading funcionality to all object in node.
        Init workers Threads and PUB/SUB thread"""
        
    def __init__(self):
        # esto se ejecuta antes que el init del componente, asi podemos cargar logs
        botlogging.Logging.__init__(self)
        self.worker_run=self._etc.get("def_worker",True)
        discovery.__init__(self,self._etc["DISCOVERY_port"])
        server_PUB_SUS(self)
        self._PROC["status"]="INIT"

    def __post_init__(self):
        #esto se ejecuta despues del init del componente 
        prepare_topics_suscriptors(self)
        self.dsc_enabled()
        self._PROC["PUB"].Start()
        self._PROC["SUS"].Start()
        # conectar primeros valores a los suscriptores
        if len(self._etc["_SUS"])>0 and self._PROC["status"]!="ERROR":
            threaded(_first_val_suscriptors(self))  
        # conectores proxy
        get_conectors(self)
        

    def start_worker(self, fn, *args):
        """ Start all workers daemon"""
        if type(fn) not in (list, tuple):
            fn = (fn,)
        if self.worker_run:
            for func in fn:
                name=self._etc["name"]+"."+func.__name__
                t = threading.Thread(target=func,name=name, args=args)
                t.setDaemon(True)
                self._PROC["workers"].append(t)
                self.L_info("{} worker Started".format(func.__name__))
                t.start()

           
#Implementataions for Control Interface
    def Get_INFO(self):
        data={"_etc":{},"_PROC":{}}
        data["_etc"]["name"]=self._etc["name"]
        data["_etc"]["ethernet"]=self._etc["ethernet"]
        data["_etc"]["host"]=self._etc["host"]
        data["_PROC"]["PID"]=self._PROC["PID"]
        data["_PROC"]["info"]=self._PROC["info"]
        data["_PROC"]["warnings"]=self._PROC["warnings"]
        data["_PROC"]["PUB"]=self._PROC["PUB"].get_topics()
        data["_PROC"]["SUS"]=self._PROC["SUS"].get_suscribers()
        data["_PROC"]["PROXYS"]=self._etc["_PROXYS"]
        data["_PROC"]["status"]=self._PROC["status"]
        data["_PROC"]["MQTT_uri"]=self._etc["MQTT_uri"]
        return data

        
    def show_PROC(self):
        show_PROC(self.Get_INFO())
        
    def get_PROC(self):
        return self._PROC

    def shutdown(self):
        self._PROC["SERVER"].stop()
        return self._etc["name"]

    def Set_Logging(self,level=20):
        if "logging_level" not in self._etc:
            self._etc["logging_level"]=50
        if level==0:
            level=self._etc["logging_level"]
        self.Level_reconfigure(level)
        self.L_info("Logging level change. new level:{}".format(level))
        
    def hello(self):
        return "hi"

    def get_name(self):
        return self._etc["name"]
    
    def get_topics_values(self,*topics):
        pass

# Implementations for publicators and  suscribers

    def Define_Topics(self,*topics):
        self._PROC["AVAILABLE_TOPICS"].extend(topics)
        for t in topics:
            if t not in self.__dict__:
                setattr(self,t,None)
            
    def Request_Proxy(self):
        pass

    def _event_check(self,fn):
        try:
            return eval(fn)
        except Exception as ex:
            #print(str(ex))
            return "ERR"
        
    def _load_frist_suscriptors(self):
        trays=10
        
        available_topics=self.dsc_get(self._etc["robot"]+"/*/Topics")
        print("AVAILABLE",available_topics)
        
    def _Handler_Broadcast(self, payload, address):
        payload,tipe,date=json.loads(payload.decode())
        if self._etc["name"] not in payload:
            #print("BR RECEIVE {}    {} {} {}".format(self._etc["name"],payload,tipe,date))
            suscriber="{}/{}".format(payload[0],payload[1])
            data=payload[2]
            self._PROC["SUS"].del_first(suscriber)
            if suscriber in self._PROC["SUS"].suscribers:
                setattr(self,self._PROC["SUS"].suscribers[suscriber],data)
            if tipe=="EVENTS":
                attr=payload[1]
                for ev in data:
                    try:
                        func="self.on_{}_{}()".format(attr,ev)
                        eval(func)
                    except:
                        #print("err",func)
                        pass
    
    def _Handler_Mqtt(self,client, userdata, msg):
        data,tipe,date=json.loads(msg.payload.decode())
        payload={msg.topic:data}
        #print("MQ REC {}  _______________{} {} {}".format(self._etc["name"],payload,tipe,date))
        r,c,attr=msg.topic.split("/")
        self._PROC["SUS"].del_first(msg.topic)
        if msg.topic in self._PROC["SUS"].suscribers:
            setattr(self,self._PROC["SUS"].suscribers[msg.topic],data)
        if tipe=="EVENTS":
            for ev in data:
                try:
                    func="self.on_{}_{}()".format(attr,ev)
                    eval(func)
                except:
                    #print("err",func)
                    pass
                    
    
    def _Handler_multicast(self, payload, address):
        print("multi: ",payload)