import numpy as np
import matplotlib.pyplot as plt

# %% Input truss structure data
E = 1e4 # elasic modules
p = 0.1 # density
s_lim = 25 # stress limit
d_lim = 2 # displacement limit

nodes = []
bars = []

nodes.append([720,360])
nodes.append([720,0])
nodes.append([360,360])
nodes.append([360,0])
nodes.append([0,360])
nodes.append([0,0])

bars.append([4,2])
bars.append([2,0])
bars.append([5,3])
bars.append([3,1])
bars.append([3,2])
bars.append([1,0])
bars.append([4,3])
bars.append([5,2])
bars.append([2,1])
bars.append([3,0])


nodes = np.array(nodes).astype(float)
bars = np.array(bars)

# Applied forces
P = np.zeros_like(nodes)
P[1, 1] = -100
P[3, 1] = -100

# Support Displacement
Ur = [0, 0, 0, 0]

# Condition of DOF (1 = free, 0 = fixed)
DOFCON = np.ones_like(nodes).astype(int)
DOFCON[4, :] = 0
DOFCON[5, :] = 0

# %% Truss structural analysis
def TrussAnalysis(A):
    NN = len(nodes)
    NE = len(bars)
    DOF = 2
    NDOF = DOF * NN

    # structural analysis
    d = nodes[bars[:, 1], :] - nodes[bars[:, 0], :]
    L = np.sqrt((d ** 2).sum(axis=1))
    angle = d.T / L
    a = np.concatenate((-angle.T, angle.T), axis=1)
    K = np.zeros([NDOF, NDOF])
    for k in range(NE):
        aux = 2 * bars[k, :]
        index = np.r_[aux[0]:aux[0] + 2, aux[1]:aux[1] + 2]

        ES = np.dot(a[k][np.newaxis].T * E * A[k], a[k][np.newaxis]) / L[k]
        K[np.ix_(index, index)] = K[np.ix_(index, index)] + ES

    freeDOF = DOFCON.flatten().nonzero()[0]
    supportDOF = (DOFCON.flatten() == 0).nonzero()[0]
    Kff = K[np.ix_(freeDOF, freeDOF)]
    Pf = P.flatten()[freeDOF]

    Uf = np.linalg.solve(Kff, Pf)
    U = DOFCON.astype(float).flatten()
    U[freeDOF] = Uf
    U[supportDOF] = Ur
    U = U.reshape(NN, DOF)
    u = np.concatenate((U[bars[:, 0]], U[bars[:, 1]]), axis = 1)
    N = E * A[:] / L[:] * (a[:] * u[:]).sum(axis=1)
    S = N/A
    Mass = (p*A*L).sum()
    return S, Mass, U

""" ---------- Partical Swarm Optimization ---------- """

#Parameteer setting
NumMembers = 10 # number of member corss-sections
AMin, AMax = 0.1, 40  # min and max cross-section arrea
changeAMin, changeAMax = -0.2 * (AMax - AMin), 0.2 * (AMax - AMin) # min and max change of cross-section area
MaxIt = 500 # Number of intervals
ps = 30 # size of each interval

c1, c2 = 2, 2 # multiplying constancts
w = 0.9 - ((0.9-0.4)/MaxIt)*np.linspace(0,MaxIt,MaxIt) # mumultiplying constancts

def limitChangeA(ChangeA):
    """
    Keeps the change in area within the limits

    :param ChangeA: The change in area to be checked
    :return: The limited change in area
    """
    for i in range(len(ChangeA)):
        if ChangeA[i] > changeAMax:
            ChangeA[i] = changeAMax
        if ChangeA[i] < changeAMin:
            ChangeA[i] = changeAMin
    return ChangeA

def limitA(A):
    """
    Keeps the cross-section area within the limits

    :param A: The cross-section area to be checked
    :return: The limited cross-section area
    """
    for i in range(len(A)):
        if A[i] > AMax:
            A[i] = AMax
        if A[i] < AMin:
            A[i] = AMin
    return A

