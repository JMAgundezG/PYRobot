#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________

from pyparsing import *
import copy
from inspect import isfunction

def set_COMP(s,l,t):
    if t[-2]!="::":
        t.append("::")
        t.append(t[-2])
    return "".join(t)

def set_PROXY(s,l,t):
    #print("PROXY",t,len(t))   
    if len(t)==3:
        return "{R}/"+s
    
def set_TOPIC(s,l,t):
    #print("TOPIC",t,len(t))   
    if len(t)==1:
        return "{R}/{C}/"+s
    if len(t)==3:
        return "{R}/"+s

def set_CONNECTOR(s,l,t):
    #print("CONNECTOR",t,len(t))    
    if len(t)==5:
        t.insert(2,"{R}/")
    return "".join(t)
  

Token=Word(alphas,alphanums + "_")
Token.setParseAction(lambda s,l,t:"".join(t))

NAME=Token+"/"+Token
NAME.setParseAction(lambda s,l,t:s)

TOPIC=(Token+"/")*(0,2)+Token
TOPIC.setParseAction(set_TOPIC)

KEY=Token+":"+Word(printables)
KEY.setParseAction(lambda s,l,t:s)

integer = Word( nums )

IP = Combine(integer + "." + integer + "." + integer + "." + integer)
IP.setParseAction(lambda s,l,t:s)

COMP=(Token+'/')*(1,5)+Token+("::"+Token)*(0,1)
COMP.setParseAction(set_COMP)

PROXY=(Token+"/")*(1,2)+Token
PROXY.setParseAction(set_PROXY)
CONNECTOR=Token+'='+(Token+"/")*(1,2)+Token
CONNECTOR.setParseAction(set_CONNECTOR)


Sintactic_Skel={
"_etc":{
    "name":NAME,
    "host":Token,
    "node":Token,
    "model":Token,
    "robot":Token,
    "mode":lambda t:(False,t) if t in ["public","local"] else (True,t),
    "sys":lambda t: (False,t) if type(t)==bool else (True,t),
    "ethernet":Token,
    "ip":IP,
    "KEY":KEY,
    "component":None,
    "cls":None,
    "port":lambda t: (False,t) if type(t)==int else (True,t),
    "MQTT_port":lambda t: (False,t) if type(t)==int else (True,t),
    "MQTT_uri":None,
    "EMIT_port":lambda t: (False,t) if type(t)==int else (True,t),
    "broadcast_port":lambda t: (False,t) if type(t)==int else (True,t),
    "def_worker":lambda t: (False,t) if type(t)==bool else (True,t),
    "frec":lambda t: (False,t) if type(t)==float else (True,t),
    "public_sync":lambda t: (False,t) if type(t)==bool else (True,t),
    "running":None,
    "logging_level":lambda t: (False,t) if type(t)==int else (True,t),
    "_COMP":COMP,
    "_INTERFACES":Token,
    "_REQ":CONNECTOR,
    "_PUB":TOPIC,
    "_SUB":CONNECTOR,
    "_PUB_EVENTS":TOPIC,
    "_SUB_EVENTS":CONNECTOR,
    "_EMIT":TOPIC,
    "_RECEIVE":CONNECTOR,
    "_EMIT_EVENTS":TOPIC,
    "_RECEIVE_EVENTS":CONNECTOR,
    "_EVENTS_":None,
    "_REQUIRES_":Token
    }
}

_OPTIONS=[k for k in Sintactic_Skel["_etc"] if k[0]=="_" ]

def GET_COMP(value):
    try:
        sal=COMP.parseString(value)
        sal=sal[0]
        return sal+"--OK"
    except:
        return value+"--ERROR"

class Sintactic(object):
    def __init__(self,skel):
        self.skel=copy.deepcopy(skel)
        self.etc=self.skel["_etc"]
        self.name=self.etc["name"]
        self.robot,self.component=self.name.split("/")
        self.errors={}
        self.check()
        
        
    def __GET(self,parse,value):
        try:
            if isfunction(parse):
                return parse(value)
            else:
                sal=parse.parseString(value)
                sal=sal[0].format(R=self.robot,C=self.component)
                #sal=sal.replace("<C>",self.component)
                return False,sal
        except:
            return (True,value)
    
    def get_errors(self):
        return self.errors
    
    def get_skel(self):
        return self.skel
    
    def check(self):
        for k,v in self.etc.items():
            if Sintactic_Skel["_etc"][k] is not None:
                if type(v)==list:
                    list_err=[]
                    list_v=[]
                    for item in v:
                        err,val=self.__GET(Sintactic_Skel["_etc"][k],item)
                        list_v.append(val)
                        if err:
                            list_err.append(val)
                    self.etc[k]=list_v
                    if (len(list_err)>0):
                        self.errors[k]=list_err
                else:
                    err,val=self.__GET(Sintactic_Skel["_etc"][k],v)
                    if k[0]=="_" and k!="_COMP":
                        val=[val]
                    self.etc[k]=val
                    if err:
                        self.errors[k]=v

