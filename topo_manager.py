from ryu.topology.switches import *
from ryu.lib.packet import *
from ofctl_utilis import *
from device import MyDevice
import queue

class topo_manager:
    def __init__(self):
        self.graph = {}
        self.vertex = []
        self.hosts = []
        self.switches = []

    def set_forwarding(self, datapath, dl_dst, port):
        ofctl = OfCtl.factory(dp=datapath, logger=None)
        actions = [datapath.ofproto_parser.OFPActionOutput(port)]
        ofctl.set_flow(cookie=0, priority=0,
                       dl_type=ether_types.ETH_TYPE_IP,
                       dl_vlan=VLANID_NONE,
                       dl_dst=dl_dst,
                       actions=actions)

    def del_forwarding(self, datapath):
        ofctl = OfCtl.factory(dp=datapath, logger=None)
        ofctl.delete_flow()

    def build(self, dev1, dev2, port):
        if (dev1 not in self.graph):
            self.graph[dev1] = {}
        self.graph[dev1][dev2] = port

    def dijkstra(self, switch):
        # print(f"dijkstra for {switch.device.dp.id}")
        INF = float('inf')
        dist = {x: INF for x in self.vertex}
        dist[switch] = 0
        next_hop = {}
        vis = self.hosts.copy()
        q = queue.PriorityQueue()
        q.put((dist[switch], switch))
        while (not q.empty()):
            dis, top = q.get()
            # print(f"top {top.device.dp.id}")
            vis.append(top)
            for adj_device, port in self.graph[top].items():
                if adj_device in self.switches and port._state != 1:
                    # print(f"adj_device {adj_device.device.dp.id}")
                    if (dist[adj_device] > dist[top] + 1):
                        dist[adj_device] = dist[top] + 1
                        next_hop[adj_device] = (top, port)
                        q.put((dist[adj_device], adj_device))
        # print(f"current next_hop table: ")
        # for key in next_hop.keys():
        #     print(f"{key.device.dp.id} -> {next_hop[key][0].device.dp.id}, {next_hop[key][1].port_no}")
        return dist, next_hop

    def host_shortest_path(self, host):
        for key in self.graph[host].keys():
            adj_switch1 = key
            host_port1 = self.graph[host][key]
            # print(f"src host {host.device.mac} connect to switch {adj_switch1.device.dp.id}")
        distance, next_hop = self.dijkstra(adj_switch1)
        for dst_host in self.hosts:
            if (dst_host == host):
                continue
            dst_mac = dst_host.device.mac
            for key in self.graph[dst_host].keys():
                adj_switch2 = key
                host_port2 = self.graph[dst_host][key]
                # print(f"dst host {dst_host.device.mac} connect to switch {adj_switch2.device.dp.id}")
            it = adj_switch2
            if (adj_switch1 == adj_switch2):  # connecting to same switch
                self.set_forwarding(adj_switch1.device.dp,
                                    dst_mac, host_port2.port_no)
            while (it != adj_switch1):
                former_switch, port = next_hop[it]
                self.set_forwarding(former_switch.device.dp,
                                    dst_mac, port.port_no)
                # print(f"forwarding: {former_switch.device.dp.id}:{port.port_no} -> {it.device.dp.id}, {dst_mac}")
                it = former_switch

    def update_topology(self):
        # print(f"update_topology() invoked")
        # print(f"deleting current flow tables")
        for switch in self.switches:
            self.del_forwarding(switch.device.dp)
        for host in self.hosts:
            self.host_shortest_path(host)

    def switch_enter(self, switch):
        self.graph[switch] = {}
        self.vertex.append(switch)
        self.switches.append(switch)

    def switch_leave(self, switch):
        if (switch not in self.vertex):
            raise KeyError("Given switch is not in the topo.")
        for key in self.graph.keys():
            if (switch in self.graph[key]):
                del self.graph[key][switch]
        self.vertex.remove(switch)
        self.switches.remove(switch)
        del self.graph[switch]

    def host_add(self, host, switch, port):
        self.graph[host] = {}
        self.vertex.append(host)
        self.hosts.append(host)
        self.build(switch, host, port)
        self.build(host, switch, port)
        self.set_forwarding(switch.device.dp, host.device.mac, port.port_no)

    def link_add(self, dev1, dev2, port1, port2):
        self.build(dev1, dev2, port1)
        self.build(dev2, dev1, port2)

    def link_delete(self, dev1, dev2):
        del self.graph[dev1][dev2]
        del self.graph[dev2][dev1]

    def port_modify(self, port, state):
        for device in self.vertex:
            neighborhood = self.graph[device]
            for adj_device in neighborhood:
                if (adj_device.device.dp.id == port.dpid and neighborhood[adj_device].port_no == port.port_no):
                    neighborhood[adj_device]._state = state
