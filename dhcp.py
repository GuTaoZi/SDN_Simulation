from ryu.lib import addrconv
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import udp
from ryu.lib.packet import dhcp
from ofctl_utilis import *
import binascii
import ipaddress
import array
from datetime import datetime

# Ref: https://en.wikipedia.org/wiki/Dynamic_Host_Configuration_Protocol


class Config():
    # don't modify, a dummy mac address for fill the mac enrty
    controller_macAddr = '7e:49:b3:f0:f9:99'
    dns = '8.8.8.8'  # don't modify, just for the dns entry
    start_ip = '10.0.0.1'  # can be modified
    end_ip = '10.0.0.3'  # can be modified
    netmask = '255.255.255.0'  # can be modified

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
    
    netmask_bin = addrconv.ipv4.text_to_bin(netmask)
    dns_bin = addrconv.ipv4.text_to_bin(dns)
    
    used = array.array('l', [0]*2049)
    used_time = array.array('L', [0]*65537)
    lease_time = '00000100' # 256s
    lease_time_int = 256
    
    my_ip = None
    my_ip_bin = None
    my_ip_int = None

    mac_ip_dict = {}
    ip_mac_dict = {}

    @classmethod
    def __init__(cls):
        cls.my_ip = cls.get_available_ip()
        print("my_ip", cls.my_ip)
        cls.declare_use_ip(cls.my_ip)
        cls.my_ip_int = ipv4_text_to_int(cls.my_ip)
        cls.my_ip_bin = addrconv.ipv4.text_to_bin(cls.my_ip)

    @classmethod
    def nack_pkt(cls, dhcp_pkt, eth_pkt):
        print("nack_pkt")

        options = [(dhcp.DHCP_MESSAGE_TYPE_OPT, binascii.a2b_hex('06')),  # NAK
                   (dhcp.DHCP_SERVER_IDENTIFIER_OPT, cls.my_ip_bin)]

        pkt = dhcp.dhcp(op=2,
                        htype=1,
                        hlen=6,
                        xid=dhcp_pkt.xid,
                        secs=dhcp_pkt.secs,
                        flags=dhcp_pkt.flags,
                        siaddr=cls.my_ip,
                        chaddr=eth_pkt.src,
                        boot_file=dhcp_pkt.boot_file)
        
        pkt.options = dhcp.options()
        for opts in options:
            pkt.options.options_len += 1
            if isinstance(opts[1], str):
                pkt.options.option_list.append(dhcp.option(opts[0], opts[1].encode()))
            else:
                pkt.options.option_list.append(dhcp.option(opts[0], bytes(opts[1])))
        return pkt

    @classmethod
    def ack_pkt(cls, dhcp_pkt, eth_pkt, new_ip, op):
        print("ack_pkt")
        options = [(dhcp.DHCP_MESSAGE_TYPE_OPT, binascii.a2b_hex(op)),
                   (dhcp.DHCP_SERVER_IDENTIFIER_OPT, cls.my_ip_bin),
                   (dhcp.DHCP_SUBNET_MASK_OPT, cls.netmask_bin),
                   (dhcp.DHCP_GATEWAY_ADDR_OPT, cls.my_ip_bin),
                   (dhcp.DHCP_IP_ADDR_LEASE_TIME_OPT, binascii.a2b_hex(cls.lease_time)),
                   (dhcp.DHCP_SERVER_IDENTIFIER_OPT, cls.my_ip_bin),
                   (dhcp.DHCP_DNS_SERVER_ADDR_OPT, cls.dns_bin)]

        pkt = dhcp.dhcp(op=2,
                        htype=1,
                        hlen=6,
                        xid=dhcp_pkt.xid,
                        secs=dhcp_pkt.secs,
                        flags=dhcp_pkt.flags,
                        ciaddr=dhcp_pkt.ciaddr,
                        yiaddr=new_ip,
                        siaddr=cls.my_ip,
                        giaddr=dhcp_pkt.giaddr,
                        chaddr=eth_pkt.src,
                        boot_file=dhcp_pkt.boot_file)

        pkt.options = dhcp.options()
        for opts in options:
            pkt.options.options_len += 1
            if isinstance(opts[1], str):
                pkt.options.option_list.append(dhcp.option(opts[0], opts[1].encode()))
            else:
                pkt.options.option_list.append(dhcp.option(opts[0], bytes(opts[1])))
        return pkt

    @classmethod
    def assemble_ack(cls, pkt, datapath, port):
        print("ack")
        # TODO: Generate DHCP ACK packet here
        # TODO: Check if the ip addr is avaliable

        eth = pkt.get_protocol(ethernet.ethernet)
        ip = pkt.get_protocol(ipv4.ipv4)
        udp_pkt = pkt.get_protocol(udp.udp)
        dhcp_pkt = pkt.get_protocol(dhcp.dhcp)

        req_ip = "0.0.0.0"

        for opts in dhcp_pkt.options.option_list :
            if opts.tag == dhcp.DHCP_REQUESTED_IP_ADDR_OPT:
                req_ip = str(ipaddress.IPv4Address(opts.value))

        if cls.declare_use_ip(req_ip):
            cls.mac_ip_dict[eth.src] = req_ip
            cls.ip_mac_dict[req_ip] = eth.src
            ack_pkt = cls.ack_pkt(dhcp_pkt, eth, req_ip, '05')
        else:
            ack_pkt = cls.nack_pkt(dhcp_pkt, eth)
        return cls.convert_to_ethernet(ack_pkt, udp_pkt, ip, eth)

    @classmethod
    def assemble_leasetime_ack(cls, pkt, datapath, port):
        print("lease_ack")
        eth = pkt.get_protocol(ethernet.ethernet)
        ip = pkt.get_protocol(ipv4.ipv4)
        udp_pkt = pkt.get_protocol(udp.udp)
        dhcp_pkt = pkt.get_protocol(dhcp.dhcp)
        c_ip = cls.mac_ip_dict.get(eth.src, None)
        if c_ip != None:
            cls.declare_use_ip(c_ip)
            return cls.convert_to_ethernet(cls.ack_pkt(dhcp_pkt, eth, c_ip, '05'), udp_pkt, ip, eth)
        else:
            return cls.convert_to_ethernet(cls.nack_pkt(dhcp_pkt, eth), udp_pkt, ip, eth)

    @classmethod
    def assemble_offer(cls, pkt, datapath):
        print("offer")
        # TODO: Generate DHCP OFFER packet here
        eth = pkt.get_protocol(ethernet.ethernet)
        ip = pkt.get_protocol(ipv4.ipv4)
        udp_pkt = pkt.get_protocol(udp.udp)
        dhcp_pkt = pkt.get_protocol(dhcp.dhcp)

        new_ip = cls.get_available_ip()

        if new_ip == None:
            offer_pkt = cls.nack_pkt(dhcp_pkt, eth)
        else:
            offer_pkt = cls.ack_pkt(dhcp_pkt, eth, new_ip, '02')

        pkt = cls.convert_to_ethernet(offer_pkt, udp_pkt, ip, eth)
        return pkt

    @classmethod
    def handle_dhcp(cls, datapath, port, pkt):
        print("dhcp_handler")
        if cls.my_ip == None:
            cls.__init__()
        # TODO: Specify the type of received DHCP packet
        # You may choose a valid IP from IP pool and genereate DHCP OFFER packet
        # Or generate a DHCP ACK packet
        # Finally send the generated packet to the host by using _send_packet method

        dhcp_pkt = pkt.get_protocol(dhcp.dhcp)
        
        dhcp_pkt : dhcp.dhcp

        is_renew = True
        op = 0
        for opts in dhcp_pkt.options.option_list :
            if opts.tag == dhcp.DHCP_REQUESTED_IP_ADDR_OPT:
                is_renew = False
            if opts.tag == dhcp.DHCP_MESSAGE_TYPE_OPT:
                op = ord(opts.value)

        if op == dhcp.DHCP_DISCOVER:
            print("DISCOVER -> OFFER")
            reply_pkt = cls.assemble_offer(pkt, datapath)
        elif op == dhcp.DHCP_REQUEST:
            print("REQUEST -> ACK")
            if is_renew:
                reply_pkt = cls.assemble_leasetime_ack(pkt, datapath, port)
            else:
                reply_pkt = cls.assemble_ack(pkt, datapath, port)
        else:
            print("Ignore DHCP")
        cls._send_packet(datapath, port, reply_pkt)

    @classmethod
    def _send_packet(cls, datapath, port, pkt):
        print("_send")
        
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        if isinstance(pkt, str):
            pkt = pkt.encode()
        
        pkt : packet.Packet
        
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
        print("get_ava")
        if (cls.start_ip_int & cls.netmask_int) != (cls.end_ip_int & cls.netmask_int):
            return None
        for i in range(cls.start_ip_int, cls.end_ip_int + 1):
            if i == cls.my_ip_int:
                continue
            posa = int((i-cls.start_ip_int) / 32)
            posb = (i-cls.start_ip_int) % 32
            if (not (cls.used[posa] & (1 << posb))) or (datetime.now().timestamp() - cls.used_time[i - cls.start_ip_int] >= cls.lease_time_int):
                return ipv4_int_to_text(i)
        return None

    @classmethod
    def declare_use_ip(cls, ip):
        print("declare")
        ip_int = ipv4_text_to_int(ip)
        if ip_int == cls.my_ip_int:
            return False
        if (cls.start_ip_int & cls.netmask_int) != (ip_int & cls.netmask_int):
            return False
        if cls.start_ip_int > ip_int or ip_int > cls.end_ip_int:
            return False
        posa = int((ip_int-cls.start_ip_int) / 32)
        posb = (ip_int-cls.start_ip_int) % 32
        cls.used[posa] |= 1 << posb
        cls.used_time[ip_int - cls.start_ip_int] = int(datetime.now().timestamp())
        return True

    @classmethod
    def convert_to_ethernet(cls, dhcp_pkt, udp_pkt: udp.udp, ip_pkt: ipv4.ipv4, eth_pkt: ethernet.ethernet):
        print("convert: ", ip_pkt.src)
        
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=eth_pkt.ethertype, dst=eth_pkt.src, src=cls.hardware_addr))
        pkt.add_protocol(ipv4.ipv4(dst=ip_pkt.src, src=cls.my_ip, proto=ip_pkt.proto))
        pkt.add_protocol(udp.udp(src_port=udp_pkt.dst_port,dst_port=udp_pkt.src_port))
        pkt.add_protocol(dhcp_pkt)
        return pkt
