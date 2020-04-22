#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________

import time
from  threading import Thread
from PYRobot.botlogging.coloramadefs import P_Log
import json
from gevent import socket
from gevent import Timeout
from gevent import monkey
monkey.patch_all(thread=False)
from deepdiff import DeepDiff

class broadcast_publication(object):
    def __init__(self,port):
        self.broad_host = '255.255.255.255'
        self.port=port
        self.client=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def public(self,payload,port=""):
        if port=="":
            port=self.port
        self.client.sendto(payload.encode(), (self.broad_host,port))

class Emitter(object):

    def __init__(self,name,obj,port=9999,sync=True,frec=0.01):
        self._name=name
        self.topics=set()
        self.topics_last={}
        self.events={}
        self.events_last={}
        self.sync=sync
        self.obj=obj
        self.frec=frec
        self.work=True
        self.pre= str(name + "/")
        self.port=port
        self.pub=broadcast_publication(port)


    def add_topics(self,*topics):
        for n in topics:
            if hasattr(self.obj,n):
                self.topics.add(n)
                self.topics_last[n]={}
            else:
                P_Log("{} not registered".format(n))

    def get_topics(self):
        return list(self.topics)

    def get_events(self):
        return [x for x in self.events]

    def add_events(self,entity,*events):
        for x in events:
            self.add_event(entity,x)

    def add_event(self,entity,event):
        try:
            name,fn=event.split("::")
            self.events.setdefault(entity,[])
            fn=fn.replace("self.","self.obj.")
            self.events[entity].append((name,fn))
            self.events_last[entity]=[]
            #print("Pub events",self.events)
        except:
            raise
            P_Log("error loading {}".format(event))

    def check(self,fn):
        try:
            return eval(fn)
        except Exception as ex:
            #print(str(ex))
            return "ERR"

    def Pub_events(self):
        # todo if no events what happend
        events_sal={}
        for entity,events in self.events.items():
            send_events=[k for k,v in events if self.check(v)==True]
            if DeepDiff(send_events,self.events_last[entity])!={}:
                events_sal[self.pre+entity]=send_events
                self.events_last[entity]=send_events
        #print(events_sal)
        if len(events_sal)>0:
            payload_value =json.dumps([events_sal,"E",time.time()])
            self.pub.public(payload_value)



    def Public(self):
        if not self.sync:
            self.Pub_topics()
            self.Pub_events()
        else:
            P_Log("Mode syncronous activated")

    def Pub_topics(self):
        sal={self.pre+n:getattr(self.obj,n) for n in self.topics if
                DeepDiff(self.topics_last[n],getattr(self.obj,n))!={}}
        self.topics_last={n:getattr(self.obj,n) for n in self.topics}
        if len(sal)>0:
            payload_value =json.dumps([sal,"V",time.time()])
            #print(payload_value)
            self.pub.public(payload_value)

    def _Do_Pub(self):
        while self.work:
            self.Pub_topics()
            self.Pub_events()
            time.sleep(self.frec)

    def stop(self):
        self.work=False

    def change_frec(self,frec):
        if frec>0:
            self.frec=frec

    def start(self):
        if self.sync:
            self.work=True
            self.thread=Thread(target=self._Do_Pub,name=self._name+":emitter")
            self.thread.setDaemon(True)
            self.thread.start()
        else:
            P_Log("Mode asyncronous activated")
