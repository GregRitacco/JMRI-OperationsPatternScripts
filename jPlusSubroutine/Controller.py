# coding=utf-8
# © 2021, 2022 Greg Ritacco

"""

"""

from opsEntities import PSE
from jPlusSubroutine import Listeners
from jPlusSubroutine import Model
from jPlusSubroutine import View

SCRIPT_NAME = 'OperationsPatternScripts.jPlusSubroutine.Controller'
SCRIPT_REV = 20221010

_psLog = PSE.LOGGING.getLogger('OPS.JP.Controller')


def restartSubroutine(subroutineFrame):
    """Allows other subroutines to restart this subroutine.
        Called by:
        PSE.restartSubroutineByName()
        """

    subroutinePanel = StartUp(subroutineFrame).makeSubroutinePanel()
    subroutineFrame.removeAll()
    subroutineFrame.add(subroutinePanel)
    subroutineFrame.revalidate()

    return

def setDropDownText():
    """Pattern Scripts/Tools/itemMethod - Set the drop down text per the config file PatternTracksSubroutine Include flag ['CP']['IJ']"""

    patternConfig = PSE.readConfigFile('CP')
    if patternConfig['jPlusSubroutine']:
        menuText = PSE.BUNDLE[u'Disable j Plus subroutine']
    else:
        menuText = PSE.BUNDLE[u'Enable j Plus subroutine']

    return menuText, 'jpItemSelected'


class StartUp:
    """Start the o2o subroutine"""

    def __init__(self, subroutineFrame=None):

        self.subroutineFrame = subroutineFrame

        return

    def makeSubroutineFrame(self):
        """Makes the title border frame"""

        self.subroutineFrame = View.ManageGui().makeSubroutineFrame()
        subroutinePanel = self.makeSubroutinePanel()
        self.subroutineFrame.add(subroutinePanel)

        _psLog.info('jPlusSubroutine makeFrame completed')

        return self.subroutineFrame

    def makeSubroutinePanel(self):
        """Makes the control panel that sits inside the frame"""

        Model.jPanelSetup()
        self.subroutinePanel, self.widgets = View.ManageGui().makeSubroutinePanel()
        self.activateWidgets()

        return self.subroutinePanel

    def activateWidgets(self):
        """The widget.getName() value is the name of the action for the widget.
            IE 'update'
            """

        widget = self.widgets['control']['UP']
        name = widget.getName()

        widget.actionPerformed = getattr(self, name)

        return

    def update(self, EVENT):
        '''Writes the text box entries to the configFile.'''

        _psLog.debug(EVENT)

        configFile = PSE.readConfigFile()

        for id, widget in self.widgets['panel'].items():
            configFile['JP'].update({id:widget.getText()})

        OSU = PSE.JMRI.jmrit.operations.setup
        OSU.Setup.setYearModeled(configFile['JP']['YR'])

        PSE.writeConfigFile(configFile)

        jPlusHeader = PSE.jPlusHeader().replace(';', '\n')
        OSU.Setup.setRailroadName(jPlusHeader)

        print(SCRIPT_NAME + ' ' + str(SCRIPT_REV))

        return
