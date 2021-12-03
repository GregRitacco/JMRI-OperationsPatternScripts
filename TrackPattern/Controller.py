# coding=utf-8
# Extended ìÄÅÉî
# Controller script for the track pattern subroutine
# No restrictions on use
# © 2021 Greg Ritacco

import jmri
import logging
import java.awt.event
from sys import path
path.append(jmri.util.FileUtil.getHomePath() + 'JMRI\\OperationsPatternScripts')
import MainScriptEntities
import TrackPattern.Model
import TrackPattern.View
import TrackPattern.ControllerSetCarsForm

class StartUp():
    '''Start the the Track Pattern subroutine'''

    scriptRev = 'TrackPattern.Controller v20211125'

    def __init__(self):

        self.psLog = logging.getLogger('PS.TP.Control')

        return

    class ComboBoxListener(java.awt.event.ActionListener):
        '''Event triggered from location combobox selection'''

        def __init__(self, panel, controls):
            self.panel = panel
            self.controls = controls

        def actionPerformed(self, event):
            try:
                newConfigFile = TrackPattern.Model.updatePatternLocation(event.getSource().getSelectedItem())
                MainScriptEntities.writeConfigFile(newConfigFile)
                newConfigFile = TrackPattern.Model.getPatternTracks(event.getSource().getSelectedItem())
                MainScriptEntities.writeConfigFile(newConfigFile)
                newConfigFile = TrackPattern.Model.updateCheckBoxStatus(False, self.controls[2].selected)
                MainScriptEntities.writeConfigFile(newConfigFile)
                self.controls = TrackPattern.View.manageGui().updatePanel(self.panel)
                StartUp().activateButtons(self.panel, self.controls)
        # catch the error when the user edits the location name
            except AttributeError:
                TrackPattern.Model.initializeConfigFile()
                self.controls = TrackPattern.View.manageGui().updatePanel(self.panel)
                StartUp().activateButtons(self.panel, self.controls)
                self.psLog.info('Location list changed, config file updated')

            print(StartUp.scriptRev)
            return

    def whenPABoxClicked(self, event):
        '''When the Yard Tracks Only box is clicked'''

        if (self.controls[1].selected):
            trackList = TrackPattern.Model.getTracksByType(self.controls[0].getSelectedItem(), 'Yard')
        else:
            trackList = TrackPattern.Model.getTracksByType(self.controls[0].getSelectedItem(), None)
        newConfigFile = TrackPattern.Model.updatePatternLocation(self.controls[0].getSelectedItem())
        MainScriptEntities.writeConfigFile(newConfigFile)
        newConfigFile = TrackPattern.Model.updatePatternTracks(trackList)
        MainScriptEntities.writeConfigFile(newConfigFile)
        newConfigFile = TrackPattern.Model.updateCheckBoxStatus(self.controls[1].selected, self.controls[2].selected)
        MainScriptEntities.writeConfigFile(newConfigFile)
        self.controls = TrackPattern.View.manageGui().updatePanel(self.panel)
        self.activateButtons(self.panel, self.controls)

        return

    def whenTPButtonPressed(self, event):
        '''Makes a track pattern based on the config file'''

    # Boilerplate - update the config file
        TrackPattern.Model.updateSettings(self.controls)
        self.psLog.info('Configuration file updated with new settings')
    # Button specific
        selectedTracks = TrackPattern.Model.getSelectedTracks()
        trackPatternDict = TrackPattern.Model.makeTrackPatternDict(selectedTracks)
        trackPatternDict.update({'RT': u'Track Pattern for Location'})
        location = trackPatternDict['YL']
        trackPatternJson = TrackPattern.Model.writePatternJson(location, trackPatternDict)
        self.psLog.info('Track Pattern for ' + location + ' JSON file written')
        textSwitchList = TrackPattern.Model.writeTextSwitchList(location, trackPatternDict)
        self.psLog.info('Track Pattern for ' + location + ' switch list file written')
        if (jmri.jmrit.operations.setup.Setup.isGenerateCsvSwitchListEnabled()):
            csvSwitchList = TrackPattern.Model.writeCsvSwitchList(location, trackPatternDict)
            self.psLog.info('Track Pattern for ' + location + ' CSV file written')
        TrackPattern.View.displayTextSwitchlist(location)
        print(StartUp().scriptRev)

        return

    def whenSCButtonPressed(self, event):
        '''Opens a set cars window for each checked track'''

    # Boilerplate - update the config file
        self.controls = TrackPattern.Model.updateSettings(self.controls)
        self.psLog.info('Configuration file updated with new settings')
    # Button specific
        selectedTracks = TrackPattern.Model.getSelectedTracks()
        windowOffset = 200
    # create a set cars form for each track in its own window
        if (selectedTracks):
            i = 0
            for track in selectedTracks:
                listForTrack = TrackPattern.Model.getSetCarsData(self.controls[0].getSelectedItem(), track)
                newWindow = TrackPattern.ControllerSetCarsForm.SetCarsWindowInstance(listForTrack)
                newWindow.setCarsForTrackWindow(windowOffset)
                self.psLog.info(u'Set Cars Window created for track ' + track)
                windowOffset += 50
                i += 1
            self.psLog.info(str(i) + ' Set Cars windows for ' + self.controls[0].getSelectedItem() + ' created')
        else:
            self.psLog.info('No tracks were selected')
        print(StartUp().scriptRev)
        
        return

    def whenPRButtonPressed(self, event):
        '''Displays the pattern report log file in a notepad window'''

        TrackPattern.View.displayPatternLog()
        print(StartUp().scriptRev)

        return

    def activateButtons(self, panel, controls):
        '''Assigns actions to the subroutine widgets'''

        self.panel = panel
        self.controls = controls
        self.controls[0].addActionListener(self.ComboBoxListener(self.panel, self.controls))
        self.controls[1].actionPerformed = self.whenPABoxClicked
        self.controls[4].actionPerformed = self.whenTPButtonPressed
        self.controls[5].actionPerformed = self.whenSCButtonPressed
        self.controls[6].actionPerformed = self.whenPRButtonPressed

        return

    def makeSubroutineFrame(self):
        '''Makes the title boarder frame'''

        self.patternFrame = TrackPattern.View.manageGui().makeFrame()
        self.psLog.info('track pattern makeFrame completed')

        return self.patternFrame

    def makeSubroutinePanel(self):
        '''Make and activate the Track Pattern objects'''

        MainScriptEntities.writeConfigFile(TrackPattern.Model.updateLocations())
        self.panel, self.controls = TrackPattern.View.manageGui().makePanel()
        self.activateButtons(self.panel, self.controls)
        self.psLog.info('track pattern makeSubroutinePanel completed')

        return self.panel
