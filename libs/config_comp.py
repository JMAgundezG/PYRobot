#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ____________developed by paco andres____________________

import os.path
from PYRobot.libs import utils, myjson
from PYRobot.libs.botlogging.coloramadefs import P_Log
from PYRobot.libs.comp_skel import Component_Skel,_OPTIONS, General_Skel
from PYRobot.libs.utils import get_PYRobots_dir
#import PYRobot.libs.parser as parser

import importlib
import pprint
import copy
import inspect

PYROBOTS=get_PYRobots_dir()
robots_dir=get_PYRobots_dir()
dir_comp="components/"


def init_ethernet():
    eths=utils.get_all_ip_eths()
    P_Log("[FY]Availables Interfaces:")
    ethernet=""
    for ips,interface in eths:
        P_Log("\t {}: {}".format(interface,ips))
        if interface==id:
            ethernet=id
            ip = ips
    if len(eths)==0:
        P_Log("[FR][ERROR][FW] No interface finded")
        exit()
    return eths

def get_ethernets():
    eths=utils.get_all_ip_eths()
    sal={e:ip for ip,e in eths}
    sal["LOCAL"]="127.0.0.1"
    return sal


def get_conf(file):
    comp_config=myjson.MyJson(file)
    return comp_config.get()

def get_comp_cls(COMP):
    if len(COMP.split("::"))==2:
        comp=COMP.split("::")[0]
        cls =COMP.split("::")[1]
        return comp,cls
    else:
        return "",""

def load_module_options(module):
    config={"_EVENTS_":{}}
    module=importlib.import_module(module)
    classes={name:obj for name,obj in inspect.getmembers(module,inspect.isclass) if name!="Service"}
    attributes=[x for x in module.__dict__ if not x.find("__")==0 and x not in classes and x!="Service"]
    config["_INTERFACES_AVAILABLE"]=classes
    opt_loaded={k:getattr(module,k) for k in attributes}
    for k,v in opt_loaded.items():
        if k.find("_EVENTS_")==0:
            config["_EVENTS_"][k.split("_EVENTS_")[1]]=v
        else:
            config[k]=v
    return config

def load_public_interfaces():
    interfaces={}
    dir_interfaces=dir_comp+"interfaces"
    module_interfaces=dir_interfaces.replace("/",".")
    Files_available=[x.split(".py")[0] for x in os.listdir(robots_dir+dir_interfaces)]
    for f in Files_available:
        module=importlib.import_module(module_interfaces+"."+f)
        classes={name:obj for name,obj in inspect.getmembers(module,inspect.isclass) if name!="Service"}
        interfaces.update(classes)
    return interfaces

def update_skel_ethernet(skel):
    if skel["_etc"]["mode"]=="local":
        skel["_etc"]["ip"]="127.0.0.1"
        skel["_etc"]["ethernet"] ="lo"
    if skel["_etc"]["mode"]=="public":
        myeth=skel["_etc"]["ethernet"]
        eth=skel["_etc"]["eths"][0][1]
        ip=skel["_etc"]["eths"][0][0]
        for ip_eth in skel["_etc"]["eths"]:
            if myeth==ip_eth[1]:
                ip=ip_eth[0]
        skel["_etc"]["ethernet"]=eth
        skel["_etc"]["ip"]=ip
    return skel

def Create_General(config):
    general=copy.deepcopy(General_Skel)
    for k,v in config["_etc"].items():
        if k in general:
            general[k]=v
    return general


def update_skel_dict(skel, mydict):
    sal=copy.deepcopy(skel)
    for k,v in mydict.items():
        if k in sal["_etc"]:
            sal["_etc"][k]=v
        else:
            sal[k]=v
    return sal

def update_skel_json(skel, filename):
    if filename!="":
        json=myjson.MyJson(filename)
    sal=copy.deepcopy(skel)
    for k,v in json.get().items():
        if k in sal["_etc"]:
            sal["_etc"][k]=v
        else:
            sal[k]=v
    sal=update_skel_ethernet(sal)
    return sal

def get_basic_etc(filename):
    sal=copy.deepcopy(Component_Skel)
    if filename !="":
        json=myjson.MyJson(filename)
    for k,v in json.get().items():
        if k in sal["_etc"]:
            sal["_etc"][k]=v
        else:
            sal[k]=v
    sal=update_skel_ethernet(sal)
    return sal



