#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________


from PYRobot.utils import utils
from pprint import pprint

import time
import sys
import os.path
import json
from PYRobot.config import myjson
from PYRobot.botlogging.coloramadefs import P_Log,C_Err
from PYRobot.config.loader_PYRobot import Loader_PYRobot
from PYRobot.utils.utils_discovery import Discovery
from PYRobot.libs.proxy import Proxy
from PYRobot.utils.utils import get_PYRobots_dir,get_host_name


robots_dir=get_PYRobots_dir()
hostname=get_host_name()

Init_Skel={"NAME":"","MODEL":"","localhost":[]}               

def show_PROC(data,all=True):
    
        P_Log("[FY]COMPONENT:[FW]{} [FY]STATUS:[FG]{}".format(data["_etc"]["name"],data["_PROC"]["status"]))
        P_Log("\t Network:{} Host: {} Pid:{}".
                format(data["_etc"]["ethernet"],data["_etc"]["host"],data["_PROC"]["PID"]))
        if all:
            P_Log("\t[FY] INTERFACES:")
            for t in data["_PROC"]["info"]:
                P_Log("\t\t {} {}".format(t[1],t[0]))
                for w in data["_PROC"]["warnings"][t[0]]:
                    P_Log("\t\t\t Warning: {} not implemented".format(w))
            if len(data["_PROC"]["PUB"])>0:
                P_Log("\t Publicating Topics: {}".format(",".join(data["_PROC"]["PUB"])))
            if len(data["_PROC"]["PUB_EVENT"])>0:
                P_Log("\t Publicating Events channels: {}".format(",".join(data["_PROC"]["PUB_EVENT"])))
            if len(data["_PROC"]["EMIT"])>0:
                P_Log("\t Emitting Topics: {}".format(",".join(data["_PROC"]["EMIT"])))
            if len(data["_PROC"]["EMIT_EVENT"])>0:
                P_Log("\t Emitting Events channels: {}".format(",".join(data["_PROC"]["EMIT_EVENT"])))
            if len(data["_PROC"]["SUB"])>0:
                P_Log("\t subscriptions Topics: {}".format(",".join(data["_PROC"]["SUB"])))
            if len(data["_PROC"]["SUB_EVENT"])>0:
                P_Log("\t subscribe Events channels: {}".format(",".join(data["_PROC"]["SUB_EVENT"])))
            if len(data["_PROC"]["RECEIVE"])>0:
                P_Log("\t Receive Topics: {}".format(",".join(data["_PROC"]["RECEIVE"])))
            if len(data["_PROC"]["RECEIVE_EVENT"])>0:
                P_Log("\t Receive Events channels: {}".format(",".join(data["_PROC"]["RECEIVE_EVENT"])))
            P_Log("\t Requires: {}".format(data["_PROC"]["requires"]))
            P_Log("")
     

def Stop_robot(Filename=None,Init={},Model={}):
    dsc=Discovery()
    robot_name=Init["NAME"]
    components=[]
    for k,v in Init.items():
        if k not in ["MODEL","NAME"]:
            components.extend([robot_name+"/"+x for x in v])
    controls={}
    for c in components:
        controls.update(dsc.Get(c+"/Control"))
    for uri in controls.values():
        if uri!="0.0.0.0:0":
            proxy=Proxy(uri)
            if proxy():
                proxy.shutdown()

def Kill_robot(Filename=None,Init={},Model={}):
    robot_name=Init["NAME"]
    pids={}
    if hostname in Init:
        for comp in Init[hostname]:
            comp_pids=utils.findProcessIdByName(robot_name+"/"+comp)
            pids.update(comp_pids)
    if "localhost" in Init:
        for comp in Init["localhost"]:
            comp_pids=utils.findProcessIdByName(robot_name+"/"+comp)
            pids.update(comp_pids)
    #print(pids)
    for p,n in pids.items():
        try:
            utils.kill_process(p)
            P_Log("[FY]killing [FW]{} PID:{}".format(n,p))
        except:
            pass

def Status_robot(Filename=None,Init={},Model={}):
    dsc=Discovery()
    robot_name=Init["NAME"]
    components=[]
    for k,v in Init.items():
        if k not in ["MODEL","NAME"]:
            components.extend([robot_name+"/"+x for x in v])
    controls={}
    for c in components:
        controls.update(dsc.Get(c+"/Control"))
    for uri in controls.values():
        if uri!="0.0.0.0:0":
            proxy=Proxy(uri)
            if proxy():
                info_comp=proxy.Get_INFO()
                show_PROC(info_comp)

def Start_robot(Filename=None,Init={},Model={}):
    loader=Loader_PYRobot(Filename,Init,Model)
    robot_name=Init["NAME"]
    loader.Check()
    components=loader.Get_Skel()
    dsc=Discovery()
    for c,comp in components.items():
        name=comp["_etc"]["name"]
        comp=json.dumps(comp)
        utils.run_component("_comp",comp,run="start")
        i=10
        get=""
        while i>0 and get!=name:
            get=dsc.Get(name+"/Running")
            get=get[0] if len(get)>0 else ""
            i=i-1
            time.sleep(0.1)

    controls=dsc.Get(robot_name+"/*/Control")
    #print(controls)
    for uri in controls.values():
        if uri!="0.0.0.0:0":
                proxy=Proxy(uri)
                if proxy():
                    proxy.Set_Logging(0)
                    


def get_robot_init(robot):
    if robot.find(".json")>0:
        if robot.find("/")==-1:
            robot=robots_dir+robot
        loader=myjson.MyJson(robot)
        init=loader.get()
        if "NAME" not in init:
            file=os.path.basename(robot)
            init["NAME"]=file.replace(".json","")
        return init
    else:
        init=Init_Skel
        C_Err(robot.find("@")==-1,"<robot name>@<host>/<model>/<components,>")
        init["NAME"],rest=robot.split("@")
        C_Err(robot.find("/")==-1,"<robot name>@<host>/<model>/<components,>")
        C_Err(len(robot.split("/"))<2,"<robot name>@<host>/<model>/<components,>")
        if len(rest.split("/"))==2:
            init["MODEL"],comp=rest.split("/")
            init["localhost"].extend(comp.split(","))
        else:
            host,init["MODEL"],comp=rest.split("/")
            del(init["localhost"])
            init[host]=[]
            init[host].extend(comp.split(","))
            
        return init
        
COMMAND={"start":Start_robot,"stop":Stop_robot,"kill":Kill_robot,"status":Status_robot}    

if __name__ == '__main__':       
   pass
   
