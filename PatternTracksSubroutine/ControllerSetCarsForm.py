# coding=utf-8
# © 2021, 2022 Greg Ritacco

"""Makes a 'Set Cars Form for Track X' form for each selected track"""

from psEntities import PatternScriptEntities
from PatternTracksSubroutine import Model
from PatternTracksSubroutine import ModelSetCarsForm
from PatternTracksSubroutine import ViewSetCarsForm
from o2oSubroutine import ModelWorkEvents

SCRIPT_NAME = 'OperationsPatternScripts.PatternTracksSubroutine.ControllerSetCarsForm'
SCRIPT_REV = 20220101

_trackNameClickedOn = None

class TextBoxEntryListener(PatternScriptEntities.JAVA_AWT.event.MouseAdapter):
    """When any of the 'Set Cars Form for Track X' text inpou boxes is clicked on"""

    def __init__(self):
        self.psLog = PatternScriptEntities.LOGGING.getLogger('PS.PT.TextBoxEntryListener')

        return

    def mouseClicked(self, MOUSE_CLICKED):

        if _trackNameClickedOn:
            MOUSE_CLICKED.getSource().setText(_trackNameClickedOn)
        else:
            self.psLog.warning('No track was selected')

        return

class CreateSetCarsFormGui:
    """Creates an instance of each 'Set Cars Form for Track X' window,
    [0] is used to avoid for-loops since there is only 1 location and track
    """

    def __init__(self, setCarsForm):

        self.psLog = PatternScriptEntities.LOGGING.getLogger('PS.PT.CreateSetCarsFormGui')

        self.setCarsForm = setCarsForm
        self.locationName = setCarsForm['locations'][0]['locationName']
        self.trackName = setCarsForm['locations'][0]['tracks'][0]['trackName']
        self.buttonDict = {}

        return

    def makeFrame(self):
        """Create a JMRI jFrame window"""

        setCarsForTrackForm, self.buttonDict = ViewSetCarsForm.makeSetCarsForTrackForm(self.setCarsForm)
        setCarsForTrackWindow = ViewSetCarsForm.setCarsForTrackWindow(setCarsForTrackForm)
        self.activateButtons()

        return setCarsForTrackWindow

    def activateButtons(self):

        for track in self.buttonDict['trackButtons']:
            track.actionPerformed = self.trackRowButton

        for inputText in self.buttonDict['textBoxEntry']:
            inputText.addMouseListener(TextBoxEntryListener())

        try:
            self.buttonDict['scheduleButton'][0].actionPerformed = self.scheduleButton
        except IndexError:
            pass

        self.buttonDict['footerButtons'][0].actionPerformed = self.switchListButton
        self.buttonDict['footerButtons'][1].actionPerformed = self.setButton
        try:
            self.buttonDict['footerButtons'][2].actionPerformed = self.trainPlayerButton
        except IndexError:
            pass

        return

    def quickCheck(self):

        if not ModelSetCarsForm.testValidityOfForm(self.setCarsForm, self.buttonDict['textBoxEntry']):
            self.psLog.critical('FAIL - ModelSetCarsForm.testValidityOfForm')
            return False
        else:
            self.psLog.info('PASS - ModelSetCarsForm.testValidityOfForm')
            return True

    def trackRowButton(self, MOUSE_CLICKED):
        """Any button of the 'Set Cars Form for Track X' - row of track buttons"""

        _trackNameClickedOn = unicode(MOUSE_CLICKED.getSource().getText(), PatternScriptEntities.ENCODING)
        global _trackNameClickedOn

        return

    def scheduleButton(self, MOUSE_CLICKED):
        """The named schedule button if displayed for the active 'Set Cars Form for Track X' window"""

        scheduleName = MOUSE_CLICKED.getSource().getText()
        schedule = PatternScriptEntities.SM.getScheduleByName(scheduleName)
        track = PatternScriptEntities.LM.getLocationByName(self.locationName).getTrackByName(self.trackName, None)
        PatternScriptEntities.JMRI.jmrit.operations.locations.schedules.ScheduleEditFrame(schedule, track)

        print(SCRIPT_NAME + ' ' + str(SCRIPT_REV))

        return

    def switchListButton(self, MOUSE_CLICKED):
        """Makes a Set Cars (SC) switch list for the active 'Set Cars Form for Track X' window"""

        self.psLog.info(MOUSE_CLICKED)

        if not self.quickCheck():
            return

        PatternScriptEntities.REPORT_ITEM_WIDTH_MATRIX = PatternScriptEntities.makeReportItemWidthMatrix()

        ModelSetCarsForm.switchListButton(self.setCarsForm, self.buttonDict['textBoxEntry'])
        ViewSetCarsForm.switchListButton()

        if PatternScriptEntities.JMRI.jmrit.operations.setup.Setup.isGenerateCsvSwitchListEnabled():
            workEventName = PatternScriptEntities.BUNDLE['Switch List for Track']
            Model.writeTrackPatternCsv(workEventName)

        print(SCRIPT_NAME + ' ' + str(SCRIPT_REV))

        return





    def setButton(self, MOUSE_CLICKED):
        """Event that moves cars to the tracks entered in the text box of
            the 'Set Cars Form for Track X' form
            """

        self.psLog.info(MOUSE_CLICKED)

        if not self.quickCheck():
            return

        # mergedForm = ModelSetCarsForm.mergeForms(self.setCarsForm, self.buttonDict['textBoxEntry'])
        mergedForm = ModelSetCarsForm.makeLocationDict(self.setCarsForm, self.buttonDict['textBoxEntry'])
        ModelSetCarsForm.setRsToTrack(mergedForm)

        setCarsWindow = MOUSE_CLICKED.getSource().getTopLevelAncestor()
        setCarsWindow.setVisible(False)
        setCarsWindow.dispose()

        print(SCRIPT_NAME + ' ' + str(SCRIPT_REV))

        return







    def trainPlayerButton(self, MOUSE_CLICKED):
        """Accumulate switch lists into the o2o-Work-Events switch list
            List is reset when set cars button on Track Pattern Sub is pressed
            """

        self.psLog.info(MOUSE_CLICKED)

        if not self.quickCheck():
            return

        MOUSE_CLICKED.getSource().setBackground(PatternScriptEntities.JAVA_AWT.Color.GREEN)

        mergedForm = ModelSetCarsForm.mergeForms(self.setCarsForm, self.buttonDict['textBoxEntry'])

        o2o = ModelWorkEvents.ConvertPtMergedForm(mergedForm)
        o2o.thinTheHerd()
        o2o.getWorkEvents()
        o2o.appendRs()
        o2o.writePtWorkEvents()

        o2o = ModelWorkEvents.o2oWorkEvents()
        o2o.getWorkEvents()
        o2o.o2oHeader()
        o2o.o2oLocations()
        o2o.saveList()

        print(SCRIPT_NAME + ' ' + str(SCRIPT_REV))

        return
