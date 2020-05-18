#!/usr/bin/env python3
# ____________developed by paco andres_10/04/2019___________________
import sys
import os
import time
from PYRobot.config import myjson
from PYRobot.utils.utils import get_PYRobots_dir,get_host_name,get_ethernets,mqtt_alive
import PYRobot.config.basic_skel as skel
from PYRobot.botlogging.coloramadefs import P_Log,C_Err
from PYRobot.config.sintactic_skel import Sintactic,GET_COMP
from PYRobot.config.semantic_skel import Semantic
from PYRobot.config.cmake_skel import CMake,all_interfaces
from PYRobot.utils.utils_discovery import Discovery
from PYRobot.libs.proxy import Proxy
import copy
from pprint import pprint



Init_Skel={"NAME":"PYRobot","MODEL":"PYRobot","localhost":["component"]}
Model_Skel={"GENERAL":{"ethernet":"enp0s25",
                       "sys":False,
                       "port":7060,
                       "broadcast_port":9999,
                       "MQTT_port":1883,
                       "EMIT_port":10000,
                       "mode":"public",
                       "KEY":"user:pass",
                       "frec":0.01
                       },
            "component":{"_COMP":"",
                            "_PUB":""
                        }
            }

robots_dir=get_PYRobots_dir()
sys.path.append(robots_dir)
dir_comp="components/"
dir_models=robots_dir+"models/"
hostname=get_host_name()

def get_all_nodes_interfaces():
    dst=Discovery()
    interfaces={"localhost":hostname}
    dst=Discovery()
    key="PYRobot/Node_*"+"/InterfacesOK"
    response=dst.Get(key)
    interfaces.update({k.split("/")[1].split("_")[1]:v for k,v in response.items() if k.find("/Node_Interface")!=-1})
    return interfaces

def get_all_hosts(eth=None):
    dst=Discovery()
    key="iamrobot/*/HI"
    response=dst.Get(key)
    host_name=get_host_name()
    if host_name not in response:
        eths=get_ethernets()
        if eth in eths:
            ips=[eths[eth]]
        else:
            ips=[ip for dis,ip in eths.items()]
        response[host_name]=ips
    response["localhost"]=response[host_name]
    return response

def get_MQTT_uri(host,port,eth):
    hosts=get_all_hosts(eth)
    uri="0.0.0.0:{}".format(port)
    if host in hosts:
        uri="{}:{}".format(hosts[host][0],port)
        if not mqtt_alive(uri):
            return "0.0.0.0:{}".format(port)
    return uri

