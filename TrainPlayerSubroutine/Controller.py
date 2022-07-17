# coding=utf-8
# © 2021, 2022 Greg Ritacco

"""The TrainPlayer Subroutine will be implemented in V3, this is just the framework"""

from psEntities import PatternScriptEntities
from TrainPlayerSubroutine import Model
from TrainPlayerSubroutine import View

SCRIPT_NAME = 'OperationsPatternScripts.TrainPlayerSubroutine.Controller'
SCRIPT_REV = 20220101

class StartUp:
    """Start the TrainPlayer subroutine"""

    def __init__(self, subroutineFrame=None):

        self.psLog = PatternScriptEntities.LOGGING.getLogger('PS.TP.Controller')
        self.subroutineFrame = subroutineFrame

        return

    def makeSubroutineFrame(self):
        """Makes the title border frame"""

        self.subroutineFrame = View.ManageGui().makeSubroutineFrame()
        subroutinePanel = self.makeSubroutinePanel()
        self.subroutineFrame.add(subroutinePanel)

        self.psLog.info('TrainPlayer makeFrame completed')

        return self.subroutineFrame

    def makeSubroutinePanel(self):
        """Makes the control panel that sits inside the frame"""

        self.subroutinePanel, self.widgets = View.ManageGui().makeSubroutinePanel()
        self.activateWidgets()

        return self.subroutinePanel

    def activateWidgets(self):
        '''Maybe get them by name?'''

        self.widgets[0].actionPerformed = self.inventoryUpdator
        self.widgets[1].actionPerformed = self.bButtonAction

        return

    def inventoryUpdator(self, EVENT):
        '''Updates JMRI rolling stock locations based on TrainPlayer inventory export'''

        updatedInventory = Model.UpdateInventory()
        if not updatedInventory.checkList():
            self.psLog.info('No TrainPlayer inventory list to update')
            return

        updatedInventory.updateExisting()
        # errorReport = updatedInventory.getErrorReport()
        # errorReportPath = PatternScriptEntities.PROFILE_PATH + 'operations\\patternReports\\Update Inventory.txt'
        # PatternScriptEntities.genericWriteReport(errorReportPath, errorReport)
        #
        # fileToOpen = PatternScriptEntities.JAVA_IO.File(errorReportPath)
        # if fileToOpen.isFile():
        #     PatternScriptEntities.genericDisplayReport(fileToOpen)
        # else:
        #     self.psLog.warning('Not found: ' + workEventPath)

        self.psLog.info('Updated Rolling stock locations from TrainPlayer')

        print(SCRIPT_NAME + ' ' + str(SCRIPT_REV))

        return

    def bButtonAction(self, EVENT):
        '''Whatever this button ends up doing'''

        print('This button is not implemented')

        return