def check_comp_files(dir_comp,cls):
    files=["conf_"+cls,"__init__"]
    Files_available=[x.split(".py")[0] for x in os.listdir(robots_dir+dir_comp)]
    for f in files:
        if f not in Files_available:
            P_Log("[FR]ERROR:[FY] File {} not found in {}".format(f,dir_comp))
            exit()
    P_Log("[FY] Files on  {} [[FG]OK[FY]]".format(dir_comp))



def get_comp_conf_(instance,cls):
    base_module=instance["dir_comp"].replace("/",".")
    try:
        local=load_module_options(base_module+"conf_"+cls)
        public_interfaces=load_public_interfaces()
        for k,v in local["_INTERFACES_AVAILABLE"].items():
            public_interfaces[k]=v
        local["_INTERFACES_AVAILABLE"]=public_interfaces
    except:
        raise
        P_Log("[FR]ERROR:[FW] Component:{} in file conf_ ".format(component))
        exit()
    #check interfaces
    if "_INTERFACES" in instance:
        try:
            interfaces=[]
            for x in instance["_INTERFACES"]:
                interfaces.append(local["_INTERFACES_AVAILABLE"][x])
            P_Log(" [FY]Interfaces:{} [FG][OK]".format(",".join(instance["_INTERFACES"])))
            instance["_INTERFACES"]=[]
            for interface in interfaces:
                instance["_INTERFACES"].append(interface.__module__+"::"+interface.__name__)
            print(instance["_INTERFACES"])
        except:
            P_Log("[FR][ERROR][FY] interface {} not supported".format(x))
            raise
            exit()
    #check publications
    pub=instance.get("_PUB",[])
    not_find=[x for x in pub if x not in local]
    if len(not_find)!=0:
        P_Log("[FR][ERROR][FY] Pub. Topics:{} not defined in conf_".format(",".join(not_find)))
        exit()
    instance["_PUB"]=pub
#    for x in pub:
#        local.pop(x)
    if len(pub)>0:
        P_Log(" [FY]Pub. Topics:{} [FG][OK]".format(",".join(pub)))

    #check broadcast publications
    pub=instance.get("_EMIT",[])
    not_find=[x for x in pub if x not in local]
    if len(not_find)!=0:
        P_Log("[FR][ERROR][FY] Emit. Topics:{} not defined in conf_".format(",".join(not_find)))
        exit()
    instance["_EMIT"]=pub
#    for x in pub:
#        local.pop(x)
    if len(pub)>0:
        P_Log(" [FY]Emit Topics:{} [FG][OK]".format(",".join(pub)))

    #check events
    if "_PUB_EVENTS" in instance:
        try:
            events={}
            for x in instance["_PUB_EVENTS"]:
                events[x]=local["_EVENTS_"][x]
                del(local["_EVENTS_"][x])
            P_Log(" [FY]Pub. Events:{} [FG][OK]".format(",".join(instance["_PUB_EVENTS"])))
            instance["_PUB_EVENTS"]=events
        except:
            raise
            P_Log("[FR][ERROR][FY]Pub. event {} not finded".format(x))
            exit()

    #check broadcast events
    if "_EMIT_EVENTS" in instance:
        try:
            events={}
            for x in instance["_EMIT_EVENTS"]:
                events[x]=local["_EVENTS_"][x]
                del(local["_EVENTS_"][x])
            P_Log(" [FY]Emit Events:{} [FG][OK]".format(",".join(instance["_EMIT_EVENTS"])))
            instance["_EMIT_EVENTS"]=events
        except:
            P_Log("[FR][ERROR][FY]Emit. event {} not finded".format(x))
            exit()

    #check subscriptions
    sub=instance.get("_SUB",[])
    not_find=[x for x in sub if x not in local]
    if len(not_find)!=0:
        P_Log("[FR][ERROR][FY] sub. Topics:{} not defined in conf_".format(",".join(not_find)))
        exit()
    instance["_SUB"]=sub
    if len(sub)>0:
        P_Log(" [FY]Subs. Topics:{} [FG][OK]".format(",".join(sub)))

    #check broadcast subscriptions
    sub=instance.get("_RECEIVE",[])
    not_find=[x for x in sub if x not in local]
    #print(local)
    #print(sub)
    if len(not_find)!=0:
        P_Log("[FR][ERROR][FY] Receive Topics:{} not defined in conf_".format(",".join(not_find)))
        exit()
    instance["_RECEIVE"]=sub
    if len(sub)>0:
        P_Log(" [FY]Receive Topics:{} [FG][OK]".format(",".join(sub)))

    #check event subscriptions
    sub=instance.get("_SUB_EVENTS",{})
    not_find=[x for x in sub if x not in local]
    if len(not_find)!=0:
        P_Log("[FR][ERROR][FY] sub. Event:{} not defined in conf_".format(",".join(not_find)))
        exit()
    instance["_SUB_EVENTS"]=sub
    if len(sub)>0:
        P_Log(" [FY]Subs. Events:{} [FG][OK]".format(",".join(sub)))

    #check event broadcast subscriptions
    sub=instance.get("_RECEIVE_EVENTS",{})
    not_find=[x for x in sub if x not in local]
    if len(not_find)!=0:
        P_Log("[FR][ERROR][FY] Receive Event:{} not defined in conf_".format(",".join(not_find)))
        exit()
    instance["_RECEIVE_EVENTS"]=sub
    if len(sub)>0:
        P_Log(" [FY]Receive Events:{} [FG][OK]".format(",".join(sub)))

    #check _REQUIRES_
    req=[x for x in instance.get("_REQ",[])]
    requires=[x for x in local.get("_REQUIRES_",[])]
    if req!=requires:
        P_Log("[FR][ERROR][FY] Requires {}".format(",".join(requires)))
        exit()
    if len(req)>0:
        P_Log(" [FY]Requires:{} [FG][OK]".format(",".join(list(req))))
    if "_REQUIRES_" in local:
        del(local["_REQUIRES_"])
    del(local["_INTERFACES_AVAILABLE"])
    del(local["_EVENTS_"])
    for k,v in local.items():
        if k not in instance:
            instance[k]=v
    return instance

