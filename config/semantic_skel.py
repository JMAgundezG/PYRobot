#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________

class Semantic(object):
    def __init__(self,comps,all_interfaces):
        self.COMPS=comps
        self.interfaces=all_interfaces
        self.errors=[]
        ATTRIBUTES=[]
        EVENTS=[]
        PUB_TOPICS=[]
        EMIT_TOPICS=[]
        PUB_EVENTS=[]
        EMIT_EVENTS=[]
        RECEIVE=[]
        RECEIVE_EVENTS=[]
        SUB=[]
        SUB_EVENTS=[]
        REQS=[]
        INTERFACES=[]
        for name,comp in self.COMPS.items():
            sufix=comp["_etc"]["name"]+"/"
            attributes=[sufix+k for k,v in comp.items() if k not in ["DOCS","_etc","_PROC"]]
            ATTRIBUTES.extend(attributes)
            events=[sufix+k for k in comp["_etc"]["_EVENTS_"]]
            EVENTS.extend(events)
            pub_topics=[k for k in comp["_etc"]["_PUB"]]
            PUB_TOPICS.extend(pub_topics)
            receive=[sufix+k.split("=")[0]+"="+k.split("=")[1] for k in comp["_etc"]["_RECEIVE"]]
            RECEIVE.extend(receive)
            receive_events=[sufix+k.split("=")[0]+"="+k.split("=")[1] for k in comp["_etc"]["_RECEIVE_EVENTS"]]
            RECEIVE_EVENTS.extend(receive_events)
            sub=[sufix+k.split("=")[0]+"="+k.split("=")[1] for k in comp["_etc"]["_SUB"]]
            SUB.extend(sub)
            sub_events=[sufix+k.split("=")[0]+"="+k.split("=")[1] for k in comp["_etc"]["_SUB_EVENTS"]]
            SUB_EVENTS.extend(sub_events)
            emit_topics=[k for k in comp["_etc"]["_EMIT"]]
            EMIT_TOPICS.extend(emit_topics)
            pub_events=[k for k in comp["_etc"]["_PUB_EVENTS"]]
            PUB_EVENTS.extend(pub_events)
            emit_events=[k for k in comp["_etc"]["_EMIT_EVENTS"]]
            EMIT_EVENTS.extend(emit_events)         
            reqs=[sufix+k.split("=")[0]+"="+k.split("=")[1] for k in comp["_etc"]["_REQ"]]
            REQS.extend(reqs)
            interfaces=[sufix+k for k in comp["_etc"]["_INTERFACES"]]
            INTERFACES.extend(interfaces)
        
        #interfaces no encontradas
        int_locates=[]
        for i in INTERFACES:
            robot,comp,interface=i.split("/")
            host=self.COMPS[comp]["_etc"]["host"]
            locates=[x for x in self.interfaces[host] if x.split("::")[1]==interface]
            if len(locates)>0:
                int_locates.append(comp+"//"+locates[0])
            else:
                self.errors.update(" interface {} not found in component {}".format(interface,comp))
        #print(int_locates)

        #chequeamos pub y emits con atributos 
        errors=["PUB {} not have Attribute definition".format(pub) for pub in PUB_TOPICS if pub not in ATTRIBUTES]
        self.errors.extend(errors)
        errors=["EMIT {} not have Attribute definition".format(pub) for pub in EMIT_TOPICS if pub not in ATTRIBUTES]
        self.errors.extend(errors)

        #chequeamos pub_event y emits_events con eventos definidos
        errors=["PUB_EVENT {} not have EVENT definition".format(pub) for pub in PUB_EVENTS if pub not in EVENTS]
        self.errors.extend(errors)
        errors=["EMIT_EVENT {} not have EVENT definition".format(pub) for pub in EMIT_EVENTS if pub not in EVENTS]
        self.errors.extend(errors)
        
        #chequeamos receive y receive_events
        errors=["RECEIVE {} not emitted".format(x) for x in RECEIVE if x.split("=")[1] not in EMIT_TOPICS]
        self.errors.extend(errors)
        errors=["RECEIVE {} already defined attribute".format(x) for x in RECEIVE if x.split("=")[0] in ATTRIBUTES]
        self.errors.extend(errors)
        errors=["RECEIVE_EVENT {} not emitted".format(x) for x in RECEIVE_EVENTS if x.split("=")[1] not in EMIT_EVENTS]
        self.errors.extend(errors)
        errors=["RECEIVE_EVENT {} already defined attribute".format(x) for x in RECEIVE_EVENTS if x.split("=")[0] in ATTRIBUTES]
        self.errors.extend(errors)

        #chequeamos sub y sub_events
        errors=["SUB {} not subscribed".format(x) for x in SUB if x.split("=")[1] not in PUB_TOPICS]
        self.errors.extend(errors)
        errors=["SUB {} already defined attribute".format(x) for x in SUB if x.split("=")[0] in ATTRIBUTES]
        self.errors.extend(errors)
        errors=["SUB_EVENT {} not emitted".format(x) for x in SUB_EVENTS if x.split("=")[1] not in PUB_EVENTS]
        self.errors.extend(errors)
        errors=["SUB_EVENT {} already defined attribute".format(x) for x in SUB_EVENTS if x.split("=")[0] in ATTRIBUTES]
        self.errors.extend(errors)
        
        #reqs incumplidos
        errors=["_REQ {} not found in INTERFACES".format(x) for x in REQS if x.split("=")[1] not in INTERFACES]
        self.errors.extend(errors)
        errors=["_REQ {} already defined attribute".format(x) for x in REQS if x.split("=")[0] in ATTRIBUTES]
        self.errors.extend(errors)
             
        #convertimos  los conectores
        for name,comp in self.COMPS.items():
            _EVENTS_=self.COMPS[name]["_etc"]["_EVENTS_"]
            self.COMPS[name]["_etc"]["_EMIT_EVENTS"]={x:_EVENTS_[x.split("/")[2]] for x in EMIT_EVENTS if x.split("/")[2] in _EVENTS_}
            self.COMPS[name]["_etc"]["_PUB_EVENTS"]={x:_EVENTS_[x.split("/")[2]] for x in PUB_EVENTS if x.split("/")[2] in _EVENTS_}
            del(self.COMPS[name]["_etc"]["_EVENTS_"])

            self.COMPS[name]["_etc"]["_SUB"]={x.split("=")[0]:x.split("=")[1] for x in comp["_etc"]["_SUB"]}
            self.COMPS[name]["_etc"]["_SUB_EVENTS"]={x.split("=")[0]:x.split("=")[1] for x in comp["_etc"]["_SUB_EVENTS"]}
            self.COMPS[name]["_etc"]["_RECEIVE"]={x.split("=")[0]:x.split("=")[1] for x in comp["_etc"]["_RECEIVE"]}   
            self.COMPS[name]["_etc"]["_RECEIVE_EVENTS"]={x.split("=")[0]:x.split("=")[1] for x in comp["_etc"]["_RECEIVE_EVENTS"]}
            self.COMPS[name]["_etc"]["_REQ"]={x.split("=")[0]:x.split("=")[1] for x in comp["_etc"]["_REQ"]}
            host=self.COMPS[name]["_etc"]["host"]
            self.COMPS[name]["_etc"]["_INTERFACES"]=[x for x in self.interfaces[host] if x.split("::")[1] in comp["_etc"]["_INTERFACES"]]
            
    
    def get_errors(self):
        return self.errors
    
    def get_skel(self):
        return self.COMPS
        

