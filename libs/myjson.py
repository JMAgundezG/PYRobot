#!/usr/bin/env python3
# ____________developed by paco andres_15/04/2019___________________

import json
import re
import collections
from PYRobot.libs.botlogging.coloramadefs import P_Log

class MyJson(object):
    def __init__(self, filename):
        self.json = self.load_json(filename)

    def load_json(self, filename):
        self.filename = filename if (
                ".json" in filename) else (filename + ".json")
        try:
            data = open(filename).read()
            data = self.del_coments(data)
            data = self.substitute_params(data)
            data_json = json.loads(data)
        except ValueError as e:
            P_Log("[FR]ERROR:[FS] JSON incorrectly described: {}".format(str(e)))
            exit()
        except Exception:
            P_Log("[FR]ERROR:[FS] file not found loading {}".format(filename))
            return {}
        return data_json

    def del_coments(self, data, ch="#"):
        salida = ""
        for line in data.splitlines():
            if line.find(ch) > -1:
                line = line[0:line.find(ch)]
            salida = salida + line + "\n"
        return salida

    def substitute_params(self, data, reg="<.*?>"):
        for match in re.findall(reg, data):
            m = match.replace("<", '"').replace(">", '":')
            data = data.replace(match, self.parameter_value(data, m))
        return data

    def parameter_value(self, data, cad):
        posi = data.find(cad)
        if posi < 0:
            return cad
        else:
            return data[posi + len(cad):data.find("\n", posi)].rstrip(",").strip('"')

    def get(self):
        return self.json
