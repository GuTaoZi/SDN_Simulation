from ryu.topology.switches import *
class MyDevice(object):
    def __init__(self, device):
        self.device = device

    def is_host(self):
        return isinstance(self.device, Host)

    def is_switch(self):
        return isinstance(self.device, Switch)

    def __lt__(self, other):
        return False