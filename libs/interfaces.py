#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________

import inspect
from mprpc import RPCServer


def get_func(cls):
    return [func for func in dir(cls) if callable(getattr(cls, func)) and
            not func.startswith("_")]


def check_functions(cls, cls1):
    return [x for x in get_func(cls) if x not in get_func(cls1)]


def get_signature(fn):
    fun_param = str(inspect.signature(fn))
    params = inspect.signature(fn).parameters
    args = []
    for p in params.values():
        if p.name != "self":
            args.append(p.name)
    return fun_param, args


class Service(RPCServer):
    pass


class Interface(object):
    def __new__(cls, service, component):
        
        not_implemented = check_functions(service, component)

        def_interface = {}
        for x in get_func(service):
            def_interface[x] = get_signature(eval("service." + x))
            if x not in Not_Implemented:
                setattr(service, x, eval("component." + x))
        # print(def_interface)
        setattr(service, "def_interface", def_interface)
        setattr(service, "Not_Implemented", Not_Implemented)
        setattr(service, "G_E_T_Configuration", cls.Get_Configuration)

        return service

    def get_configuration(self):
        return self.def_interface
