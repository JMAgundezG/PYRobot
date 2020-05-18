#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________


from PYRobot.utils import utils
from pprint import pprint

import time
import sys
import os.path
import json
import re
from PYRobot.config import myjson
from PYRobot.botlogging.coloramadefs import P_Log,C_Err
from PYRobot.config.loader_PYRobot import Loader_PYRobot
from PYRobot.utils.utils_discovery import Discovery
from PYRobot.utils.utils import show_PROC
from PYRobot.libs.proxy import Proxy
from PYRobot.utils.utils import get_PYRobots_dir,get_host_name


robots_dir=get_PYRobots_dir()
hostname=get_host_name()

Init_Skel={"NAME":"","MODEL":"","localhost":[]}    


def get_node_interfaces(host):
    dst=Discovery()
    interfaces={}
    dst=Discovery()
    key="PYRobot/Node_"+host+"/InterfacesOK"
    response=dst.Get(key)
    interfaces.update({k.split("/")[1].split("_")[1]:v for k,v in response.items() if k.find("/Node_Interface")!=-1})
    return interfaces
               
     
def Stop_robot(search):
    dsc=Discovery()
    controls={}
    for s in search:
        controls.update(dsc.Get(s+"/Control"))
    for uri in controls.values():
        if uri!="0.0.0.0:0":
            proxy=Proxy(uri)
            if proxy():
                name=proxy.shutdown()
                P_Log("[FR][STOP][FY] Signal Stop in Component [FW]{}".format(name))
                
    if len(controls)==0:
        P_Log("[FY] Nothing to Stop")

def Kill_robot(search):
    pids={}
    for s in search:
        robot,comp=s.split("/")
        comp_pids=utils.findProcessIdByName(robot+"/")
        pids.update(comp_pids)
    kill={}
    for s in search:
        s=s.replace("*",".+")
        s=s.replace("?",".+")
        finded={k:v for k,v in pids.items() if re.search(s,v)}
        
        kill.update(finded)
    kill={k:v for k,v in kill.items() if v.find("python3 ")==-1}
    for p,n in kill.items():
        try:
            utils.kill_process(p)
            P_Log("[FY]killing [FW]{} PID:{}".format(n,p))
        except:
            pass
    if len(kill)==0:
        P_Log("[FY] Nothing to Kill")

def Status_robot(search):
    dsc=Discovery()
    controls={}
    for s in search:
        controls.update(dsc.Get(s+"/Control"))
    for uri in controls.values():
        if uri!="0.0.0.0:0":
            proxy=Proxy(uri)
            if proxy():
                info_comp=proxy.Get_INFO()
                show_PROC(info_comp)
    if len(controls)==0:
        P_Log("[FY] Nothing to show")
        
def Find_robot(search,show=True):
    dsc=Discovery()
    names=[]
    if type(search)==str:
        search=[search] 
    for s in search:
        name=dsc.Get(s+"/Name")
        names.extend(name)
    if len(names)==0:
        if show:
            P_Log("[FY] Nothing to show")
        return []
    if show:
        P_Log("[FY] Find Components:")
        for n in names:
            P_Log("\tComponent: [FG]{}".format(n))
    return names
        
    
def Start_robot(Filename=None,Init={},Model={}):
    loader=Loader_PYRobot(Filename,Init,Model)
    robot_name=Init["NAME"]
    onlinecomps=Find_robot("{}/*".format(robot_name),show=False)
    loader.Check()
    components=loader.Get_Skel()
    dsc=Discovery()
  
    for c,comp in components.items():
        name=comp["_etc"]["name"]
        host=comp["_etc"]["host"]
        if name not in onlinecomps:
            comp=json.dumps(comp)
            if host=="localhost":
                utils.run_component("_comp",comp,run="start")
            else:
                uris=get_node_interfaces(host)
                if host in uris:
                    proxy=Proxy(uris[host])
                    if proxy():
                        proxy.Run_comp(comp)
                P_Log("[FY]component:[FW]{} [FY]starting in host:[FW]{}".format(name,host))
        else:
            P_Log("[FY]component:[FW]{} [FY] is online on [FW]{}".format(name,host))

    trys=6
    while trys>0:
        controls=dsc.Get(robot_name+"/*/ControlOK")
        if len(controls)==len(components):
            trys=0
        else:
            trys=trys-1
            time.sleep(0.09)
    if len(controls)!=len(components):
        P_Log("[FY][Warning][FW] some components are not running") 
    P_Log("[FY] Waiting for connect loggins...")
    controls=dsc.Get(robot_name+"/*/ControlOK")
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
    
def get_comp(cad):
    if len(cad.split("/"))==1:
        components=[cad+"/*"]
        return components
    if len(cad.split("/"))==2:
        robot,comp=cad.split("/")
        components=[robot+"/"+c for c in comp.split(",")]
        return components
        
    else:
        return []
        
COMMAND={"start":Start_robot,"stop":Stop_robot,"kill":Kill_robot,"status":Status_robot,"find":Find_robot}    

if __name__ == '__main__':       
   pass
   
