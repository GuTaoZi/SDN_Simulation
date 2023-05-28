# class NetNode:
#     def __init__(self, device):
#         self.device = device
#         self.adjacent = []
#         self.rtable = {}
#         self.rtable[0] = self

#     def remove(self):
#         self.device = None
#         self.adjacent = None
#         self.rtable = None

#     def has_port(self,port):
#         return any(iport.dpid == port.dpid and iport.port_no == port.port_no for iport in [self.owner.port])

# class HostNode(NetNode):
#     counter = 0

#     def __init__(self, device):
#         super().__init__(device)
#         self.id = HostNode.counter
#         HostNode.counter
    


# class SwitchNode(NetNode):
#     counter = 0

#     def __init__(self, device):
#         super().__init__(device)
#         self.id = SwitchNode.counter
#         SwitchNode.counter += 1


# What to do when removing nodes? 

class Graph:
    def __init__(self):
        self.vertices = {}

    def add_vertex(self, vertex):
        if vertex not in self.vertices:
            self.vertices[vertex] = {}

    def remove_vertex(self, vertex):
        if vertex in self.vertices:
            for neighbor in self.vertices[vertex]:
                del self.vertices[neighbor][vertex]
            del self.vertices[vertex]
            self.vertices.pop(vertex)

    def add_uni_edge(self, vertex1, vertex2, weight=1):
        if vertex1 in self.vertices and vertex2 in self.vertices:
            self.vertices[vertex1][vertex2] = weight

    def add_un_edge(self, vertex1, vertex2, weight=1):
        self.add_uni_edge(vertex1, vertex2, weight)
        self.add_uni_edge(vertex2, vertex1, weight)

    def remove_uni_edge(self, vertex1, vertex2):
        if vertex1 in self.vertices and vertex2 in self.vertices:
            del self.vertices[vertex1][vertex2]

    def remove_un_edge(self, vertex1, vertex2):
        self.remove_uni_edge(vertex1, vertex2)
        self.remove_uni_edge(vertex2, vertex1)

    def floyd(self):
        INF = float('inf')
        n = len(self.vertices)
        dist = [[INF] * n for _ in range(n)]
        next_hop = [[None] * n for _ in range(n)]

        for i, vertex1 in enumerate(self.vertices):
            for j, vertex2 in enumerate(self.vertices):
                if vertex1 == vertex2:
                    dist[i][j] = 0
                    next_hop[i][j] = vertex1
                elif vertex2 in self.vertices[vertex1]:
                    dist[i][j] = self.vertices[vertex1][vertex2]
                    next_hop[i][j] = vertex2

        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if dist[i][k] + dist[k][j] < dist[i][j]:
                        dist[i][j] = dist[i][k] + dist[k][j]
                        next_hop[i][j] = next_hop[i][k]

        return dist, next_hop


if __name__ == '__main__':
    g = Graph()

    g.add_vertex('A')
    g.add_vertex('B')
    g.add_vertex('C')
    g.add_vertex('D')

    g.add_un_edge('A', 'B', 2)
    g.add_un_edge('A', 'C', 5)
    g.add_un_edge('B', 'C', 1)
    g.add_un_edge('B', 'D', 6)
    g.add_un_edge('C', 'D', 3)

    dist, next_hop = g.floyd()

    print(dist)

    print(next_hop)
