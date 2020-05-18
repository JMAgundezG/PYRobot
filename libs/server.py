#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________


from gevent.server import StreamServer
from PYRobot.libs.interface_control import Control_Interface
from PYRobot.libs.interfaces import Interface
from multiprocessing import Process
import PYRobot.utils.utils as utils
from PYRobot.botlogging.coloramadefs import P_Log
import os
import time
import sys
from PYRobot.libs.proxy import Proxy
from gevent import monkey
monkey.patch_all(thread=False)

def Loader_Config(clss, **kwargs):
    """ Decorator for load configuration into component
        init superclass control
    """
    original_init = clss.__init__

    def init(self):
        for k, v in kwargs.items():
            #print(k,"-->",v)
            setattr(self, k, v)
        super(clss, self).__init__()
        original_init(self) 
        #super(clss, self).__init__()
    clss.__init__ = init
    return clss

def Start_Server(config):
    servers=[]
    warnings={}
    info=[]
    status=False
    interfaces=config["_etc"]["_INTERFACES"]
    if type(interfaces) not in [tuple,list]:
        interfaces=[interfaces,]
    host=config["_etc"]["ip"]
    port=config["_etc"]["port"]
    name=config["_etc"]["name"]
    cls=config["_etc"]["cls"]
    STATUS=""
    try:
        class_comp=Loader_Config(cls,**config)
        obj=class_comp()
        utils.change_process_name(name)
        obj._PROC["PID"]=os.getpid()
        STATUS=obj._PROC["status"]
        del(config["_etc"]["cls"])
    except Exception as ex:
        P_Log("[FR][ERROR][FY] Instanced Component {}".format(name))
        P_Log(str(ex))
        STATUS="ERROR"
    if STATUS=="ERROR":
        exit()
        
    # stablishing interface servers
    try:
        interfaces.append(Control_Interface)
        for inter in interfaces:
            interface=Interface(inter,obj)
            warnings[obj._etc["name"]+"/"+interface.__name__]=interface.Not_Implemented
            assing_port=port[0][0]
            info.append((obj._etc["name"]+"/"+interface.__name__,"{}:{}".format(host,assing_port)))
            port[0][1].close()
            servers.append(StreamServer((host,assing_port), interface()))
            del(port[0])
        obj._PROC["info"]=info
        obj._PROC["warnings"]=warnings
        obj._PROC["SERVER"]=servers[-1]
        for s in servers:
            s.start()
        del(config["_etc"]["_INTERFACES"])
        del(config["_etc"]["port"])
        STATUS="INIT"
    except Exception as ex:
        P_Log("[FR][ERROR][FY] Creating interface Component {}".format(name))
        P_Log(str(ex))
        STATUS="ERROR"
        exit()

    # Running __run__ method if exit
    method_list = [func for func in dir(obj) if callable(getattr(obj, func))]
    try:
        obj.__post_init__()
        STATUS=obj._PROC["status"]        
    except Exception as ex:
        P_Log("[FR][ERROR][FY] in initiator {}".format(name))
        P_Log(str(ex))
        STATUS="ERROR"   
        
    
    if STATUS=="ERROR": 
        obj.show_PROC()
        for s in servers:
            s.close()   
        exit()
    if "__Run__" in method_list:
        try:
            obj.__Run__()
            obj._PROC["status"]="OK"
        except Exception as ex:
            obj.L_Def("\t[FR][ERROR][FY] in __Run__{}".format(ex))
            STATUS="ERROR"
            raise
    if STATUS=="ERROR":
        obj.show_PROC() 
        for s in servers:
            s.close()   
        exit()        
    obj.show_PROC()
    try:
        servers[-1].serve_forever()
        try:
            obj.__Close__()
        except:
            pass
        for s in servers:
            s.close()    
        #P_Log("[FR][STOP][FY]  Signal Stop in Component {}".format(name))
    except:
        P_Log("[FR][STOP][FY]  Signal Stop in Component {}".format(name))       
        raise