def get_module_class(dir,cls):
    """
    Return a list of (classes,modules) for a given dir component
    Warning: if module has non installed packages return a empty list
    """
    list_class = []
    error_class = []
    base_dir=robots_dir+dir
    base_comp=dir.replace("/",".")
    Files_available=[x.split(".py")[0] for x in os.listdir(base_dir) if x.find(".py")>-1]
    for m in Files_available:
        try:
            mod = importlib.import_module(base_comp+m)
            for name,obj in inspect.getmembers(mod, inspect.isclass):
                if cls==name:
                    #print("cls",name,obj,mod)
                    return mod, base_comp+m,error_class

        except Exception as e:
            error_class.append((e,base_comp+m))
    return m,base_comp+m, error_class


def get_cls_comp(dir_comp,cls):

    base_module=dir_comp.replace("/",".")
    try:
        module, module_name,errors =get_module_class(dir_comp,cls)
        #print(module_name,cls)
        #print(module,cls)
        #print(errors)
        if module=="":
            P_Log("[FR]ERROR:[FW] class {} not found in component".format(cls))
            for e,error in errors:
                P_Log("\t[FR]{}[FW] on {}".format(e,error))
            exit()
    except:
        raise
        exit()
    try:
        #module=importlib.import_module(module)
        comp_cls=getattr(module,cls)
        P_Log("[FY] Module:{},  Class:{} [FG][OK][FW]".format(module.__name__,cls))
        return comp_cls
    except Exception as ex:
        P_Log("[FR]ERROR:[FW] Module {} --> {}".format(base_module,str(ex)))
        #raise
        exit()

def Create_skel(model,name,general,instance):
    instance["model"]=model
    #instance["name"]=robot+"/"+name
    #instance["robot"]=robot
    instance["component"],instance["cls"] = get_comp_cls(instance["_COMP"])
    instance["dir_comp"]=dir_comp+instance["component"]+"/"
    del(instance["_COMP"])
    cls=instance["cls"]
    check_comp_files(instance["dir_comp"],cls)
    obj_cls=get_cls_comp(instance["dir_comp"],cls)
    instance["cls"]=obj_cls.__module__+"::"+obj_cls.__name__
    skel=copy.deepcopy(Component_Skel)
    instance=get_comp_conf_(instance,cls)

    skel=update_skel_dict(skel,general)
    skel=update_skel_dict(skel,instance)
    #skel=update_skel_ethernet(skel)
    if skel["_etc"]["name"]=="Noname":
        skel["_etc"]["robot"]=skel["_etc"]["host"]
    else:
        skel["_etc"]["robot"]=skel["_etc"]["name"]
    skel["_etc"]["name"]=skel["_etc"]["robot"]+"/"+name
    return skel
