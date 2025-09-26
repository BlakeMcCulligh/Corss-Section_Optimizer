import numpy as np

import Optimization
import TrussAnalysis
import pandas as pd
import openpyxl

def readIn(truss):
    NodsXlsx = pd.read_excel('Nodes.xlsx')

    x = list(NodsXlsx['X'])
    y = list(NodsXlsx['Y'])
    Suport = list(NodsXlsx['Support'])
    ForceMag = list(NodsXlsx['ForceMag'])
    ForceDir = list(NodsXlsx['ForceDir'])

    for i in range(len(x)):
        truss.addNode([x[i], y[i]])
        truss.addSuport(i, Suport[i])
        if ForceMag[i] != 0:
            truss.addPointForce(i,ForceDir[i],ForceMag[i])

    MembersXlsx = pd.read_excel('Members.xlsx')

    Node1 = list(MembersXlsx['Node1'])
    Node2 = list(MembersXlsx['Node2'])
    CorssSectionGroup = list(MembersXlsx['Cross-Section Group'])

    for i in range(len(Node1)):
        truss.addMember([Node1[i], Node2[i]], CorssSectionGroup[i])

AMin = 0.1
AMax = 40
MaxItervals = 500
PopSize = 30
stressLimit = 25

t = TrussAnalysis.Truss()
readIn(t)

NumMembers = len(t.m)
A = np.zeros(NumMembers)
for i in range(NumMembers):
    A[i] = 5

t.startAnalysis()
[S, Mass, U] = t.Analysis(A)
t.Draw(U, 50)

NumMembers = len(t.m)
NumCrossSections = NumMembers
NumNodes  = len(t.n)

a = Optimization.ParticalSwarmOptimization(NumMembers, NumNodes, NumCrossSections, AMin, AMax, MaxItervals, PopSize, stressLimit, t)
a.Evaluate()
a.Plot()