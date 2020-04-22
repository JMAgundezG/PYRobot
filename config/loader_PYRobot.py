#!/usr/bin/env python3
# ____________developed by paco andres_10/04/2019___________________
import sys
import os
import time
from PYRobot.config import myjson
from PYRobot.utils.utils import get_PYRobots_dir,get_host_name
import PYRobot.config.basic_skel as skel
from PYRobot.botlogging.coloramadefs import P_Log,C_Err
from PYRobot.config.sintactic_skel import Sintactic,GET_COMP
from PYRobot.config.semantic_skel import Semantic
from PYRobot.config.cmake_skel import CMake,all_interfaces
import copy



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

def get_uri_node(host):
    if host=="localhost":
        return host
    else:
        return "0.0.0.0:0"

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
        if len(errors)!=0:
            P_Log(" [FR][FAIL]")
            for e in errors:
                P_Log("[FR][ERROR][FW] {}".format(e))
            C_Err(len(errors)>0," in COMP_")       
        else:
            P_Log(" [FG][OK]")
        
        # preparamos la estructura final de componentes

        # revisamos si estan los host preparados
        self.uri_nodes={k:get_uri_node(k) for k in self.inits}
        P_Log("[FY]Checking Distributed Hosts ",ln=False)
        errors=[host for host,uri in self.uri_nodes.items() if uri=="0.0.0.0:0"]
        if len(errors)!=0:
            P_Log(" [FR][FAIL]")
            for e in errors:
                P_Log("[FR][ERROR][FW] host {} not is online".format(e))
            C_Err(len(errors)>0," in Distibuted Host")       
        else:
            P_Log(" [FG][OK]")
            
        #pedimos configuracion a los nodos
        P_Log("[FY]Checking Components code",ln=False)
        loader_comps=[config["host"]+"--"+config["_COMP"] for comp,config in self.Instances.items()]
        loader_comps=list(set(loader_comps))

        errors=[]
        config_comps={}  
        for c in loader_comps:
            host,comp=c.split("--")
            comp,cls=comp.split("::")
            if host=="localhost":
                g=CMake(comp)
                errors.extend(g.get_errors(cls))
                config_comps[comp+"::"+cls]=g.get_status(cls)
            else:
                #TODO perdir a los nodos
                pass           
        if len(errors)!=0:
            P_Log(" [FR][FAIL]")
            for e in errors:
                P_Log("[FR][ERROR][FW] {}".format(e))
            C_Err(len(errors)>0," in components code")
        else:
            P_Log(" [FG][OK]")
        
        #actualizamos COMPONENTS con la configuracion del componente
        for name,comp in self.COMPONENTS.items():
            namecomp=comp["_etc"]["_COMP"]
            if namecomp in config_comps:
                self.COMPONENTS[name]=skel.update_skel_dict(self.COMPONENTS[name],config_comps[namecomp]["config"])
                
           
        #chequeamos las interfaces disponibles hay que hacerlo por nodes
        #TODO distribuirlo a nodos
        
        P_Log("[FY]Checking Interfaces ",ln=False)   
        loader_interfaces={host:[] for host in self.inits}
        for c,conf in self.Instances.items():
            if "_INTERFACES" not in conf:
                self.Instances[c]["_INTERFACES"]=[]
            if type(conf["_INTERFACES"])!=list:
                self.Instances[c]["_INTERFACES"]=[conf["_INTERFACES"]]
            loader_interfaces[conf["host"]].extend(self.Instances[c]["_INTERFACES"])
        errors=[]
        self.INTERFACES={}    
        for host,interfaces in loader_interfaces.items():
            if host=="localhost":
                all_i=all_interfaces()
                self.INTERFACES[host]=all_i.get_interfaces(interfaces)
                self.INTERFACES[host]=list(set(self.INTERFACES[host]))
                errors.extend(all_i.get_error_interfaces(interfaces))
            else:
                pass
                #TODO perdir a nodo  
        if len(errors)!=0:
            P_Log(" [FR][FAIL]")
            for e in errors:
                P_Log("[FR][ERROR][FW] {}".format(e))
            C_Err(len(errors)>0," in Interfaces")       
        else:
            P_Log(" [FG][OK]")
      
        # hacemos chequeo sintactico de las instancias      
        #actualizamos COMPONENTS con la configuracion de instances
        for name,comp in self.COMPONENTS.items():
            if name in self.Instances:
                self.COMPONENTS[name]=skel.update_skel_dict(self.COMPONENTS[name],self.Instances[name])      

        errors={}        
        P_Log("[FY]Checking Sintactic Model",ln=False)   
        
        for name,comp in self.COMPONENTS.items():
            check=Sintactic(comp)
            err=check.get_errors()
            if len(err)>0:
                errors[k]=check.get_errors()
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
        check=Semantic(self.COMPONENTS,self.INTERFACES)
        errors=check.get_errors()
        self.COMPONENTS=check.get_skel() 
        if len(errors)==0:
            P_Log(" [FG][OK]")
        else:
            P_Log(" [FR][FAIL]")       
        for e in show_errors:
            P_Log("[FR][ERROR][FW] {}".format(e))
        C_Err(len(errors)>0,"Semantic in model")


   
if __name__ == '__main__':
    if len(sys.argv)< 2:
        P_Log("please type create_model model")
        exit()
    if len(sys.argv)==2:
        import pprint
        #a=Loader_PYRobot(Init={})
        a=Loader_PYRobot(sys.argv[1])
        a.Check()
        comps=a.Get_Skel()
        
        
        
     
        