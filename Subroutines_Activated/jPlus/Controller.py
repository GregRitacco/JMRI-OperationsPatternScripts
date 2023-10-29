# coding=utf-8
# © 2023 Greg Ritacco

"""
A simple subroutine to add extended info about a railroad to JMRI.
The info can be input directly or imported from TrainPlayer if using o2o.
This subroutine causes a modified JMRI manifest and
a modified JMRI switch list set to be created.
"""

from opsEntities import PSE
from opsEntities import TextReports
from Subroutines_Activated.jPlus import Model
from Subroutines_Activated.jPlus import View

SCRIPT_NAME = '{}.{}'.format(PSE.SCRIPT_DIR, __name__)
SCRIPT_REV = 20231001

_psLog = PSE.LOGGING.getLogger('OPS.JP.Controller')

def getSubroutineDropDownItem():
    """Pattern Scripts/Tools/'Show or disable' Subroutines.<subroutine>"""

    subroutineName = __package__.split('.')[1]

    menuItem = PSE.JAVX_SWING.JMenuItem()

    configFile = PSE.readConfigFile()
    if configFile[subroutineName]['SV']:
        menuText = '{} {}'.format(PSE.getBundleItem('Hide'), __package__)
    else:
        menuText = '{} {}'.format(PSE.getBundleItem('Show'), __package__)

    menuItem.setName(__package__)
    menuItem.setText(menuText)

    return menuItem

def opsPreProcess(message=None):

    return

def opsProcess(message=None):
    """
    Modifies the OPS pattern report.
    Modifies the OPS switch list.
    Modifies the JMRI manifest.
    """

    if message == 'opsPatternReport':
        Model.modifyPatternReport()

    if message == 'opsSwitchList':
        Model.modifySwitchList()

    if message == 'TrainBuilt':
        Model.modifyManifest()

    return

def opsPostProcess(message=None):
    """
    Writes the OPS version of a train manifest.
    """
    if message == 'TrainBuilt':
        train = PSE.getNewestTrain()
        manifest = PSE.getTrainManifest(train)

        textManifest = TextReports.opsJmriManifest(manifest)
        manifestName = 'ops train ({}).txt'.format(train.toString())
        manifestPath = PSE.OS_PATH.join(PSE.PROFILE_PATH, 'operations', 'manifests', manifestName)
        PSE.genericWriteReport(manifestPath, textManifest)

    return


class StartUp:
    """
    Start the jPlus subroutine
    """

    def __init__(self):

        self.configFile = PSE.readConfigFile()

        return

    def getSubroutine(self):
        """
        Returns the subroutine and activates the widgets.
        """

        subroutine, self.widgets = View.ManageGui().makeSubroutine()
        subroutineName = __package__.split('.')[1]
        subroutine.setVisible(self.configFile[subroutineName]['SV'])
        self.activateWidgets()

        _psLog.info(__package__ + ' makeFrame completed')

        return subroutine

    def startUpTasks(self):

        return

    def activateWidgets(self):

        widget = self.widgets['control']['UP']
        widget.actionPerformed = self.update

        widget = self.widgets['control']['UX']
        widget.actionPerformed = self.useExtended

        return

    def update(self, EVENT):
        """
        Update button.
        """

        _psLog.debug(EVENT)

        Model.updateRailroadDetails(self.widgets['panel'])
        Model.compositeRailroadName()
        Model.updateYearModeled()
        Model.refreshOperationsSettingsFrame()

        self.widgets['control']['UX'].setSelected(True)

        print('{} rev:{}'.format(SCRIPT_NAME, SCRIPT_REV))

        return

    def useExtended(self, EVENT):
        """
        The Use Extended Header checkbox.
        """

        _psLog.debug(EVENT)

        configFile = PSE.readConfigFile()            
        configFile['jPlus']['LD'].update({'EH':EVENT.getSource().selected})
        PSE.writeConfigFile(configFile)

        return
