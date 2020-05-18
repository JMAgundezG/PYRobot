import os
import sys
from pyparsing import *
import importlib
import inspect
from PYRobot.utils.utils import get_PYRobots_dir
from PYRobot.botlogging.coloramadefs import P_Log

robots_dir=get_PYRobots_dir()
sys.path.append(robots_dir+"components")
dir_comp="components/"



def get_packages_not_inst(lines):
    pack = Word(srange("[a-zA-Z_]"), srange("[a-zA-Z0-9_.]"))
    subpack = Word(srange("[a-zA-Z_]*"), srange("[a-zA-Z0-9_,]"))
    package_import = Suppress("import ")+pack
    package_from = Suppress("from ")+pack
    packages=[]
    for l in lines: 
        try:
            m=package_import.parseString(l) 
            packages.extend(m)
        except:
            pass
        try:
            m=package_from.parseString(l) 
            packages.extend(m)
        except:
            pass
    packages=list(set(packages))
    errors=[]
    for p in packages:
        try:
            m=importlib.import_module(p)
        except:
            errors.append("Please Run pip3 install "+p)    
    return errors

def get_comp_cls(lines):
    name=Word(srange("[a-zA-Z_]"), srange("[a-zA-Z0-9_]"))
    comp_class=Suppress("class ")+name+Suppress("(control.Control):")
    comp=[]
    for l in lines: 
        try:
            m=comp_class.parseString(l)
            comp.extend(m) 
        except:
            pass
    return comp

def load_module_options(module):
    config={"_EVENTS_":{}}
    try:
        module=importlib.import_module(module)
        classes={name:obj for name,obj in inspect.getmembers(module,inspect.isclass) if name!="Service"}
        attributes=[x for x in module.__dict__ if not x.find("__")==0 and x not in classes and x!="Service"]
        #config["_INTERFACES_AVAILABLE"]=classes
        opt_loaded={k:getattr(module,k) for k in attributes}
        for k,v in opt_loaded.items():
            if k.find("_EVENTS_")==0:
                config["_EVENTS_"][k.split("_EVENTS_")[1]]=v
            else:
                config[k]=v
    except:
        config={}    
    return config

def get_interface_cls(f):
    name=Word(srange("[a-zA-Z_]"), srange("[a-zA-Z0-9_]"))
    interface_class=Suppress("class ")+name+Suppress("(Service):")
    interface=[]
    module=f.replace(robots_dir,"").replace("/",".").replace(".py","")
    
    with open(f,"r") as file:
        lines=file.readlines()
        for l in lines: 
            try:
                m=interface_class.parseString(l)
                interface.extend([module+"::"+c for c in m])  
            except:
                pass
    errors=check_module(module)
    config={}
    if len(errors)==0:
        config=load_module_options(module)
    return errors,interface,config

def check_imports(imports):
    errors=[]
    for p in imports:
        try:
            m=importlib.import_module(p)
        except:
            errors.append(p)
    return errors

def check_module(module):
    errors=[]
    try:
        m=importlib.import_module(module)
    except Exception as e:
        errors.append(module+"-->"+str(e))
    return errors

class all_interfaces(object):
    def __init__(self):
        interface_dir=robots_dir+dir_comp
        confiles=[]
        for path, dirs, files in os.walk(interface_dir):
            if "__" not in path:
                for f in files:
                    if ("conf_" in f):
                        confiles.append(path+"/"+f)
        dir_interfaces=interface_dir+"interfaces/"
        self.interfaces={}
        files_interfaces=[dir_interfaces+x for x in os.listdir(dir_interfaces) if x.find(".py")!=-1 and "__init__" not in x]
        files_interfaces.extend(confiles)
        
        for f in files_interfaces:
            #module=f.replace(robots_dir,"").replace("/",".").replace(".py","")
            errors,inter,_=get_interface_cls(f)
            for i in inter:
                self.interfaces[i]=errors
                
    def get_all_interfaces(self):    
        return [x for x,e in self.interfaces.items() if len(e)==0]
    
    def get_interfaces(self,l):
        if type(l)not in [list,tuple]:
            l=[l]
        return [x for i in l for x in self.get_all_interfaces() if x.split("::")[1]==i]

    def get_error_interfaces(self,l):
        if type(l) not in [list,tuple]:
            l=[l]
        cls=[k.split("::")[1] for k in self.interfaces]
        not_found=["Interface {} not found".format(x) for x in l if x not in cls]
        allerrors={x:e for x,e in self.interfaces.items() for i in l if len(e)!=0 and "::"+i in x}
        errors=[]
        errors.extend(not_found)
        for i,e in allerrors.items():
            errors.extend(e)
        return errors
            
