
from gevent import socket
from gevent import monkey
import paho.mqtt.publish as pub
import paho.mqtt.client as mqtt
from gevent.server import DatagramServer
import time
import json
import ecal.core.core as ecal_core
from ecal.core.publisher import StringPublisher
from ecal.core.subscriber import StringSubscriber
import sys
from types import FunctionType


class EcalDriver(object):
    """
    Driver to communicate with a ECAL server.
    It uses a "Borg" pattern to optimize and clean the code
    """
    __instance = {}
    __initialized = False

    def __init__(self, name: str = "DEFAULT"):
        """
            Constructor
            Params:
                -   name[str]: name of connection in the server
        """
        self.__dict__ = self.__instance
        self.publishers = {}
        self.subscribers = {}

    def init(self):
        """
        Starts the connection with ECAL
        """
        if not EcalDriver.__initialized:
            if not EcalDriver.__initialized:
                ecal_core.initialize(sys.argv, name)
                if not ecal_core.ok():
                    raise Exception("CANNOT CONNECT TO ECAL_CORE")
                self.__initialized = True

    def pub(self, topic: str, msg: str = None) -> None:
        """
        Creates a StringPublisher with a topic if it's not created.
        Also, it sends a message using the referenced StringPublisher
        """
        if topic not in self.publishers.keys():
            self.publishers[topic] = StringPublisher(topic)
        print(ecal_core.ok())
        if msg is not None:
            self.publishers[topic].send(msg)

    def create_sub(self, topic: str, callback: FunctionType = (lambda x: print(x))) -> None:
        """
        Creates a StringSubscriber and, if the callback is not None,
        implements a callback
        """
        if topic not in self.subscribers.keys():
            self.subscribers[topic] = StringSubscriber(topic)
            if callback is not None:
                self.subscribers[topic].set_callback(callback)

    def receive_from_topic(self, topic) -> tuple:
        """
        Receives the message in the topic if it exists
        """
        if topic in self.subscribers.keys():
            ret, msg, time = self.subscribers[topic].receive(50000)
            if ret == 0:
                return 0, msg
            else:
                return ret, ""
        return -1, ""

    def finalize(self):
        """
        Finalizes the connection with ECAL
        """
        if EcalDriver.__initialized:
            ecal_core.finalize()
            EcalDriver.__initialized = False
            self.publishers = {}
            self.subscribers = {}

    def __del__(self):
        """
        Destructor of the object
        It just calls the self.finalize() method
        """

        self.finalize()


class MqttPub(object):
    def __init__(self, host, port, qos=0, retain=False):
        self.host = host
        self.port = port
        self.qos = qos
        self.retain = retain

    def pub(self, topic, data, data_type="TOPICS"):
        payload = json.dumps([data, data_type, time.time()])
        pub.single(topic, payload, hostname=self.host, port=self.port,qos=self.qos)


class BroadcastPub(object):
    def __init__(self, port):
        self.broad_host = '255.255.255.255'
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def pub(self, topic, data, data_type="TOPICS"):
        robot, comp, topic = topic.split("/")
        data = [robot + "/" + comp, topic, data]
        payload = json.dumps([data, data_type, time.time()])
        self.client.sendto(payload.encode(), (self.broad_host, self.port))


class MqttSub(object):
    def __init__(self, host, port, on_handler, qos=0):
        self.host = host
        self.port = port
        self.qos = qos
        self.client = mqtt.Client()
        self.client.on_message=on_handler
        self.client.connect(host=self.host, port=self.port, keepalive=60)
        self.client.loop_start()

    def connect(self, proxies):
        topics = [(proxy, self.qos) for proxy in proxies]
        self.client.subscribe(topic=topics)

