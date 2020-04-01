#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________


from PYRobot.libs.interfaces import Service


class Control_Interface(Service):

    def hello(self):
        pass

    def shutdown(self):
        pass

    def get_PROC(self):
        pass
    
    def Get_INFO(self):
        pass

    def get_name(self):
        pass

    def show_PROC(self,all=True):
        pass
    
    def Set_Logging(self,level=20):
        pass