class CMake(object):
    def __init__(self,comp):
        self.cls={}
        comp=comp.replace("components","")
        self.component=comp
        files_comp,files_conf=self.__get_files()

        cls=[]
        for f in files_comp:
            module=f.replace("/",".").replace(".py","")
            with open(robots_dir+f, 'r') as file:
                lines=file.readlines()
                cls=get_comp_cls(lines)
                need_packages=get_packages_not_inst(lines)
                run_errors=check_module(module)
            for c in cls:
                self.cls[c]={}
                self.cls[c]["config"]={}
                #self.cls[c]["config"]["component"]=module
                self.cls[c]["config"]["cls"]=module+"::"+c
                self.cls[c]["need_packages"]=need_packages
                self.cls[c]["run_errors"]=run_errors
                fileconf=dir_comp+comp+"/conf_"+c+".py"
                if fileconf in files_conf:
                    errors,interface,config=get_interface_cls(robots_dir+fileconf)
                    self.cls[c]["run_errors"].extend(errors)
                    self.cls[c]["config"].update(config)
                    #self.cls[c]["interfaces"]=interface
                    
    def __get_files(self):
        self.module_errors=[]
        self.ismodule=False
        files_comp=[]
        files_conf=[]
        try:
            files_comp=[dir_comp+self.component+"/"+x for x in os.listdir(robots_dir+dir_comp+self.component) if x.find(".py")!=-1 and "conf_" not in x]
        except Exception as e:
            self.module_errors.append(str(e))
        try:
            files_conf=[dir_comp+self.component+"/"+x for x in os.listdir(robots_dir+dir_comp+self.component) if x.find(".py")!=-1 and "conf_" in x]
        except Exception as e:
            self.module_errors.append(str(e))
        try:
            files_comp.remove(dir_comp+self.component+"/"+"__init__.py")
            self.ismodule=True
        except Exception as e:
            self.module_errors.append("No __init__ file found in modules")
        return files_comp, files_conf

    def get_module_errors(self):
        return self.module_errors
    
    def show_module_errors(self):
        if len(self.module_errors)>0:
            for e in self.module_errors:
                P_Log("\t[FR][ERROR][FW] {}".format(e))
            return True
        return False
    
    def get_status(self,c):
        if c in self.cls:
            return self.cls[c]
        else:
            return ["{} no found in {}".format(c,self.component)]
        if c is None:
            c=list(self.cls)[0]
        return self.cls[c]
    
    def get_errors(self,c):
        if c in self.cls:
            errors=self.cls[c]["run_errors"]+self.cls[c]["need_packages"]+self.module_errors
        else:
            errors=["{} no found in {}".format(c,self.component)]
        return errors
    
    def get_classes(self):
        return [x for x in self.cls]
    
    def show_status(self,c):
        if self.show_module_errors():
            return ""
        P_Log("[FG]Checking [FW]{}::{}".format(self.component,c))
        if c not in self.cls:
            P_Log("\t[FR][ERROR][FW] Class {} not found in {}".format(c,self.component))
            return ""
        if len(self.cls[c]["run_errors"])>0 or len(self.cls[c]["need_packages"])>0:
            info=self.cls[c]
            for e in info["run_errors"]:
                P_Log("\t[FR][ERROR][FW] {}".format(e))
            for p in info["need_packages"]:
                P_Log("\t[FY][Install][FW] {} (sudo pip3 install {})".format(p,p))
            return ""
        info=self.cls[c]
        P_Log("\t [FG][OK][FW] Loading MODULE: {}".format(info["module"]))
        if info["config"]!={}:
            P_Log("\t [FG][OK][FW] Loading Configuration")
            for i in info["interfaces"]:
                P_Log("\t [FG][OK][FW] Interface: {}".format(i))
        else:
            P_Log("\t Configuration file not found")
            

if __name__ == '__main__':  
    pass
    
