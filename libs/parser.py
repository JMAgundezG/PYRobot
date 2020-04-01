#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ____________developed by paco andres____________________

from pyparsing import *
import copy



TOPIC=Word(srange("[a-zA-Z_]"), srange("[a-zA-Z0-9_]"))
token=TOPIC
PROXY=TOPIC+('/'+TOPIC)*(1,2)
_SUB_=TOPIC+'='+PROXY
_INTERFACE=TOPIC
_REQ_= _SUB_
COMP=((TOPIC+'/')*(0,1)+TOPIC)+("::"+TOPIC)*(0,1)
KEY=token+"@"+Word(alphanums)
COMPONENT=(TOPIC+"://")+TOPIC+('/'+TOPIC)*(0,1)

def get_TOPIC(cad):
    try:
        TOPIC.parseString(cad)
        return cad
    except:
        return ""

def is_TOPIC(cad):
    return get_TOPIC(cad)!=""

def get_COMP(cad):
    try:
        comp=COMP.parseString(cad)
        #print(comp)
        if len(comp)==1 or comp[1]!='/':
            comp.insert(0,"/")
            comp.insert(0,"stable")
        if len(comp)<4 or comp[3]!="::":
            cls=comp[-1]
            comp.append("::")
            comp.append(cls)
        if comp[0] not in ["stable","developing","sys","local"]:
            comp=[]
        #print("".join(comp))
        return "".join(comp)
    except:
        raise
        return ""

def is_COMP(cad):
    return get_COMP(cad)!=""

def get_PROXY(cad):
    pre=""
    try:
        proxy=PROXY.parseString(cad)
        if len(proxy)==3:
            pre='LOCAL/'
        return pre+"".join(proxy)
    except:
        return ""

def is_PROXY(cad):
    return get_PROXY(cad)!=""

def get_INTERFACE(cad):
    try:
        interface=_INTERFACE.parseString(cad)
    except:
        return ""

def is_INTERFACE(cad):
    return get_INTERFACE(cad)!=""

def get_SUB(cad):
    sal={}
    try:
        sub=_SUB_.parseString(cad)
        sal[sub[0]]=get_PROXY("".join(sub[2:]))
        return sal
    except:
        return {}

def is_SUB(cad):
    return get_SUB(cad)!={}

def get_REQ(cad):
    return get_SUB(cad)

def is_REQ(cad):
    return is_REQ(cad)


def get_COMPONENT(cad):
    pre=""
    try:
        comp=COMPONENT.parseString(cad)
        if len(comp)==3:
            comp.insert(2,"/")
            comp.insert(2,"LOCAL")
        return "".join(comp)
    except:
        return ""

def is_COMPONENT(cad):
    return get_COMPONENT(cad)!=""

def instance_check(instance):
    #labels=["_INTERFACES","_PUB","_SUB","_EMIT","_RECEIVE","_PUB_EVENTS","_EMIT_EVENTS",
    #        "_SUB_EVENTS","_RECEIVE_EVENTS","_REQ"]
    lab_parser={"_COMP":get_COMP,"_PUB":get_TOPIC,"_EMIT":get_TOPIC,"_INTERFACES":get_TOPIC,
                "_SUB":get_SUB,"_RECEIVE":get_SUB,"_SUB_EVENTS":get_SUB,"_RECEIVE_EVENTS":get_SUB,
                "_PUB_EVENTS":get_TOPIC,"_EMIT_EVENTS":get_TOPIC,"_REQ":get_REQ}
    for k,v in instance.items():
        if (k in lab_parser) and (type(v) not in [list,tuple]):
            if k!="_COMP":
                instance[k]=[v]
    errors=[]
    inst=copy.deepcopy(instance)
    for key,value in instance.items():
        if key in lab_parser:
            if type(value) in [list,tuple]:
                if key in ["_REQ","_SUB","_SUB_EVENTS","_RECEIVE","_RECEIVE_EVENTS"]:
                    opts={}
                else:
                    opts=[]
                for v in value:
                    ret=lab_parser[key](v)
                    if len(ret)==0:
                        errors.append((key,v))
                    else:
                        if type(opts)==list:
                            opts.append(ret)
                        else:
                            opts.update(ret)
                inst[key]=opts
            else:
                inst[key]=lab_parser[key](value)
                if inst[key]=="":
                    errors.append((key,value))
    return inst,errors
