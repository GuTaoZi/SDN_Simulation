$\Huge\textbf{CS305 SDN Simulation}$

$\Huge\text{Project Report}$

In this project, a simple SDN control system is implemented using `Ryu` and `Mininet` in Python.

Project for SUSTech CS305 Computer Network.

## Contributors

| SID      | Name                                              | Contributions      | Contribution Rate |
| -------- | ------------------------------------------------- | ------------------ | ----------------- |
| 12111624 | [GuTaoZi](https://github.com/GuTaoZi)             | Shortest path etc. | 50%               |
| 12112012 | [Jayfeather233](https://github.com/Jayfeather233) | DHCP etc.          | 50%               |

## Project Structure

```cpp
SDN_Simulation
.
|-- controller.py
|-- device.py
|-- dhcp.py
|-- graph.py
|-- LICENSE
|-- ofctl_utilis.py
|-- project_demo_instructions.md
|-- project_report.md
|-- README.md
|-- README-zh.md
|-- requirements.txt
|-- tests
|   |-- dhcp_test
|   |   |-- test2.py
|   |   `-- test_network.py
|   `-- switching_test
|       |-- test_network.py
|       `-- test_tree.py
`-- topo_manager.py
```

## Task 1: DHCP

In DHCP, the main function is replying for `DISCOVER` and `REQUEST`. If it is a `DISCOVER`, then find an unused IP address and reply it as a `OFFER`. If it is a `REQUEST`, then claim that IP is used and reply with a `ACK`. Besides the basic function, we add `lease duration` in DHCP's options, this means after a specific time, the IP address will be recycled. After that, the client should send an `REQUEST` to further use this IP. The DHCP Server itself will create an IP pool to know which IP was used so it will not allocate duplicate IP.

## Task 2: Shortest-Path Switching

### Graph abstraction

We use 2 classes to abstract the graph: `MyDevice` class as the vertex class for the graph, and `topo_manager` as the graph class with event handler functions and route scheduling function.

`MyDevice` class is very simple, just pack up two types of devices in the graph.

```python
class MyDevice(object):
    def __init__(self, device):
        self.device = device
    def is_host(self):
        return isinstance(self.device, Host)
    def is_switch(self):
        return isinstance(self.device, Switch)
    def __lt__(self, other):
        return False
```

### Event handling

In `topo_manager`, there are some event handler functions:

```python
def switch_enter(self, switch)
def switch_leave(self, switch)
def host_add(self, host, switch, port)
def link_add(self, dev1, dev2, port1, port2)
def link_delete(self, dev1, dev2)
def port_modify(self, port, state)
```

The ways to handle these events are:

- switch entering: simply wrap up the switch as device node, add this node to the graph
- switch leave: remove the vertex in the graph with the same datapath id as the given switch, update topology flow table
- host add: put the information of the new host into ARP table, update topology glow table
- link add: add undirected edges(weight default set as 1) to the graph, update topology flow table
- link delete: delete undirected edges according to given datapath id, update topology flow table

### Dijkstra

We implement Dijkstra as the route scheduling algorithm, the pseudocode is shown as follows:

```pseudocode
function Dijkstra(graph, source):
    Initialize distances: dist[node] = infinity for all nodes in graph
    Set distance from source to itself: dist[source] = 0
    Initialize an empty priority queue: pq
    
    Enqueue source with distance 0 into pq
    
    while pq is not empty:
        Dequeue a node, current, from pq
        
        if current has been visited:
            Continue to the next iteration
        
        Mark current as visited
        
        for each neighbor in graph[current]:
            Calculate new distance: new_dist = dist[current] + weight(current, neighbor)
            
            if new_dist < dist[neighbor]:
                Update dist[neighbor] to new_dist
                
                next hop of neighbor <- current
                
                Enqueue neighbor with distance new_dist into pq
    
    Return dist
```

We output the next hop map after each round of Dijkstra by default, for the sake of checking the shortest route.

## Testcases

### Tree topology

In this test case, the topology structure is in a shape of binary tree, with 7 switches and 8 hosts.

The flow table is:

![](https://github.com/GuTaoZi/SDN_Simulation/raw/main/tests/switching_test/test_tree.png)

And the `pingall` output is:

<img src="https://s2.loli.net/2023/06/01/zvYt84oPilJNyrp.png" alt="image.png" style="zoom:50%;" />

### Robust topology

In this test case, the topology structure is more complex, shown as follows:

The flow table is:

![](https://github.com/GuTaoZi/SDN_Simulation/raw/main/tests/switching_test/test_robo.png)

And the `pingall` output is:

<img src="https://s2.loli.net/2023/06/01/9P7NViqn5gw3pyU.png" alt="image.png" style="zoom:50%;" />

## Bonus Tasks

#### DHCP



### Complex testcase

see `test2.py` & `test_tree.py`