def calcCost(weight, deflection, stress):
    """
    Calculates the cost of the truss corss-sections

    :param weight: Total weight of the truss
    :param deflection: deflections of all the nodes of the truss
    :param stress: stresses in all the members of the truss
    :return: cost of the truss
    """

    # adding cost if a member is exceding the stree limit
    C_total = 0
    for cd in range(NumMembers):
        if np.abs(stress[cd]) > s_lim:
            C1 = np.abs((stress[cd] - s_lim) / s_lim)
        else:
            C1 = 0
        C_total = C_total + C1

    # finding the maximum vertical deflection
    maxDif = 0
    for i in range(len(nodes)):
        if np.abs(deflection[i, 1]) > maxDif:
            maxDif = np.abs(deflection[i, 1])

    # calculating cost
    Cs = weight ** 1.8 * 75 + 0.95 * maxDif * 4000000

    return Cs * (1+ C_total)

#%% Algorithm
def Optimization():
    class ParticleSwarmOptimize:
        def __init__(self):
            """
            Initiate Optimizer
            """

            self.Area = np.random.uniform((AMax - AMin) * 0.5, AMax, [ps, NumMembers])
            self.ChangeInArea = np.random.uniform(changeAMin, changeAMax, [ps, NumMembers])

            self.cost = np.zeros(ps)

            self.stress = np.zeros([ps, NumMembers])
            self.weight = np.zeros([ps, NumMembers])
            self.disp = np.zeros([ps,len(nodes),2])

            for i in range(ps):
                self.stress[i], self.weight[i], self.disp[i] = TrussAnalysis(self.Area[i])
                self.cost[i] = calcCost(self.weight[i][0], self.disp[i], self.stress[i])

            self.pBestAreas = np.copy(self.Area)
            self.pBestCost = np.copy(self.cost)

            self.index = np.argmin(self.pBestCost)
            self.gBestAreas = self.pBestAreas[self.index]
            self.gBestCost = self.pBestCost[self.index]

            self.BestAreas = np.zeros([MaxIt, NumMembers])
            self.BestCost = np.zeros(MaxIt)


        def Evaluate(self):
            """
            Optimizes the given truss

            :return:
            """

            for it in range(MaxIt):
                for i in range(ps):

                    # changing cross-section areas
                    self.ChangeInArea[i] = ((w[it] * self.ChangeInArea[i])
                                            + c1 * np.random.rand(NumMembers) * (self.pBestAreas[i] - self.Area[i])
                                            + c2 * np.random.rand(NumMembers) * (self.gBestAreas - self.Area[i]))
                    self.ChangeInArea[i] = limitChangeA(self.ChangeInArea[i])
                    self.Area[i] += self.ChangeInArea[i]
                    self.Area[i] = limitA(self.Area[i])

                    # geting the cost of the truss
                    self.stress[i], self.weight[i], self.disp[i] = TrussAnalysis(self.Area[i])
                    self.cost[i] = calcCost(self.weight[i][0], self.disp[i], self.stress[i])

                    # updating best costs
                    if self.cost[i] < self.pBestCost[i]:
                        self.pBestAreas[i] = self.Area[i]
                        self.pBestCost[i] = self.cost[i]
                        if self.pBestCost[i] < self.gBestCost:
                            self.gBestAreas = self.pBestAreas[i]
                            self.gBestCost = self.pBestCost[i]

                # Saving the best costs and areas for each interval
                self.BestCost[it] = self.gBestCost
                self.BestAreas[it] = self.gBestAreas

        def Plot(self):
            plt.plot(self.BestCost)
            print("Design Variables A[in2]")
            print(self.BestAreas[-1][np.newaxis].T)
            Stress, cost, Disp = TrussAnalysis(self.BestAreas[-1])
            print("stress [ksi]")
            print(Stress[np.newaxis].T)
            print("Displacement [in]")
            print(Disp)
            #plt.ylim([10e-120, 10e20])
            #plt.xlim([0, 3000])
            #plt.ylabel("besy Function Value")
            #plt.xlabel("Number of Iterations")
            #plt.title("ParticleSwarmOptimize Swarm Optimization of sphere Function")
            print("Best Fitness Value =", self.gBestCost)
            plt.show()

    a = ParticleSwarmOptimize()
    a.Evaluate()
    a.Plot()

#%% Run
Optimization()
