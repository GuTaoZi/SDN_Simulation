from ryu.topology.switches import *
from ryu.ofproto import ofproto_v1_0
from ryu.ofproto import ofproto_v1_0_parser
from ryu.lib.packet import *


class MyDevice:
    def __init__(self, device):
        self.device = device
        self.adjacent = []
        self.rtable = {self: (0, self)}

    def is_host(self):
        return isinstance(self.device, Host)

    def is_switch(self):
        return isinstance(self.device, Switch)
    
    def distance_vector_update(self,):

    
    def add_adjacent(self,adjacent_device,port):
        self.adjacent.append((adjacent_device,port))

    def remove(self):
        if (self.is_switch):
            datapath = self.device.dp
            OpenflowProto = datapath.ofproto
            OpenflowParser = datapath.ofproto_parser
            for to_device in self.rtable.keys():
                if (to_device.is_host()):
                    match = OpenflowParser.OFPMATCH(
                        dl_dst=to_device.device.mac)
            req = OpenflowParser.OFPFlowMod(datapath=datapath, command=OpenflowProto.OFPFC_DELETE,
                                            buffer_id=0xffffffff, out_port=OpenflowProto.OFPP_NONE, match=match)
            datapath.send_msg(req)
        self.device = None
        self.adjacent = None
        self.rtable = None

    def port_to(self, to_device):
        port_list = [port for device,
                     port in self.adjacent if device == to_device]
        return None if port_list == [] else port_list[0]

    def has_port(self, port):
        if (self.is_host):
            return any(iport for iport in [self.device.port] if iport.dpid == port.dpid and iport.port_no == port.port_no)
        if (self.is_switch):
            return any(iport for iport in self.device.ports if iport.dpid == port.dpid and iport.port_no == port.port_no)

    def switch_commit(self):
        if(not self.is_switch):
            print("switch_commit() should only be invoked by switch device!")
            return
        datapath = self.owner.dp
        OpenflowProto = datapath.ofproto
        OpenflowParser = datapath.ofproto_parser

        actions = [OpenflowParser.OFPActionOutput(
            OpenflowProto.OFPP_CONTROLLER)]
        match = OpenflowParser.OFPMatch()
        req = OpenflowParser.OFPFlowMod(datapath=datapath, command=OpenflowProto.OFPFC_ADD, buffer_id=0xffffffff,
                                        priority=1000, flags=0, match=match, out_port=0, actions=actions)
        datapath.send_msg(req)

        for to_device in self.router_table.keys():
            if to_device.is_host():
                next_skip = self.router_table[to_device][1]
                next_skip_port = self.get_port(
                    next_skip).port_no
                actions = [OpenflowParser.OFPActionOutput(
                    next_skip_port), OpenflowParser.OFPActionOutput(OpenflowProto.OFPP_CONTROLLER)]
                match = OpenflowParser.OFPMatch(dl_dst=to_device.mac)

                req = OpenflowParser.OFPFlowMod(datapath=datapath, command=OpenflowProto.OFPFC_ADD, buffer_id=0xffffffff,
                                                priority=2333, flags=0, match=match, out_port=next_skip_port, actions=actions)
                datapath.send_msg(req)
