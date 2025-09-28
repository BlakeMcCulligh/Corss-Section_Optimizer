import pandas as pd
import GeneralFunctions
import time

from Optimize import SAPInterface

class Truss:
    def __init__(self, bridgelength, StringerElevation):
        self.nodes = []  # [x, y]
        self.supports = []  # [node, support] Support: 1 = pin, 2 = roller

        self.members = []  # [node1, node2]
        self.CSGroup = []  # cross-section group
        self.CSGcrossSection = []  # cross-section for a given cross-section group

        self.nodeNames = []
        self.memberNames = []

        self.Sap_Object = SAPInterface.openSAP()
        self.readIn()

        self.BridgeLength = bridgelength
        self.StringerElevation = StringerElevation

        self.preLoadNames = ['L=3_PreLoad', 'L=4-6_PreLoad', 'L=5-6_PreLoad', 'L=6-6_PreLoad', 'L=7-6_PreLoad',
                             'L=8-6_PreLoad', 'L=9_PreLoad', 'L=9-6_PreLoad', 'L=10_PreLoad', 'L=11_PreLoad',
                             'L=12_PreLoad']
        self.MainSpanNames = ['L=3_Main', 'L=4-6_Main', 'L=5-6_Main', 'L=6-6_Main', 'L=7-6_Main', 'L=8-6_Main',
                              'L=9_Main',
                              'L=9-6_Main', 'L=10_Main', 'L=11_Main', 'L=12_Main']
        self.CantileverNames = ['L=3_Cant', 'L=4-6_Cant', 'L=5-6_Cant', 'L=6-6_Cant', 'L=7-6_Cant', 'L=8-6_Cant',
                                'L=9_Cant',
                                'L=9-6_Cant', 'L=10_Cant', 'L=11_Cant', 'L=12_Cant']

    def anaylize(self, CSGcrossSections, Iteration, Population, CantileverPoint):
        self.CSGcrossSection = CSGcrossSections

        #tS = time.time()
        SapModel = SAPInterface.createSAPFile(self.Sap_Object)
        #tE = time.time()
        #print('Time to create file: ' + str(tE - tS))

        #tS = time.time()
        self.addToSAPFile(SapModel)
        #tE = time.time()
        #print('Time to add geomitry: ' + str(tE - tS))

        #tS = time.time()
        self.addLoads(SapModel, self.BridgeLength, self.StringerElevation)
        #tE = time.time()
        #print('Time to add loads: ' + str(tE - tS))

        #tS = time.time()
        self.addSuports(SapModel)
        #tE = time.time()
        #print('Time to add suports: ' + str(tE - tS))

        #tS = time.time()
        self.save(SapModel, Iteration, Population)
        #tE = time.time()
        #print('Time to save: ' + str(tE - tS))

        #tS = time.time()
        [mainDisplacementMax, cantileverDisplacementMax, massOfTruss] = self.solve(SapModel, CantileverPoint, Iteration,
                                                                                   Population)
        #tE = time.time()
        #print('Time to solve and get data: ' + str(tE - tS))

        #tS = time.time()
        cost = self.calcCost(mainDisplacementMax, cantileverDisplacementMax, massOfTruss)
        #tE = time.time()
        #print('Time to calc cost: ' + str(tE - tS))

        return cost

    def addToSAPFile(self, SapModel):
        for i in range(len(self.nodes)):
            Name = ""
            [a, ret] = SapModel.PointObj.AddCartesian(0, self.nodes[i][0], self.nodes[i][1], Name, str(i), 'GLOBAL',
                                                      False, 0)
            self.nodeNames.append(a)

        for i in range(len(self.members)):
            Name = ""
            [a, ret] = SapModel.FrameObj.AddByPoint(self.nodeNames[self.members[i][0]],
                                                    self.nodeNames[self.members[i][1]],
                                                    Name,
                                                    self.CSGcrossSection[self.CSGroup[i]],
                                                    str(i))
            self.memberNames.append(a)

    def readIn(self):
        NodsXlsx = pd.read_excel('Nodes.xlsx')

        x = list(NodsXlsx['X'])
        y = list(NodsXlsx['Y'])
        Suport = list(NodsXlsx['Support'])
        Number = list(NodsXlsx['Number'])

        listConvert = [None] * (max(Number) + 1)

        for i in range(len(Number)):
            listConvert[Number[i]] = i

        for i in range(len(x)):
            self.nodes.append([x[i], y[i]])
            self.supports.append([i, Suport[i]])

        MembersXlsx = pd.read_excel('Members.xlsx')

        Node1 = list(MembersXlsx['Node1'])
        Node2 = list(MembersXlsx['Node2'])
        CorssSectionGroup = list(MembersXlsx['Cross-Section Group'])

        for i in range(len(Node1)):
            self.members.append([listConvert[Node1[i]], listConvert[Node2[i]]])
            self.CSGroup.append(CorssSectionGroup[i])

    def addLoads(self, SapModel, BridgeLength, StringerElevation):

        BetweenMainSpan = [[36, 70], [54, 90], [66, 102], [78, 114], [90, 126], [102, 138], [108, 144], [114, 150],
                           [120, 156], [132, 168], [144, 180]]
        BetweenCatilever = [BridgeLength - 36, BridgeLength]

        self.addPreLoad(SapModel, BetweenMainSpan, BetweenCatilever, StringerElevation)
        self.addLoadsMainSpan(SapModel, BetweenMainSpan, StringerElevation)
        self.addLoadsCantilever(SapModel, BetweenMainSpan, BetweenCatilever, StringerElevation)

    def addSuports(self, SapModel):
        restraint = [[False, False, False, False, False, False], [True, True, True, False, False, False],
                     [False, False, True, False, False, False], [False, False, True, False, False, False]]
        for i in range(len(self.supports)):
            ret = SapModel.PointObj.setRestraint(str(self.supports[i][0]), restraint[self.supports[i][1]])

    def save(self, SapModel, Iteration, Population):
        OutputPath = 'C:\\Users\\blake\\OneDrive\\Desktop\\Sap2000CodeOutput\\Save_' + str(Iteration) + "_" + str(Population)
        ret = SapModel.File.Save(OutputPath)

    def solve(self, SapModel, CantileverPoint, Iteration, Population):
        # run model (this will create the analysis model)
        ret = SapModel.Analyze.RunAnalysis()

        # get preload results
        preLoadResults = self.getLoadCasesVerticalResults(SapModel, self.preLoadNames)
        print(preLoadResults)
        # get mainspan load results
        mainSpanLoadResults = self.getLoadCasesVerticalResults(SapModel, self.MainSpanNames)
        print(mainSpanLoadResults)
        # get cantilver load results
        cantilverLoadResults = self.getLoadCasesVerticalResults(SapModel, self.CantileverNames)
        print(cantilverLoadResults)

        mainSpanDisplacement = []
        cantileverDisplacement = []
        for i in range(len(preLoadResults)):
            cantileverDisplacement.append(cantilverLoadResults[i][CantileverPoint] - preLoadResults[i][CantileverPoint])
            caseMainDisplacement = []
            for j in range(len(preLoadResults[i])):
                caseMainDisplacement.append(mainSpanLoadResults[i][j] - preLoadResults[i][j])
            mainSpanDisplacement.append(max(caseMainDisplacement))

        mainDisplacementMax = max(mainSpanDisplacement)
        cantileverDisplacementMax = max(cantileverDisplacement)

        massOfTruss = self.getMass(SapModel)

        self.saveResults(Iteration, Population, mainDisplacementMax, cantileverDisplacementMax, massOfTruss)
        return mainDisplacementMax, cantileverDisplacementMax, massOfTruss

    def AddStringerLoads(self, SapModel, LoadCase, StringerElevation, BetweenDis, Magnitude, Direction):
        """
        Adds distributed loads to the stringer

        :param SapModel: The SAP Model
        :param LoadCase: Name of the Load Case the Load is to be in
        :param StringerElevation: Height of the top of the stringer
        :param BetweenDis: the range in y direction the load is to be applyed
        :param Magnitude: magnitued of the force (lb/in)
        :param Direction: direction of the force (4 = lateral, 10 = gravity)
        :return:
        """
        for i in range(len(self.members)):
            n1 = self.nodes[self.members[i][0]]
            n2 = self.nodes[self.members[i][1]]

            if (n1[1] == StringerElevation) & (n2[1] == StringerElevation):
                rangeOverlap = GeneralFunctions.overlap_range([n1[0], n2[0]], BetweenDis)
                if rangeOverlap is not None:
                    ret = SapModel.FrameObj.SetLoadDistributed(self.memberNames[i], LoadCase, 1, Direction,
                                                               rangeOverlap[0] - n1[0],
                                                               rangeOverlap[1] - n1[0], Magnitude, Magnitude,
                                                               'GLOBAL')
                    if ret != 0:
                        print("AddStringerLoads Failed")

    def addPreLoad(self, SapModel, BetweenMainSpan, BetweenCantilever, StringerElevation):
        LTYPE_OTHER = 8
        MagPreLoad = 2.7778  # lbs/in

        for i in range(len(self.preLoadNames)):
            ret = SapModel.LoadPatterns.Add(self.preLoadNames[i], LTYPE_OTHER, 1, True)
            self.AddStringerLoads(SapModel, self.preLoadNames[i], StringerElevation, BetweenMainSpan[i],
                                  MagPreLoad, 10)
            self.AddStringerLoads(SapModel, self.preLoadNames[i], StringerElevation, BetweenCantilever, MagPreLoad,
                                  10)

    def addLoadsMainSpan(self, SapModel, BetweenMainSpan, StringerElevation):
        LTYPE_OTHER = 8
        MainSpanLoad = 44.4445  # lbs/in

        for i in range(len(self.MainSpanNames)):
            ret = SapModel.LoadPatterns.Add(self.MainSpanNames[i], LTYPE_OTHER, 1, True)
            self.AddStringerLoads(SapModel, self.MainSpanNames[i], StringerElevation, BetweenMainSpan[i],
                                  MainSpanLoad, 10)

    def addLoadsCantilever(self, SapModel, BetweenMainSpan, BetweenCatilever, StringerElevation):
        LTYPE_OTHER = 8
        MainSpanLoad = 44.4445  # lbs/in
        CantileverLoad = 25  # lbs/in

        for i in range(len(self.CantileverNames)):
            ret = SapModel.LoadPatterns.Add(self.CantileverNames[i], LTYPE_OTHER, 1, True)
            self.AddStringerLoads(SapModel, self.CantileverNames[i], StringerElevation, BetweenMainSpan[i],
                                  MainSpanLoad, 10)
            self.AddStringerLoads(SapModel, self.CantileverNames[i], StringerElevation, BetweenCatilever,
                                  CantileverLoad,
                                  10)

    def getVerticalDisp(self, SapModel, i):
        ObjectElm = 0
        NumberResults = 0
        Obj = []
        Elm = []
        LoadCase = []
        StepType = []
        StepNum = []
        U1 = []
        U2 = []
        U3 = []
        R1 = []
        R2 = []
        R3 = []
        [NumberResults, Obj, Elm, LoadCase, StepType, StepNum, U1, U2, U3, R1, R2, R3,
         ret] = SapModel.Results.JointDispl(self.nodeNames[i], ObjectElm, NumberResults, Obj, Elm, LoadCase, StepType,
                                            StepNum, U1, U2, U3, R1, R2, R3)
        return U3[0]

    def getLoadCasesVerticalResults(self, SapModel, ListLoadCasses):
        LoadCaseResults = []
        for i in range(len(ListLoadCasses)):
            ret = SapModel.Results.Setup.DeselectAllCasesAndCombosForOutput()
            ret = SapModel.Results.Setup.SetCaseSelectedForOutput(ListLoadCasses[i])

            LoadDisplacement = []
            for j in range(len(self.nodes)):
                LoadDisplacement.append(self.getVerticalDisp(SapModel, j))
            LoadCaseResults.append(LoadDisplacement)
        return LoadCaseResults

    def getMass(self, SapModel):
        a = 1
        #TODO

    def saveResults(self, Iteration, Population, mainDisplacementMax, cantileverDisplacementMax, massOfTruss):
        #TODO
        print(cantileverDisplacementMax)

        a = 1

    def calcCost(self, mainDisplacementMax, cantileverDisplacementMax, massOfTruss):
        #TODO

        a = 1
        return 1

# test
bridgeLength = 276
stringerElevation = 25.5
iteration = 1
population = 1
cantileverPoint = 8

T = Truss(bridgeLength, stringerElevation)
TStart = time.time()
T.anaylize(["R1"], iteration, population, cantileverPoint)
TEnd = time.time()
print(TEnd - TStart)
