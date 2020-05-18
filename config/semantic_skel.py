#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________

class Semantic(object):
    def __init__(self,comps):
        self.COMPS=comps
        self.errors=[]
        self.warnings=[]
        ATTRIBUTES=[]
        EVENTS=[]
        _TOPICS=[]
        _EVENTS=[]
        SUS=[]
        PROXYS=[]
        INTERFACES=[]
        FULL_EVENTS=[]
        for name,comp in self.COMPS.items():
            sufix=comp["_etc"]["name"]+"/"
            attributes=[sufix+k for k,v in comp.items() if k not in ["DOCS","_etc","_PROC"]]
            ATTRIBUTES.extend(attributes)
            events=comp["_etc"]["_EVENTS_"]
            EVENTS.extend(events)
            _topics=[sufix+t.split("::")[1] for t in comp["_etc"]["_TOPICS"]]
            _TOPICS.extend(_topics)
            sus=[sufix+k.split("=")[0]+"="+k.split("=")[1] for k in comp["_etc"]["_SUS"]]
            SUS.extend(sus)
            _events=[t.split("::")[1] for t in comp["_etc"]["_EVENTS"]]
            full_events=[sufix+x for x in _events]
            _EVENTS.extend(_events)
            FULL_EVENTS.extend(full_events)
            proxys=[sufix+k.split("=")[0]+"="+k.split("=")[1] for k in comp["_etc"]["_PROXYS"]]
            PROXYS.extend(proxys)
            interfaces=[sufix+k for k in comp["_etc"]["_INTERFACES"]]
            INTERFACES.extend(interfaces)

        # #interfaces no encontradas
        # int_locates=[]
        # for i in INTERFACES:
        #     robot,comp,interface=i.split("/")
        #     host=self.COMPS[comp]["_etc"]["host"]
        #     locates=[x for x in self.interfaces[host] if x.split("::")[1]==interface]
        #     if len(locates)>0:
        #         int_locates.append(comp+"//"+locates[0])
        #     else:
        #         self.errors.update(" interface {} not found in component {}".format(interface,comp))
        # #print(int_locates)


        #chequeamos _events con eventos definidos
        errors=["EVENT {} not have EVENT definition".format(pub) for pub in _EVENTS if pub not in EVENTS]
        self.errors.extend(errors)
        

        # #chequeamos suscribers 
        # errors=["_SUS {} not suscribed".format(x) for x in SUS if x.split("=")[1] not in _TOPICS+FULL_EVENTS]
        # self.warnings.extend(errors)
        
        #reqs incumplidos 
        #TODO faltan los __REQUIRE__
        # errors=["_PROXYS {} not found in INTERFACES".format(x) for x in PROXYS if x.split("=")[1] not in INTERFACES]
        # self.errors.extend(errors)
        errors=["_PROXYS {} already defined attribute".format(x) for x in PROXYS if x.split("=")[0] in ATTRIBUTES]
        self.errors.extend(errors)
             
        #convertimos  los conectores
        
        for name,comp in self.COMPS.items():
            
            _EVENTS_=self.COMPS[name]["_etc"]["_EVENTS_"]
            myevents=self.COMPS[name]["_etc"]["_EVENTS"]
            self.COMPS[name]["_etc"]["_EVENTS"]={x:_EVENTS_[x.split("::")[1]] for x in myevents if x.split("::")[1] in _EVENTS_}
            del(self.COMPS[name]["_etc"]["_EVENTS_"])
            self.COMPS[name]["_etc"]["_SUS"]={x.split("=")[0]:x.split("=")[1] for x in comp["_etc"]["_SUS"]}
            self.COMPS[name]["_etc"]["_PROXYS"]={x.split("=")[0]:x.split("=")[1] for x in comp["_etc"]["_PROXYS"]}
            host=self.COMPS[name]["_etc"]["host"]
            self.COMPS[name]["_etc"]["_INTERFACES"]=self.COMPS[name]["_etc"]["_CLS_INTERFACES"]
            del(self.COMPS[name]["_etc"]["_CLS_INTERFACES"])
            
    
    def get_errors(self):
        return self.errors
    def get_warnings(self):
        return self.warnings
    
    def get_skel(self):
        return self.COMPS
        

