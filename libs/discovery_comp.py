#!/usr/bin/env python3
# ____________developed by paco andres_29/02/2020___________________

from gevent.server import DatagramServer
from gevent import socket
import json
import re

buff_size=4096

class discovery(object):
    def __init__(self,broadcast_port=9999):
        self._PROC["dst_client"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._PROC["dst_client"].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._PROC["dst_client"].setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._PROC["dst_client"].settimeout(0.1)
        self._PROC["dst_server"] = DatagramServer(('', self._etc["broadcast_port"]), handle=self._receive)
        self._PROC["dst_server"].start()
        #print(self.__dict__)
    

    def dsc_get(self,key):
        robot,comp,query=key.split("/")
        key="{}::{}".format(self._etc["name"],key)
        self._PROC["dst_client"].sendto(key.encode(), ("255.255.255.255", self._etc["broadcast_port"]))
        #print("getting",key)
        instances=[]
        try:
           while True:
               data,address = self._PROC["dst_client"].recvfrom(buff_size)
               data=data.decode()
               #print("raw data",data)
               instances.append(data)
        except:
            pass
        if query=="Broker":
            inst= self._Get_Broker(instances)
            return inst
        if query=="Name":
            inst= self._Get_Name(instances)
            return inst
        if query=="Interfaces":
            inst= self._Get_Interfaces(instances)
            #print("send", inst)
            return inst
        if query=="Control":
            inst= self._Get_Control(instances)
            #print("send", inst)
            return inst
        if query=="Running":
            inst= self._Get_Running(instances)
            #print("send", inst)
            return inst

    def _receive(self, key, address):
        # data sender::robot/component/required
        key=key.decode()
        sender,query=key.split("::")
        #if sender==self._etc["name"]:
        #    return False
        if self._PROC["status"]!="OK":
            return False
        
        robot,comp,query=query.split("/")
        name=robot+"/"+comp
        name=name.replace("*",".+")
        name=name.replace("?",".+")
        if re.match(name,self._etc["name"]):
            if query=="Broker":
                send=self._Send_Broker()
                self._PROC["dst_server"].sendto(send.encode(), address)
            if query=="Name":
                send=self._Send_Name()
                self._PROC["dst_server"].sendto(send.encode(), address)
            if query=="Interfaces":
                for inter in self._Send_Interfaces():
                    inter=json.dumps(inter)
                    self._PROC["dst_server"].sendto(inter.encode(), address)
            if query=="Control":
                for inter in self._Send_Control():
                    inter=json.dumps(inter)
                    self._PROC["dst_server"].sendto(inter.encode(), address)
            if query=="Running":
                send=self._Send_Running()
                #print(send)
                self._PROC["dst_server"].sendto(send.encode(), address)
            
    def _Send_Broker(self):
        return self._etc["MQTT_uri"]
    
    def _Get_Broker(self,instances):
        broker=[x for x in instances if x!="0.0.0.0:0"]
        if len(broker)>=1:
            return broker[0]
        else:
            return "0.0.0.0:0"
    
    def _Send_Name(self):
        return self._etc["name"]
    
    def _Get_Name(self,instances):
        return instances

    def _Send_Running(self):
        if self._PROC["running"]=="RUN":
            return self._etc["name"]
        else:
            return self._PROC["running"]
    
    def _Get_Running(self,instances):
        return instances
    
    def _Send_Interfaces(self):
            return self._PROC["info"]
        
    def _Get_Interfaces(self,instances):
        instances=[json.loads(x) for x in instances]
        interfaces={x[0]:x[1] for x in instances if "Control_Interface" not in x[0]}
        #print("get ",interfaces)
        return interfaces
    
    def _Send_Control(self):
            return self._PROC["info"]
        
    def _Get_Control(self,instances):
        instances=[json.loads(x) for x in instances]
        interfaces={x[0]:x[1] for x in instances if "Control_Interface" in x[0]}
        #print("get ",interfaces)
        return interfaces

if __name__ == '__main__':
    pass