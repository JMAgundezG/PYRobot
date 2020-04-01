#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________

from gevent import monkey
monkey.patch_all(thread=False)
import time
import os
import threading
from threading import Thread
from termcolor import colored
from PYRobot.libs.botlogging import botlogging
from PYRobot.libs.discovery_comp import discovery
import PYRobot.libs.utils as utils
from PYRobot.libs.proxy import Proxy
from PYRobot.libs.utils_mqtt import mqtt_alive
from PYRobot.libs.publication_mqtt import Publication
from PYRobot.libs.subscription_mqtt import subscriptions
from PYRobot.libs.broadcast_emitter import Emitter
from PYRobot.libs.broadcast_receiver import Receiver
import copy

RETRYS=50

def threaded(fn):
    """To use as decorator to make a function call threaded."""

    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args,name=fn.__name__, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

def connect_component(obj):
    obj._PROC["running"]="stop"
    obj.worker_run=obj._etc.get("def_worker",True)

    #loading topics and events
    name=obj._etc["name"]
    robot=obj._etc["robot"]
    uri=obj._etc["MQTT_uri"]
    sync=obj._etc["public_sync"]
    frec=obj._etc["frec"]
    emit_port=obj._etc["EMIT_port"]
    components_online=obj.dsc_get(obj._etc["robot"]+"/*/Name")
    if name in components_online:
        obj.L_error("{} is on line".format(name))
        exit()
    # ver si el robot esta en linea y traer configuracion

    #loading publications MQTT
    if len(obj._etc["_PUB"])+len(obj._etc["_PUB_EVENTS"])>0:
        #preguntar por broker.
        obj._PROC["PUB"]=Publication(name,uri,obj,sync,frec)
        obj._PROC["PUB"].add_topics(*obj._etc["_PUB"])
        for ent,events in obj._etc["_PUB_EVENTS"].items():
            for e in events:
                obj._PROC["PUB"].add_event(ent,e)
        if sync:
            obj._PROC["PUB"].start()

    #loading publications broadcast emitter
    if len(obj._etc["_EMIT"])+len(obj._etc["_EMIT_EVENTS"])>0:
        obj._PROC["EMIT"]=Emitter(name,obj,emit_port,sync,frec)
        obj._PROC["EMIT"].add_topics(*obj._etc["_EMIT"])
        for ent,events in obj._etc["_EMIT_EVENTS"].items():
            for e in events:
                obj._PROC["EMIT"].add_event(ent,e)
        if sync:
            obj._PROC["EMIT"].start()

    #conectar subcriptores MQTT
    #preguntar por broker.
    name=obj._etc["name"]
    if len(obj._etc["_SUB"])+len(obj._etc["_SUB_EVENTS"])>0:
        mqtt=obj.dsc_get(obj._etc["robot"]+"/*/Broker")
        if mqtt!="0.0.0.0:0":
            obj._etc["MQTT_uri"]=mqtt
        uri=obj._etc["MQTT_uri"]
        if not mqtt_alive(uri):
            obj.L_error("Broker {} Not is on line ".format(uri))
        obj._PROC["SUB"]=subscriptions(name,uri,obj)
        topics={x:k.replace("LOCAL/",robot+"/")
                  for x,k in obj._etc["_SUB"].items()}
        obj._PROC["SUB"].subscribe_topics(**topics)
        events={x:k.replace("LOCAL/",robot+"/")
                  for x,k in obj._etc["_SUB_EVENTS"].items()}
        obj._PROC["SUB"].subscribe_events(**events)
        obj._PROC["SUB"].connect()

    #conectar receiver
    name=obj._etc["name"]
    if len(obj._etc["_RECEIVE"])+len(obj._etc["_RECEIVE_EVENTS"])>0:
        obj._PROC["RECEIVE"]=Receiver(name,emit_port,obj)
        topics={x:k.replace("LOCAL/",robot+"/")
                  for x,k in obj._etc["_RECEIVE"].items()}
        obj._PROC["RECEIVE"].subscribe_topics(**topics)
        events={x:k.replace("LOCAL/",robot+"/")
                  for x,k in obj._etc["_RECEIVE_EVENTS"].items()}
        obj._PROC["RECEIVE"].subscribe_events(**events)
        obj._PROC["RECEIVE"].connect()

    #lanzar proxys remotes y locales _REQ_INTERFACES HECHO
    req={x:k.replace("LOCAL/",robot+"/")
              for x,k in obj._etc["_REQ"].items()}
    name=obj._etc["name"]+".conectors"
    t = threading.Thread(target=_conectors,args=(obj,req,),name=name)
    t.setDaemon(True)
    t.start()

def _conectors(obj,reqs):
    #importante : dentro de los threads no podemos acceder a proxys externos
    # gevent no funciona bien en el intercambio con thread
    # solucion crear el proxy dentro.]
    items=list(reqs)
    while obj._PROC["requires"] not in ["OK","FAIL"]:
        retrys=RETRYS
        available_interfaces=obj.dsc_get(obj._etc["robot"]+"/*/Interfaces")
        while items!=[] and retrys>0:
            item=items.pop()
            #print("requiero",reqs[item])
            #print(available_interfaces)
            if reqs[item] in available_interfaces:
                uri=available_interfaces[reqs[item]]
                obj.L_info("{} connect to {}".format(item,uri))
                setattr(obj,item,uri)
            else:
                items.append(item)
                time.sleep(0.2)
            retrys=retrys-1
        if items==[]:
            obj._PROC["requires"]="OK"
        else:
            obj._PROC["requires"]="FAIL"
            obj.L_info("Error connecting {}".format(items))
    while obj._PROC["status"] not in ["OK","ERROR"]:
        time.sleep(0.2)
    if obj._PROC["requires"]=="OK":
        for w in obj._PROC["workers"]:
            w.start()
            obj.L_info("{} worker Started".format(w.name))
            
    else:
        obj.shutdown()

