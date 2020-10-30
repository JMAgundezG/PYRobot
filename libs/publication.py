#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
____________
Author: - Paco Andres
Collaborators: - Cristian Vazquez
               - Jose Manuel Agundez
Created: - 15/04/2019
____________

"""

from PYRobot.utils.utils import get_ip_port
from PYRobot.botlogging.coloramadefs import P_Log
from PYRobot.libs.comunications import Mqtt_Pub, Broadcast_Pub


class Publication(object):

    def __init__(self, name, mqtt_uri, broadcast, qos=0):
        self.host, self.port = get_ip_port(mqtt_uri)
        self.robot, self.comp = name.split("/")
        self.mqtt_uri = mqtt_uri
        self.broadcast = broadcast
        self.qos = qos
        self.topics = {}
        self.pre = str(name) + "/"
        self.pre_events = self.robot + "/events/" + self.comp + "/"
        self.mqtt_enable = False
        self.broadcast_enable = False
        self.multicast_enable = False

    def start(self):
        mq = [topic for topic, cls_tipe in self.topics.items() if cls_tipe[1] == "MQ"]
        broad = [topic for topic, cls_tipe in self.topics.items() if cls_tipe[1] == "BR"]
        if len(mq) > 0:
            self.mqtt_enable = True
            self.Mqtt = Mqtt_Pub(self.host, self.port, self.qos)
            print("PUB mq start")
        if len(broad) > 0:
            self.broadcast_enable = True
            self.Broad = Broadcast_Pub(self.broadcast)
            print("PUB br_start")

    def add_topic(self, cls, topic):
        if cls in ["TOPICS", "EVENTS"]:
            tipe, topic = topic.split("::")
            self.topics[topic] = (cls, tipe)

    def add_topics(self, cls, *topics):
        for t in topics:
            self.add_topic(cls, t)

    def get_topics(self, tipe=None):
        if tipe == None:
            return {k: v[1] for k, v in self.topics.items()}
        else:
            return {k: v[1] for k, v in self.topics.items() if v[0] == tipe}

    def get_events(self, tipe=None):
        if tipe == None:
            return {k: v[1] for k, v in self.topics.items() if v[0] == "EVENTS"}
        else:
            return {k: v[1] for k, v in self.topics.items() if v[1] == tipe and v[0] == "EVENTS"}

    def Pub(self, topic, data):
        if topic in self.topics:
            cls, tipe = self.topics[topic]
            # print("publications:",cls,tipe,data)
            if tipe == "MQ" and self.mqtt_enable:
                self.Mqtt.pub(self.pre + topic, data, data_type=cls)
            if tipe == "BR" and self.broadcast_enable:
                self.Broad.pub(self.pre + topic, data, data_type=cls)
            if tipe == "MC" and self.multicast_enable:
                pass
