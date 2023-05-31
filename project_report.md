$\Huge\textbf{CS305 SDN Simulation}$

$\Huge\text{Project Report}$

In this project, a simple SDN control system is implemented using `Ryu` and `Mininet` in Python.

Project for SUSTech CS305 Computer Network.

## Contributors

| SID      | Name                                              | Contributions | Contribution Rate |
| -------- | ------------------------------------------------- | ------------- | ----------------- |
| 12111624 | [GuTaoZi](https://github.com/GuTaoZi)             |               |                   |
| 12112012 | [Jayfeather233](https://github.com/Jayfeather233) |               |                   |

## Project Structure

- [ ] Update this part after implementation.

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

- [ ] `dhcp.py` implementation
- [ ] `controller.py` implementation

## Task 2: Shortest-Path Switching

- [ ] Graph abstraction
- [ ] `controller.py` implementation
- [ ] Robustness test

## Bonus Tasks

- [ ] Update after implementation


### implement details

#### controller

In controller, we write a class named `topo_manager`, that store the network topo graph. When a node(ether switch or host) add in or remove, we will update the graph and find new shortest path. For `arping`,

#### DHCP

In DHCP, the main function is replying for `DISCOVER` and `REQUEST`. If it is a `DISCOVER`, then find an unused IP address and reply it as a `OFFER`. If it is a `REQUEST`, then claim that IP is used and reply with a `ACK`. Besides the basic function, we add `lease duration` in DHCP's options, this means after a specific time, the IP address will be recycled. After that, the client should send an `REQUEST` to further use this IP. The DHCP Server itself will create an IP pool to know which IP was used so it will not allocate duplicate IP.

### Complex testcase

see `test2.py` & `test_tree.py`