# Class control component
class Control(botlogging.Logging,discovery):
    """ This class provide threading funcionality to all object in node.
        Init workers Threads and PUB/SUB thread"""

    def __init__(self):
        botlogging.Logging.__init__(self)
        discovery.__init__(self)
        connect_component(self)

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


    def start_thread(self, fn, *args):
        """ Start all workers daemon"""
        if self.worker_run:
            name=self._etc["name"]+"."+fn.__name__
            t = threading.Thread(target=fn,name=name, args=args)
            t.setDaemon(True)
            self._PROC["workers"].append(t)
            self.L_info("{} worker Started".format(fn.__name__))
            t.start()
            
    def Get_INFO(self):
        data={"_etc":{},"_PROC":{}}
        data["_etc"]["name"]=self._etc["name"]
        data["_etc"]["ethernet"]=self._etc["ethernet"]
        data["_etc"]["host"]=self._etc["host"]
        data["_PROC"]["PID"]=self._PROC["PID"]
        data["_PROC"]["info"]=self._PROC["info"]
        data["_PROC"]["warnings"]=self._PROC["warnings"]
        if self._PROC["PUB"] is not None:
            data["_PROC"]["PUB"]=self._PROC["PUB"].get_topics()
            data["_PROC"]["PUB_EVENT"]=self._PROC["PUB"].get_events()
        else:
            data["_PROC"]["PUB"]=[]
            data["_PROC"]["PUB_EVENT"]=[]
        if self._PROC["EMIT"] is not None:    
            data["_PROC"]["EMIT"]=self._PROC["EMIT"].get_topics()
            data["_PROC"]["EMIT_EVENT"]=self._PROC["EMIT"].get_events()
        else:
            data["_PROC"]["EMIT"]=[]
            data["_PROC"]["EMIT_EVENT"]=[]
        if self._PROC["SUB"] is not None:    
            data["_PROC"]["SUB"]=self._PROC["SUB"].get_topics()
            data["_PROC"]["SUB_EVENT"]=self._PROC["SUB"].get_events()
        else:
            data["_PROC"]["SUB"]=[]
            data["_PROC"]["SUB_EVENT"]=[]   
        if self._PROC["RECEIVE"] is not None:     
            data["_PROC"]["RECEIVE"]=self._PROC["RECEIVE"].get_topics()
            data["_PROC"]["RECEIVE_EVENT"]=self._PROC["RECEIVE"].get_events()
        else:
            data["_PROC"]["RECEIVE"]=[]
            data["_PROC"]["RECEIVE_EVENT"]=[]
        data["_PROC"]["requires"]=self._PROC["requires"]
        data["_PROC"]["status"]=self._PROC["status"]
        return data

        
    def show_PROC(self,all=True):
        self.L_print("[FG] [OK][FY] Starded Component {}".format(self._etc["name"]))
        self.L_print("\t Network:{} Host: {} Pid:{}".
                format(self._etc["ethernet"],self._etc["host"],self._PROC["PID"]))
        if all:
            for t in self._PROC["info"]:
                self.L_print("\t {} {}".format(t[1],t[0]))
                for w in self._PROC["warnings"][t[0]]:
                    self.L_print("\t\t Warning: {} not implemented".format(w))
            if self._PROC["PUB"] is not None:
                t=self._PROC["PUB"].get_topics()
                if len(t)>0:
                    self.L_print("\t Publicating Topics: {}".format(t))
                t=self._PROC["PUB"].get_events()
                if len(t)>0:
                    self.L_print("\t Publicating Events channels: {}".format(t))
            if self._PROC["EMIT"] is not None:
                t=self._PROC["EMIT"].get_topics()
                if len(t)>0:
                    self.L_print("\t Emitting Topics: {}".format(t))
                t=self._PROC["EMIT"].get_events()
                if len(t)>0:
                    self.L_print("\t Emitting Events channels: {}".format(t))
            if self._PROC["SUB"] is not None:
                t=self._PROC["SUB"].get_topics()
                if len(t)>0:
                    self.L_print("\t subscriptions Topics: {}".format(t))
                t=self._PROC["SUB"].get_events()
                if len(t)>0:
                    self.L_print("\t subscribe Events channels: {}".format(t))
            if self._PROC["RECEIVE"] is not None:
                t=self._PROC["RECEIVE"].get_topics()
                if len(t)>0:
                    self.L_print("\t Receive Topics: {}".format(t))
                t=self._PROC["RECEIVE"].get_events()
                if len(t)>0:
                    self.L_print("\t Receive Events channels: {}".format(t))
            self.L_print("\t Requires: {}".format(self._PROC["requires"]))
            self.L_print("\t STATUS: {}".format(self._PROC["status"]))
        

    def New_handler(self,event,handler):
        method_list = [func for func in dir(self) if callable(getattr(self, func))]
        if handler.__name__ in method_list:
            if self._PROC["SUB"] is not None:
                self._PROC["SUB"].add_handler(event,handler)
            if self._PROC["RECEIVE"] is not None:
                self._PROC["RECEIVE"].add_handler(event,handler)
        else:
            self.L_print("[FR][ERROR][FY] handler {} not founded".format(handler.__name__))

    def get_PROC(self):
        return self._PROC

    def shutdown(self):
        self._PROC["SERVER"].stop()

    def Set_Logging(self,level=20):
        
        if level==0:
            level=self._etc["logging_level"]
        self.Level_reconfigure(level)
        self.L_info("Logging level change. new level:{}".format(level))
        

    def hello(self):
        return "hi"

    def get_name(self):
        return self._etc["name"]
