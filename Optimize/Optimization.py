import numpy as np
import matplotlib.pyplot as plt
import TrussAnalysis

class ParticalSwarmOptimization:

    def __init__(self, NumMembers, NumNodes, NumCrossSections, AMin, AMax, MaxItervals, PopSize, stressLimit, Truss):
        self.Truss = Truss

        self.NumMembers = NumMembers  # number of member corss-sections
        self.NumNodes = NumNodes

        self.NumCrossSections = NumCrossSections
        self.AMin, self.AMax = AMin, AMax  # min and max cross-section arrea
        self.changeAMin, self.changeAMax = -0.2 * (AMax - AMin), 0.2 * (AMax - AMin)  # min and max change of cross-section area
        self.MaxIt = MaxItervals  # Number of intervals
        self.ps = PopSize  # size of each interval

        self.StressLimit = stressLimit

        self.c1, self.c2 = 2, 2  # multiplying constancts
        self.w = 0.9 - ((0.9 - 0.4) / self.MaxIt) * np.linspace(0, self.MaxIt, self.MaxIt)  # mumultiplying constancts

        # Initilizing all varables
        self.Area = np.random.uniform((self.AMax - self.AMin) * 0.5, self.AMax, [self.ps, self.NumMembers])
        self.ChangeInArea = np.random.uniform(self.changeAMin, self.changeAMax, [self.ps, self.NumMembers])

        self.cost = np.zeros(self.ps)

        self.stress = np.zeros([self.ps, self.NumMembers])
        self.weight = np.zeros([self.ps, self.NumMembers])
        self.disp = np.zeros([self.ps, self.NumNodes, 2])

        for i in range(self.ps):
            self.stress[i], self.weight[i], self.disp[i] = self.Truss.Analysis(self.Area[i])
            self.cost[i] = self.calcCost(self.weight[i][0], self.disp[i], self.stress[i])

        self.pBestAreas = np.copy(self.Area)
        self.pBestCost = np.copy(self.cost)

        self.index = np.argmin(self.pBestCost)
        self.gBestAreas = self.pBestAreas[self.index]
        self.gBestCost = self.pBestCost[self.index]

        self.BestAreas = np.zeros([self.MaxIt, self.NumMembers])
        self.BestCost = np.zeros(self.MaxIt)

    def Evaluate(self):
        """
        Optimizes the given truss

        :return:
        """

        for it in range(self.MaxIt):
            for i in range(self.ps):

                # changing cross-section areas
                self.ChangeInArea[i] = ((self.w[it] * self.ChangeInArea[i])
                                        + self.c1 * np.random.rand(self.NumMembers) * (self.pBestAreas[i] - self.Area[i])
                                        + self.c2 * np.random.rand(self.NumMembers) * (self.gBestAreas - self.Area[i]))
                self.ChangeInArea[i] = self.limitChangeA(self.ChangeInArea[i])
                self.Area[i] += self.ChangeInArea[i]
                self.Area[i] = self.limitA(self.Area[i])

                # geting the cost of the truss
                self.stress[i], self.weight[i], self.disp[i] = self.Truss.Analysis(self.Area[i])
                self.cost[i] = self.calcCost(self.weight[i][0], self.disp[i], self.stress[i])

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
        Stress, cost, Disp = self.Truss.Analysis(self.BestAreas[-1])
        print("stress [ksi]")
        print(Stress[np.newaxis].T)
        print("Displacement [in]")
        print(Disp)
        # plt.ylim([10e-120, 10e20])
        # plt.xlim([0, 3000])
        # plt.ylabel("besy Function Value")
        # plt.xlabel("Number of Iterations")
        # plt.title("ParticleSwarmOptimize Swarm Optimization of sphere Function")
        print("Best Fitness Value =", self.gBestCost)
        plt.show()

    def limitChangeA(self, ChangeA):
        """
        Keeps the change in area within the limits

        :param ChangeA: The change in area to be checked
        :return: The limited change in area
        """
        for i in range(len(ChangeA)):
            if ChangeA[i] > self.changeAMax:
                ChangeA[i] = self.changeAMax
            if ChangeA[i] < self.changeAMin:
                ChangeA[i] = self.changeAMin
        return ChangeA

    def limitA(self, A):
        """
        Keeps the cross-section area within the limits

        :param A: The cross-section area to be checked
        :return: The limited cross-section area
        """
        for i in range(len(A)):
            if A[i] > self.AMax:
                A[i] = self.AMax
            if A[i] < self.AMin:
                A[i] = self.AMin
        return A

    def calcCost(self, weight, deflection, stress):
        """
        Calculates the cost of the truss corss-sections

        :param weight: Total weight of the truss
        :param deflection: deflections of all the nodes of the truss
        :param stress: stresses in all the members of the truss
        :return: cost of the truss
        """

        # adding cost if a member is exceding the stree limit
        C_total = 0
        for cd in range(self.NumMembers):
            if np.abs(stress[cd]) >  self.StressLimit:
                C1 = np.abs((stress[cd] -  self.StressLimit) /  self.StressLimit)
            else:
                C1 = 0
            C_total = C_total + C1

        # finding the maximum vertical deflection
        maxDif = 0
        for i in range(self.NumNodes):
            if np.abs(deflection[i, 1]) > maxDif:
                maxDif = np.abs(deflection[i, 1])

        # calculating cost
        Cs = weight ** 1.8 * 75 + 0.95 * maxDif * 4000000

        return Cs * (1 + C_total)


