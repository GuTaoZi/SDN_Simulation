from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology import event
from ryu.topology.switches import *
from ryu.ofproto import ofproto_v1_0
from ryu.lib.packet import packet, ethernet, ether_types, arp
from ryu.lib.packet import dhcp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import packet
from ryu.lib.packet import udp
from dhcp import DHCPServer

from graph import *

class ControllerApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ControllerApp, self).__init__(*args, **kwargs)
        self.graph = Graph()    # Graph

    @set_ev_cls(event.EventSwitchEnter)
    def handle_switch_add(self, ev: event.EventSwitchEnter):
        """
        Event handler indicating a switch has come online.
        """
        new_switch: Switch = ev.switch
        dpid = new_switch.dp.id
        self.topo._register(new_switch.dp)
        

    @set_ev_cls(event.EventSwitchLeave)
    def handle_switch_delete(self, ev:event.EventSwitchLeave):
        """
        Event handler indicating a switch has been removed
        """
        del_switch = ev.switch
        dpid = del_switch.dp.id


    @set_ev_cls(event.EventHostAdd)
    def handle_host_add(self, ev: event.EventHostAdd):
        """
        Event handler indiciating a host has joined the network
        This handler is automatically triggered when a host sends an ARP response.
        """ 
        # TODO:  Update network topology and flow rules
        new_host = ev.host
        port = new_host.port
        mac = new_host.mac
        

    @set_ev_cls(event.EventLinkAdd)
    def handle_link_add(self, ev):
        """
        Event handler indicating a link between two switches has been added
        """
        # TODO:  Update network topology and flow rules

    @set_ev_cls(event.EventLinkDelete)
    def handle_link_delete(self, ev):
        """
        Event handler indicating when a link between two switches has been deleted
        """
        # TODO:  Update network topology and flow rules
   
        

    @set_ev_cls(event.EventPortModify)
    def handle_port_modify(self, ev):
        """
        Event handler for when any switch port changes state.
        This includes links for hosts as well as links between switches.
        """
        # TODO:  Update network topology and flow rules



    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        try:
            msg = ev.msg
            datapath = msg.datapath
            pkt = packet.Packet(data=msg.data)
            pkt_dhcp = pkt.get_protocols(dhcp.dhcp)
            inPort = msg.in_port
            if not pkt_dhcp:
                # TODO: handle other protocols like ARP 
                pass
            else:
                DHCPServer.handle_dhcp(datapath, inPort, pkt)      
            return 
        except Exception as e:
            self.logger.error(e)
    