#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________

from PYRobot.botlogging.coloramadefs import P_Log
import time
from  threading import Thread
from PYRobot.utils.utils import get_ip_port
import json
from gevent.server import DatagramServer


class Receiver(object):
    def __init__(self,name,port=10000,obj=None):
        self.name=name
        self.topics={}
        self.events={}
        self.obj=obj
        self.port=port

    def receive(self, data, address):
        value=json.loads(data.decode())
        payload,type,date=json.loads(data.decode())
        if type=="E":
            update={self.events[k][0]:v for k,v in payload.items() if k in self.events}
            handlers={self.events[k][0]:self.events[k][1] for k in payload
                        if k in self.events and self.events[k][1] is not None}
            self.obj.__dict__.update(update)
            try:
                for event,method in handlers.items():
                    method(event,update[event],date)
            except:
                P_Log("[FR][ERROR][FW] In handler method {}".format(method))
        if type=="V":
            update={self.topics[k]:v for k,v in payload.items() if k in self.topics}
            self.obj.__dict__.update(update)

    def connect(self):
        self.bcast = DatagramServer(('', self.port), handle=self.receive)
        self.bcast.start()

    def loop(self):
        self.client.loop()

    def subscribe_topics(self,**topics):
        for item,proxy in topics.items():
            self.topics[proxy]=item
            if item not in self.obj.__dict__:
                setattr(self.obj,item,None)

    def subscribe_events(self,**events):
        for item,proxy in events.items():
            self.events[proxy]=[item,None]
            if item not in self.obj.__dict__:
                setattr(self.obj,item,[])

    def get_topics(self):
        return list(self.topics.values())

    def get_events(self):
        return list(self.events)

    def start(self):
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()

    def add_handler(self,event,handler):
        events=[k for k,v in self.events.items() if v[0]==event]
        if len(events)==1:
            ev=events[0]
            self.events[ev][1]=handler
