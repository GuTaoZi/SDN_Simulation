from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo


def disable_ipv6(node):
    node.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
    node.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
    node.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")


def ping(host, dst, count=1, timeout=1):
    return host.cmd('ping -c %s -W %s %s' % (count, timeout, dst))


def send_arp(node, count=1):
    node.cmd('arping -c %s -A -I %s-eth0 %s' % (count, node.name, node.IP()))
    print(f"arped node")


def send_dhcp(node):
    print('Sending DHCP request dhclient -v %s-eth0 ' % (node.name))
    node.cmd('dhclient -v %s-eth0' % (node.name))


def do_arp_all(net):
    for h in net.hosts:
        send_arp(h)


class TriangleTopo(Topo):
    def __init__(self, **opts):
        Topo.__init__(self, **opts)
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')
        h6 = self.addHost('h6')
        h7 = self.addHost('h7')
        h8 = self.addHost('h8')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')
        s6 = self.addSwitch('s6')
        s7 = self.addSwitch('s7')
        self.addLink(s1, s2)
        self.addLink(s1, s5)
        self.addLink(s2, s3)
        self.addLink(s2, s4)
        self.addLink(s5, s6)
        self.addLink(s5, s7)

        self.addLink(s3, h1)
        self.addLink(s3, h2)
        self.addLink(s4, h3)
        self.addLink(s4, h4)
        self.addLink(s6, h5)
        self.addLink(s6, h6)
        self.addLink(s7, h7)
        self.addLink(s7, h8)


def run_mininet():
    import time
    topo = TriangleTopo()
    net = Mininet(topo=topo, autoSetMacs=True, controller=RemoteController)
    for h in net.hosts:
        disable_ipv6(h)
    for h in net.switches:
        disable_ipv6(h)

    net.start()
    time.sleep(1)
    print(f"Now do arp all")
    do_arp_all(net)
    CLI(net)

    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run_mininet()
