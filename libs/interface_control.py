#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________


from PYRobot.libs.interfaces import Service


class ControlInterface(Service):

    def hello(self):
        pass

    def shutdown(self):
        pass

    def get_proc(self):
        pass
    
    def get_info(self):
        pass

    def get_name(self):
        pass

    def show_proc(self, all=True):
        pass
    
    def set_logging(self, level=20):
        pass
