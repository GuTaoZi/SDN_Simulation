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

from device import MyDevice
from topo_manager import topo_manager
from ofctl_utilis import *


class ControllerApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ControllerApp, self).__init__(*args, **kwargs)
        self.topo = topo_manager()
        self.arp_table = {}

    @set_ev_cls(event.EventSwitchEnter)
    def handle_switch_add(self, ev: event.EventSwitchEnter):
        """
        Event handler indicating a switch has come online.
        """
        new_switch = MyDevice(ev.switch)
        print(f"adding switch {ev.switch.dp.id}")
        self.topo.switch_enter(new_switch)

    @set_ev_cls(event.EventSwitchLeave)
    def handle_switch_delete(self, ev: event.EventSwitchLeave):
        """
        Event handler indicating a switch has been removed
        """
        print(f"deleting switch {ev.switch.dp.id}")
        for switch in self.topo.switches:
            if (switch.device.dp.id == ev.switch.dp.id):
                self.topo.switch_leave(switch)
                break

    @set_ev_cls(event.EventHostAdd)
    def handle_host_add(self, ev: event.EventHostAdd):
        """
        Event handler indiciating a host has joined the network
        This handler is automatically triggered when a host sends an ARP response.
        """
        # TODO:  Update network topology and flow rules
        print(f"adding host {ev.host.mac}")
        new_host = MyDevice(ev.host)
        port = ev.host.port
        self.arp_table[ev.host.ipv4[0]]=ev.host.mac
        for switch in self.topo.switches:
            if (switch.device.dp.id == port.dpid):
                self.topo.host_add(new_host, switch, port)
                break
        self.topo.update_topology()

    @set_ev_cls(event.EventLinkAdd)
    def handle_link_add(self, ev: event.EventLinkAdd):
        """
        Event handler indicating a link between two switches has been added
        """
        # TODO:  Update network topology and flow rules
        print(f"adding link {ev.link.src.dpid}->{ev.link.dst.dpid}")
        for switch in self.topo.switches:
            if (switch.device.dp.id == ev.link.src.dpid):
                src_switch = switch
            if (switch.device.dp.id == ev.link.dst.dpid):
                dst_switch = switch
        self.topo.link_add(src_switch, dst_switch, ev.link.src, ev.link.dst)
        self.topo.update_topology()

    @set_ev_cls(event.EventLinkDelete)
    def handle_link_delete(self, ev):
        """
        Event handler indicating when a link between two switches has been deleted
        """
        # TODO:  Update network topology and flow rules
        print(f"deleting link {ev.link.src.dipid}->{ev.link.dst.dpid}")
        for switch in self.topo.switches:
            if (switch.device.dp.id == ev.link.src.dpid):
                src_switch = switch
            if (switch.device.dp.id == ev.link.dst.dpid):
                dst_switch = switch
        self.topo.link_delete(src_switch, dst_switch, ev.link.src, ev.link.dst)
        self.topo.update_topology()

    @set_ev_cls(event.EventPortModify)
    def handle_port_modify(self, ev: event.EventPortModify):
        """
        Event handler for when any switch port changes state.
        This includes links for hosts as well as links between switches.
        """
        # TODO:  Update network topology and flow rules
        print(f"modifying port {ev.port.dpid} {ev.port.port_no}")
        for switch in self.topo.switches:
            if (switch.device.dp.id == ev.port.port_dpid):
                break
        self.topo.port_modify(ev.port, ev.port._state)
        self.topo.update_topology()

    def handle_arp(self, datapath, msg, arp_pkt):
        for key in self.arp_table.keys():
            print(key,self.arp_table[key])
        ofctl = OfCtl_v1_0(datapath, logger=None)
        print(f"reply: IP\tMAC")
        print(f"{arp_pkt.dst_ip}\t{self.arp_table[arp_pkt.dst_ip]}")
        print(f"{arp_pkt.dst_ip}\t{arp_pkt.src_mac}")
        ofctl.send_arp(arp_opcode=arp.ARP_REPLY,
                       vlan_id=VLANID_NONE,
                       dst_mac=arp_pkt.src_mac,
                       sender_mac=self.arp_table[arp_pkt.dst_ip],
                       sender_ip=arp_pkt.dst_ip,
                       target_ip=arp_pkt.src_ip,
                       target_mac=arp_pkt.src_mac,
                       src_port=ofproto_v1_0.OFPP_CONTROLLER,
                       output_port=msg.in_port)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        try:
            msg = ev.msg
            datapath = msg.datapath
            pkt = packet.Packet(data=msg.data)
            inPort = msg.in_port
            if pkt.get_protocols(dhcp.dhcp):
                print(f"+++ DHCP packet received")
                DHCPServer.handle_dhcp(datapath, inPort, pkt)
            elif pkt.get_protocols(arp.arp):
                print(f"+++ ARP packet received")
                arp_pkt = pkt.get_protocol(arp.arp)
                if arp_pkt.opcode == arp.ARP_REQUEST:
                    print(f"request: IP\tMAC")
                    print(f"{arp_pkt.src_ip}\t{arp_pkt.src_mac}")
                    print(f"{arp_pkt.dst_ip}\t{arp_pkt.dst_mac}")
                    self.arp_table[arp_pkt.src_ip]=arp_pkt.src_mac
                    self.handle_arp(datapath=datapath,msg=msg,arp_pkt=arp_pkt)
            return
        except Exception as e:
            self.logger.error(e)
