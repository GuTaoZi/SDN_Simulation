from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology import event, switches
from ryu.ofproto import ofproto_v1_0
from ryu.lib.packet import packet, ethernet, ether_types, arp
from ryu.lib.packet import dhcp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import packet
from ryu.lib.packet import udp
from dhcp import DHCPServer

class ControllerApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ControllerApp, self).__init__(*args, **kwargs)

    @set_ev_cls(event.EventSwitchEnter)
    def handle_switch_add(self, ev):
        """
        Event handler indicating a switch has come online.
        """
        switch_dp = ev.switch.dp
        ofproto = switch_dp.ofproto
        parser = switch_dp.ofproto_parser
        print(f"Switch {switch_dp.id} connected")

        match = parser.OFPMatch()

        # Define actions to be taken by the flow entry
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]

        # Install the flow entry on the switch
        self.add_flow(switch_dp, 1, match, actions)

    @set_ev_cls(event.EventSwitchLeave)
    def handle_switch_delete(self, ev):
        """
        Event handler indicating a switch has been removed
        """
        switch_dp = ev.switch.dp
        ofproto = switch_dp.ofproto
        parser = switch_dp.ofproto_parser

        # Define match criteria for the flow entry
        match = parser.OFPMatch()

        # Define an instruction to delete all flow entries on the switch
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_CLEAR_ACTIONS, [])]

        # Create a flow modification message to delete the flow entries
        mod = parser.OFPFlowMod(datapath=switch_dp, command=ofproto.OFPFC_DELETE, match=match, instructions=inst)

        # Send the flow modification message to the switch to delete the flow entries
        switch_dp.send_msg(mod)
        
    def add_flow(self, datapath, priority, match, actions):
        """
        Install a flow entry on a switch
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
        datapath.send_msg(mod)


    @set_ev_cls(event.EventHostAdd)
    def handle_host_add(self, ev):
        """
        Event handler indiciating a host has joined the network
        This handler is automatically triggered when a host sends an ARP response.
        """ 
        # TODO:  Update network topology and flow rules
        # Get switch and port information for the host
        host_port = ev.port
        host_switch = host_port.dpid
        parser = host_port.datapath.ofproto_parser

        # Define match criteria for the flow entry
        match = parser.OFPMatch()

        # Define actions to be taken by the flow entry
        actions = [parser.OFPActionOutput(port=host_port.port_no)]

        # Install the flow entry on the switch
        self.add_flow(self.datapaths[host_switch], 1, match, actions)

    @set_ev_cls(event.EventLinkAdd)
    def handle_link_add(self, ev):
        """
        Event handler indicating a link between two switches has been added
        """
        # TODO:  Update network topology and flow rules
        # Get switch and port information for the link
        link_src = ev.link.src
        link_dst = ev.link.dst
        parser = ev.msg.datapath.ofproto_parser

        # Define match criteria for the flow entry
        match = parser.OFPMatch(in_port=link_src.port_no)

        # Define actions to be taken by the flow entry
        actions = [parser.OFPActionOutput(port=link_dst.port_no)]

        # Install the flow entry on the source switch
        self.add_flow(self.datapaths[link_src.dpid], 1, match, actions)

    @set_ev_cls(event.EventLinkDelete)
    def handle_link_delete(self, ev):
        """
        Event handler indicating when a link between two switches has been deleted
        """
        # TODO:  Update network topology and flow rules
   
        link_src = ev.link.src
        link_dst = ev.link.dst

        # Remove the link from the network topology
        self.topology.remove_link(link_src.dpid, link_src.port_no, link_dst.dpid, link_dst.port_no)

        # Remove any flow entries that use this link
        self.remove_link_flows(link_src.dpid, link_dst.dpid)
        

    @set_ev_cls(event.EventPortModify)
    def handle_port_modify(self, ev):
        """
        Event handler for when any switch port changes state.
        This includes links for hosts as well as links between switches.
        """
        # TODO:  Update network topology and flow rules
        port = ev.port
        switch_dp = self.topology.get_switch(port.dpid).dp
        ofproto = switch_dp.ofproto
        parser = switch_dp.ofproto_parser

        # Update the status of the port in the network topology
        if port.state == 1:
            self.topology.set_port_status(port.dpid, port.port_no, "UP")
        else:
            self.topology.set_port_status(port.dpid, port.port_no, "DOWN")

        # Remove any flow entries that use this port
        self.remove_port_flows(port.dpid, port.port_no)

        # If the port is a link to another switch, add a flow entry to forward traffic to that switch
        if self.topology.is_link_port(port.dpid, port.port_no):
            link = self.topology.get_link_by_port(port.dpid, port.port_no)
            dst_dpid = link.dst.dpid
            dst_port = link.dst.port_no

            # Define match criteria for the flow entry
            match = parser.OFPMatch()

            # Define an action to forward packets to the destination switch
            out_port = ofproto.OFPP_LOCAL if dst_dpid == switch_dp.id else dst_port
            actions = [parser.OFPActionOutput(out_port)]

            # Install the flow entry on the switch
            self.add_flow(switch_dp, 1, match, actions)


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
                pkt_arp = pkt.get_protocols(arp.arp)
                # ARPServer.handle_arp(datapath, inPort, pkt)
                pass
            else:
                DHCPServer.handle_dhcp(datapath, inPort, pkt)      
            return 
        except Exception as e:
            self.logger.error(e)
    
