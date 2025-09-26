import numpy as np

class Truss:
    def __init__(self):
        self.n = []
        self.m = []
        self.membersCrossSectionGroup = []
        self.E = 1e4  # elasic modules
        self.p = 0.1  # density

        self.PointForces = []
        self.Suports = []

        self.nodes = None
        self.bars = None
        self.P = None
        self.DOFCON = None

    def addPointForce(self, Node, Direction, Magnitude):
        """
        Adds a point load to a node

        :param Node: Number of node starting at 0
        :param Direction: (0=x,1=y)
        :param Magnitude: Magnitude of the load
        """
        self.PointForces.append([Node, Direction, Magnitude])

    def addSuport(self, Node, Type):
        """
        Adds a support to a node
        :param Node:  Number of node starting at 0
        :param Type: (0 = pined, 1 = free)
        """
        if Type == 0:
            self.Suports.append([Node, 0,0])
        elif Type == 1:
            self.Suports.append([Node, 1,1])


    def addMember(self, Nodes, corssSectionGroup):
        """
        Adds a members
        :param Nodes: [nodes 1, Node 2] sNumber of node starting at 0
        :param corssSectionGroup: starting at zero number of cress section group
        """
        self.m.append(Nodes)
        self.membersCrossSectionGroup.append(corssSectionGroup)

    def addNode(self, cords):
        """
        Adds a node
        :param cords: [x,y]
        """
        self.n.append(cords)

    def startAnalysis(self):
        self.nodes = np.array(self.n).astype(float)
        self.bars = np.array(self.m)

        # Applied forces
        self.P = np.zeros_like(self.nodes)
        for i in range(len(self.PointForces)):
            self.P[self.PointForces[i][0], self.PointForces[i][1]] = self.PointForces[i][2]

        # Condition of DOF (1 = free, 0 = fixed)
        self.DOFCON = np.ones_like(self.nodes).astype(int)

        for i in range(len(self.Suports)):
            self.DOFCON[self.Suports[i][0], 0] = self.Suports[i][1]
            self.DOFCON[self.Suports[i][0], 1] = self.Suports[i][2]

    def Analysis(self, A):
        NN = len(self.nodes)
        NE = len(self.bars)
        DOF = 2
        NDOF = DOF * NN

        # structural analysis
        d = self.nodes[self.bars[:, 1], :] - self.nodes[self.bars[:, 0], :]
        L = np.sqrt((d ** 2).sum(axis=1))
        angle = d.T / L
        a = np.concatenate((-angle.T, angle.T), axis=1)
        K = np.zeros([NDOF, NDOF])
        for k in range(NE):
            aux = 2 * self.bars[k, :]
            index = np.r_[aux[0]:aux[0] + 2, aux[1]:aux[1] + 2]

            ES = np.dot(a[k][np.newaxis].T * self.E * A[k], a[k][np.newaxis]) / L[k]
            K[np.ix_(index, index)] = K[np.ix_(index, index)] + ES

        freeDOF = self.DOFCON.flatten().nonzero()[0]
        supportDOF = (self.DOFCON.flatten() == 0).nonzero()[0]
        Kff = K[np.ix_(freeDOF, freeDOF)]
        Pf = self.P.flatten()[freeDOF]

        Uf = np.linalg.solve(Kff, Pf)
        U = self.DOFCON.astype(float).flatten()
        U[freeDOF] = Uf
        U[supportDOF] = [0,0,0,0]
        U = U.reshape(NN, DOF)
        u = np.concatenate((U[self.bars[:, 0]], U[self.bars[:, 1]]), axis=1)
        N = self.E * A[:] / L[:] * (a[:] * u[:]).sum(axis=1)
        S = N / A
        Mass = (self.p * A * L).sum()
        return S, Mass, U