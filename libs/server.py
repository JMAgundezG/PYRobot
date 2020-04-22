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
            setattr(self, k, v)
        super(clss, self).__init__()
        original_init(self)
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
    try:
        class_comp=Loader_Config(cls,**config)
        obj=class_comp()
        utils.change_process_name(name)
        obj._PROC["PID"]=os.getpid()
        
        if obj.hello()=="hi":
            obj._PROC["status"]="INSTANCED"
        else:
            obj._PROC["status"]="ERROR"
            exit()
    except Exception as ex:
        P_Log("[FR][ERROR][FY] Instanced Component {}".format(name))
        P_Log(str(ex))
 
    # stablishing interface servers
    try:
        obj._PROC["status"]="INTERFACING"
        interfaces.append(Control_Interface)
        for inter in interfaces:
            interface=Interface(inter,obj)
            warnings[obj._etc["name"]+"/"+interface.__name__]=interface.Not_Implemented
            port=utils.get_free_port(port,host)
            info.append((obj._etc["name"]+"/"+interface.__name__,"{}:{}".format(host,port)))
            servers.append(StreamServer((host,port), interface()))
            port=port+1
        obj._PROC["info"]=info
        obj._PROC["warnings"]=warnings
        obj._PROC["SERVER"]=servers[-1]
    except Exception as ex:
        P_Log("[FR][ERROR][FY] Creating interface Component {}".format(name))
        P_Log(str(ex))
        exit()
    # Running __run__ method if exit
    method_list = [func for func in dir(obj) if callable(getattr(obj, func))]
    #print("\n")
    if "__Run__" in method_list:
        try:
            obj.__Run__()
            obj._PROC["status"]="OK"
        except Exception as ex:
            obj.L_Def("\t[FR][ERROR][FY] in __Run__{}".format(ex))
            raise
            exit()
    else:
        obj._PROC["status"]="OK"
    # wait requires for work and start server
    try:
        obj.show_PROC()
        while obj._PROC["requires"] not in ["OK","FAIL"]:
            time.sleep(0.2)
        if obj._PROC["requires"]=="OK":
            for s in servers[:-1]:
                s.start()
            obj._PROC["running"]="RUN"
            #print("started",obj._etc["name"])
            #print(obj.__dict__)
            servers[-1].serve_forever()
            P_Log("[FR][STOP][FY]  Signal Stop in Component {}".format(name))
        else:
            P_Log("[FR][ERROR][FY]  Requeriments incompleted {}".format(name))
    except:
        raise
        for s in servers:
            s.close()
        P_Log("[FR][STOP][FY]  Signal Stop in Component {}".format(name))
        
    finally:
        try:
            obj.__Close__()
        except:
            pass


def Run_Server(config):
    register= not config["_etc"]["sys"]
    process = Process(target=Start_Server,args=(config))
    process.daemon=True
    process.start()
    return process
