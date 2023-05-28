from ryu.lib import addrconv
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import udp
from ryu.lib.packet import dhcp
from ofctl_utilis import *
import array


class Config():
    controller_macAddr = '7e:49:b3:f0:f9:99' # don't modify, a dummy mac address for fill the mac enrty
    dns = '8.8.8.8' # don't modify, just for the dns entry
    start_ip = '192.168.1.2' # can be modified
    end_ip = '192.168.1.100' # can be modified
    netmask = '255.255.255.0' # can be modified

    # You may use above attributes to configure your DHCP server.
    # You can also add more attributes like "lease_time" to support bouns function.


class DHCPServer():
    hardware_addr = Config.controller_macAddr
    start_ip = Config.start_ip
    end_ip = Config.end_ip
    netmask = Config.netmask
    dns = Config.dns
    
    start_ip_int = ipv4_text_to_int(start_ip)
    end_ip_int = ipv4_text_to_int(end_ip)
    netmask_int = ipv4_text_to_int(netmask)
    used = array.array('l', [0]*524289)

    @classmethod
    def assemble_ack(cls, pkt, datapath, port):
        # TODO: Generate DHCP ACK packet here
        
        eth = pkt.get_protocol(ethernet.ethernet)
        ip = pkt.get_protocol(ipv4.ipv4)
        dhcp_pkt = pkt.get_protocol(dhcp.dhcp)

        options = [(dhcp.DHCP_MESSAGE_TYPE_OPT, dhcp.DHCP_ACK),
                   (dhcp.DHCP_SERVER_IDENTIFIER_OPT, cls.hardware_addr),
                   (dhcp.DHCP_SUBNET_MASK_OPT, cls.netmask),
                   (dhcp.DHCP_DNS_SERVER_ADDR_OPT, cls.dns)]

        ack_pkt = dhcp.dhcp(bootp_op=2,
                            bootp_htype=1,
                            bootp_hlen=6,
                            bootp_xid=dhcp_pkt.xid,
                            bootp_secs=dhcp_pkt.secs,
                            bootp_flags=dhcp_pkt.flags,
                            bootp_ciaddr=ip.src,
                            bootp_yiaddr=dhcp_pkt.yiaddr,
                            bootp_siaddr=cls.hardware_addr,
                            bootp_giaddr=dhcp_pkt.giaddr,
                            chaddr=eth.src,
                            options=options)

        return ack_pkt


    @classmethod
    def assemble_offer(cls, pkt, datapath):
        # TODO: Generate DHCP OFFER packet here
        eth = pkt.get_protocol(ethernet.ethernet)
        ip = pkt.get_protocol(ipv4.ipv4)
        dhcp_pkt = pkt.get_protocol(dhcp.dhcp)

        
        new_ip = cls.get_available_ip()
        
        if new_ip == None:
            options = [(dhcp.DHCP_MESSAGE_TYPE_OPT, 4),
           (dhcp.DHCP_SERVER_IDENTIFIER_OPT, cls.hardware_addr)]

            offer_pkt = dhcp.dhcp(bootp_op=2,
                bootp_htype=1,
                bootp_hlen=6,
                bootp_xid=dhcp_pkt.xid,
                bootp_secs=dhcp_pkt.secs,
                bootp_flags=dhcp_pkt.flags,
                bootp_ciaddr=ip.src,
                chaddr=eth.src,
                options=options)
        else:
            
            options = [(dhcp.DHCP_MESSAGE_TYPE_OPT, dhcp.DHCP_OFFER),
                    (dhcp.DHCP_SERVER_IDENTIFIER_OPT, cls.hardware_addr),
                    (dhcp.DHCP_SUBNET_MASK_OPT, cls.netmask),
                    (dhcp.DHCP_DNS_SERVER_ADDR_OPT, cls.dns)]

            offer_pkt = dhcp.dhcp(bootp_op=2,
                                bootp_htype=1,
                                bootp_hlen=6,
                                bootp_xid=dhcp_pkt.xid,
                                bootp_secs=dhcp_pkt.secs,
                                bootp_flags=dhcp_pkt.flags,
                                bootp_ciaddr=0,
                                bootp_yiaddr=new_ip,
                                bootp_siaddr=cls.hardware_addr,
                                bootp_giaddr=dhcp_pkt.giaddr,
                                chaddr=eth.src,
                                options=options)

        return offer_pkt



    @classmethod
    def handle_dhcp(cls, datapath, port, pkt):
        # TODO: Specify the type of received DHCP packet
        # You may choose a valid IP from IP pool and genereate DHCP OFFER packet
        # Or generate a DHCP ACK packet
        # Finally send the generated packet to the host by using _send_packet method

        dhcp_pkt = pkt.get_protocol(dhcp.dhcp)
        if dhcp_pkt.op == dhcp.DHCP_DISCOVER:
            offer_pkt = cls.assemble_offer(pkt, datapath)
            cls._send_packet(datapath, port, offer_pkt)
        elif dhcp_pkt.op == dhcp.DHCP_REQUEST:
            ack_pkt = cls.assemble_ack(pkt, datapath, port)
            cls._send_packet(datapath, port, ack_pkt)


    @classmethod
    def _send_packet(cls, datapath, port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        if isinstance(pkt, str):
            pkt = pkt.encode()
        pkt.serialize()
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)
    
    @classmethod
    def get_available_ip(cls):
        # TODO: Implement a method to get an available IP
        if (cls.start_ip_int&cls.netmask_int) != (cls.end_ip_int&cls.netmask_int):
            return None
        for i in range(cls.start_ip_int, cls.end_ip_int + 1):
            posa = int((i-cls.start_ip_int) / 32)
            posb = (i-cls.start_ip_int) % 32
            if not(cls.used[posa] & (1<<posb)):
                cls.used[posa] |= 1<<posb
                return ipv4_int_to_text(i)
        return None