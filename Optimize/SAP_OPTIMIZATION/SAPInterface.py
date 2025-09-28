import comtypes.client
#from comtypes.gen import SAP2000v1

def openSAP():
    """
    Opens SAP2000
    :return: The open program sap object
    """
    helper = comtypes.client.CreateObject("SAP2000v1.Helper")
    helper = helper.QueryInterface(comtypes.gen.SAP2000v1.cHelper)
    sap_object = helper.GetObject("CSI.SAP2000.API.SapObject")
    if sap_object is None:
        sap_object = helper.CreateObjectProgID("CSI.SAP2000.API.SapObject")
        sap_object.ApplicationStart()

    return sap_object

def createSAPFile(sap_object):
    """
    creates a SAP file in the current open program
    creates the material properties

    :param sap_object: the open program SAP object
    :return: the SAP model
    """
    SapModel = sap_object.SapModel

    lb_in_F = 1
    SapModel.InitializeNewModel(lb_in_F)

    ret = SapModel.File.NewBlank()

    # define material property (material name, material)
    MATERIAL_Steel = 1
    ret = SapModel.PropMaterial.SetMaterial('Steel', MATERIAL_Steel)

    # assign isotropic mechanical properties to material (material, E, Poisson's ratio, thermal coefficent)
    ret = SapModel.PropMaterial.SetMPIsotropic('Steel', 10000, 0.2, 0.0000055)

    inportCrossSections(SapModel)

    return SapModel

def inportCrossSections(SapModel):
    """
    adds all the cross-sections to the SAP model

    :param SapModel: the SAP model
    """
    ret = SapModel.PropFrame.SetRectangle("R1", "Steel", 10, 5)