class Loader_PYRobot(object):
    def __init__(self,init_file=None,Init={},Model={}):
        #chequeamos si hay file o dict y los cargamos
        if init_file is None:
            self.inits=Init
            C_Err(self.inits=={},"Init error dict")
            C_Err("MODEL" not in self.inits,"MODEL robot not found in init")
            C_Err("NAME" not in self.inits,"Name robot not found in init")
            self.model=self.inits["MODEL"]
            self.init_file="Init.json"
            
        else:
            self.Name_robot=init_file
            self.init_file=robots_dir+init_file+".json"
            loader=myjson.MyJson(self.init_file)
            self.inits=loader.get()
            C_Err(self.inits=={},"file error {}".format(self.init_file))
            C_Err("MODEL" not in self.inits,"MODEL robot not found in init")
            self.inits.setdefault("NAME",init_file)
            model=self.inits["MODEL"]
        if Model=={}:
            self.instance_file=dir_models+self.model+".json"
            loader_instances=myjson.MyJson(self.instance_file)  
            self.instances=loader_instances.get()  
        else:
            self.instances=Model
        self.COMPONENTS={}
    
    def Get_Skel(self):
        return self.COMPONENTS

    def Check(self):
        model=self.inits["MODEL"]
        del(self.inits["MODEL"])
        self.name_robot=self.inits["NAME"]
        del(self.inits["NAME"])
        instances=self.instances 
        #organizamos init
        self.inits.setdefault(hostname, [])
        self.inits.setdefault("localhost", [])
        self.inits["localhost"].extend(self.inits[hostname])
        del(self.inits[hostname])
        self.COMPONENTS={}
        comps=[c for host,comps in self.inits.items() for c in comps]

        #cargamos la configuracion general
        #actualizamos host y model
        general={}
        if "GENERAL" in instances:
            general=instances["GENERAL"]
        del(instances["GENERAL"])
        general["robot"]=self.name_robot
        general["model"]=model
        
        P_Log("[FG]Loading Robot:[FW]{}[FG] Model:[FW]{}".format(self.name_robot,model))
        
        #chequeamos componentes duplicados y no encontrados
        C_Err(len(comps)!=len(set(comps)),"There are components duplicates in {}".format(self.init_file))
        not_found=[x for x in comps if x not in instances]
        C_Err(len(not_found)!=0,"There are components not found in model {}".format(model))
        
        # preparamos Instances y la estructura final de componentes
        self.Instances={}
        errors=[]
        P_Log("[FY]Checking COMP_ ",ln=False)
        for host,comps in self.inits.items():
            for comp in comps:
                self.COMPONENTS[comp]=copy.deepcopy(skel.Component_Skel)
                self.Instances[comp]=copy.deepcopy(general)
                self.Instances[comp].update(instances[comp])
                self.Instances[comp]["host"]=host
                self.Instances[comp]["name"]=self.Instances[comp]["robot"]+"/"+comp
                if "_COMP" in self.Instances[comp]:
                    check_comp=GET_COMP(self.Instances[comp]["_COMP"])
                    val,err=check_comp.split("--")
                    self.Instances[comp]["_COMP"]=val
                    if err=="ERROR":
                        errors.append(" {} in _COMP {}".format(comp,val))
                else:
                    errors.append(" {} no label _COMP".format(comp))
                self.COMPONENTS[comp]["_etc"]["_COMP"]=val
                self.COMPONENTS[comp]["_etc"]["name"]=self.Instances[comp]["name"]
                self.COMPONENTS[comp]["_etc"]["host"]=host
        if len(errors)!=0:
            P_Log(" [FR][FAIL]")
            for e in errors:
                P_Log("[FR][ERROR][FW] {}".format(e))
            C_Err(len(errors)>0," in COMP_")       
        else:
            P_Log(" [FG][OK]")
        
        #chequeamos el broker mqtt
        P_Log("[FY]Checking Broker ",ln=False)
        errors=[]
        for name,comp in self.Instances.items():
            mqtt_uri=comp.get("MQTT_uri","localhost")
            port=comp.get("MQTT_port",1883)
            eth=comp.get("ethernet","eth")
            eths=get_ethernets()
            if eth in eths:
                eth=eths[eth]
            self.Instances[name]["ethernet"]=eth    
            self.Instances[name]["MQTT_uri"]=get_MQTT_uri(mqtt_uri,port,eth)
            if self.Instances[name]["MQTT_uri"]=="0.0.0.0:{}".format(port):
                errors.append(errors.append(" {} no MQTT_uri on line".format(name)))
        if len(errors)!=0:
            P_Log(" [FY][Warning]")
            for e in errors:
                P_Log("\t[FY][Warning][FW] {}".format(e))      
        else:
            P_Log(" [FG][OK]")
         
 
        # preparamos la estructura final de componentes
        # revisamos si estan los host preparados
        available_host=get_all_hosts()
        P_Log("[FY]Checking Distributed Hosts ",ln=False)
        errors=[k for k in self.inits if k not in available_host]
        if len(errors)!=0:
            P_Log(" [FY][Warning]")
            for e in errors:
                P_Log("\t[FY][Warning][FW] host {} not is online".format(e))  
        else:
            P_Log(" [FG][OK]")
        self.Instances={name:comp for name,comp in self.Instances.items() if self.Instances[name]["host"] in ["localhost",get_host_name()]}

        #pedimos configuracion local de los componentes locales
        errors=[]
        all_i=all_interfaces()
        P_Log("[FY]Checking Components code",ln=False)
        for comp,config in self.Instances.items():
            c,cls=config["_COMP"].split("::")  
            g=CMake(c)
            status=g.get_status(cls)
            errors.extend([" in _COMP {} {}".format(c,x) for x in g.get_errors(cls)])
            errors.extend([" need package _COMP {} {}".format(c,x) for x in status["need_packages"]])
            errors.extend([" Run error _COMP {} {}".format(c,x) for x in status["run_errors"]])
            if len(errors)==0:
                self.Instances[comp].update(status["config"])
            if "_INTERFACES" in config:
                errs=all_i.get_error_interfaces(config["_INTERFACES"])
                errors.extend([" _Interfaces _COMP {} {}".format(c,x) for x in errs])
                if len(errs)==0:
                    self.Instances[comp]["_CLS_INTERFACES"]=all_i.get_interfaces(config["_INTERFACES"])
        
        if len(errors)!=0:
            P_Log(" [FR][FAIL]")
            for e in errors:
                P_Log("[FR][ERROR][FW] {}".format(e))
            C_Err(len(errors)>0," in components code")
        else:
            P_Log(" [FG][OK]") 
            
        #actualizamos COMPONENTS con la configuracion de instances
        for name,comp in self.Instances.items():
            if name in self.COMPONENTS:
                self.COMPONENTS[name]=skel.update_skel_dict(self.COMPONENTS[name],self.Instances[name])
        self.COMPONENTS={k:v for k,v in self.COMPONENTS.items() if k in self.Instances}
        
        # hacemos chequeo sintactico de las instancias  
        errors={}        
        P_Log("[FY]Checking Sintactic Model",ln=False)   
        for name,comp in self.COMPONENTS.items():
            check=Sintactic(comp)
            err=check.get_errors()
            if len(err)>0:
                errors[name]=check.get_errors()
            self.COMPONENTS[name]=check.get_skel()      
        if len(errors)==0:
            P_Log(" [FG][OK]")
        else:
            P_Log(" [FR][FAIL]")  
        show_errors={"Component: "+k+" Token: "+kk:vv for k,v in errors.items() for kk,vv in v.items()}
        
        for k,e in show_errors.items():
            P_Log("[FR][ERROR][FW] {} --> {}".format(k,e))
        C_Err(len(show_errors)>0,"Sintactics errors in model")
        

        #hacemos el chequeo semantico de las instancias.
        errors={}        
        P_Log("[FY]Checking Semantic Model",ln=False)   
        check=Semantic(self.COMPONENTS)
        errors=check.get_errors()
        self.COMPONENTS=check.get_skel() 
        if len(errors)==0:
            P_Log(" [FG][OK]")
        else:
            P_Log(" [FR][FAIL]")       
        for e in errors:
            P_Log("[FR][ERROR][FW] {}".format(e))
        C_Err(len(errors)>0,"Semantic in model")
        
        if len(check.get_warnings())>0:
            for e in check.get_warnings():
                P_Log("\t[FY][WARNING][FW] {}".format(e))

        #limpiamos COMPONENTS
        #pprint(self.COMPONENTS)
   
if __name__ == '__main__':
    pass

        
        
        
     
        