# © 2021, 2022 Greg Ritacco

'''Pattern Scripts plugin for JMRI Operations Pro'''

import jmri
from apps import Apps
import java
import java.beans
import java.awt
import javax.swing

import logging
import time
from sys import path as sysPath

SCRIPT_NAME = 'OperationsPatternScripts.MainScript'
SCRIPT_REV = 20220101

SCRIPT_DIR = 'OperationsPatternScripts'
# SCRIPT_DIR = 'OperationsPatternScripts-2.0.0.b2'
# SCRIPT_DIR = 'OperationsPatternScripts-2.0.0.b3'

SCRIPT_ROOT = jmri.util.FileUtil.getPreferencesPath() + SCRIPT_DIR

sysPath.append(SCRIPT_ROOT)
from psEntities import MainScriptEntities
from TrainPlayerSubroutine import ExportToTrainPlayer
MainScriptEntities.SCRIPT_ROOT = SCRIPT_ROOT

class Logger:

    def __init__(self):

        logPath = jmri.util.FileUtil.getProfilePath() + 'operations\\buildstatus\\PatternScriptsLog.txt'
        logFileFormat = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.psFileHandler = logging.FileHandler(logPath, mode='w', encoding='utf-8')
        self.psFileHandler.setFormatter(logFileFormat)

        return

    def startLogger(self):

        psLog = logging.getLogger('PS')
        psLog.setLevel(10)
        psLog.addHandler(self.psFileHandler)

        return

    def stopLogger(self):

        psLog = logging.getLogger('PS')
        psLog.removeHandler(self.psFileHandler)

        return

class TrainsTableListener(javax.swing.event.TableModelListener):
    '''Catches user add or remove train while TrainPlayer support is enabled'''

    def __init__(self, builtTrainListener):

        self.builtTrainListener = builtTrainListener

        return

    def tableChanged(self, TABLE_CHANGE):

        trainList = MainScriptEntities.TM.getTrainsByIdList()
        for train in trainList:
            train.removePropertyChangeListener(self.builtTrainListener) # Does not throw error if there is no listener to remove
            train.addPropertyChangeListener(self.builtTrainListener)

        return

class BuiltTrainListener(java.beans.PropertyChangeListener):
    '''Starts TrainPlayer manifest export on trainBuilt'''

    def propertyChange(self, TRAIN_BUILT):

        if TRAIN_BUILT.propertyName == 'TrainBuilt' and TRAIN_BUILT.newValue:
            tpManifest = ExportToTrainPlayer.ManifestForTrainPlayer()
            tpManifest.passInTrain(TRAIN_BUILT.getSource())
            tpManifest.start()

        return

class PatternScriptsWindowListener(java.awt.event.WindowListener):
    '''Listener to respond to the plugin window operations. A bit verbose because of intended expansion in v3'''

    def __init__(self):

        return

    def closeSetCarsWindows(self):
        '''Close all the Set Cars windows when the Pattern Scripts window is closed'''

        for frameName in jmri.util.JmriJFrame.getFrameList():
            frame = jmri.util.JmriJFrame.getFrame(frameName)
            if frame.getName() == 'setCarsWindow':
                frame.setVisible(False)
                frame.dispose()

        return

    def windowClosed(self, WINDOW_CLOSED):

        self.closeSetCarsWindows()
        WINDOW_CLOSED.getSource().dispose()

        return

    def windowClosing(self, WINDOW_CLOSING):

        updateWindowParams(WINDOW_CLOSING.getSource())

        return

    def windowIconified(self, WINDOW_ICONIFIED):
        return
    def windowDeiconified(self, WINDOW_DEICONIFIED):
        return
    def windowOpened(self, WINDOW_OPENED):
        return
    def windowActivated(self, WINDOW_ACTIVATED):
        return
    def windowDeactivated(self, WINDOW_DEACTIVATED):
        return

def updateWindowParams(window):

    configPanel = MainScriptEntities.readConfigFile()
    configPanel['CP'].update({'PH': window.getHeight()})
    configPanel['CP'].update({'PW': window.getWidth()})
    configPanel['CP'].update({'PX': window.getX()})
    configPanel['CP'].update({'PY': window.getY()})
    MainScriptEntities.writeConfigFile(configPanel)

    return

class View:

    def __init__(self, scrollPanel):

        self.controlPanel = scrollPanel
        self.menuItemList = []

        return

    def makePsButton(self):

        psButton = javax.swing.JButton(name='psButton')

        return psButton

    def makePluginPanel(self):

        pluginPanel = javax.swing.JPanel()
        # pluginPanel.setLayout(javax.swing.BoxLayout(pluginPanel, javax.swing.BoxLayout.PAGE_AXIS))

        return pluginPanel

    def makeScrollPanel(self, pluginPanel):

        configPanel = MainScriptEntities.readConfigFile('CP')
        scrollPanel = javax.swing.JScrollPane(pluginPanel)
        scrollPanel.border = javax.swing.BorderFactory.createLineBorder(java.awt.Color.GRAY)

        # scrollPanel.setPreferredSize(java.awt.Dimension(configPanel['PW'], configPanel['PH']))
        # scrollPanel.setMaximumSize(scrollPanel.getPreferredSize())

        return scrollPanel

    def makePatternScriptsWindow(self):

        uniqueWindow = jmri.util.JmriJFrame()
        menuItemList = []

        asMenuItem = javax.swing.JMenuItem(self.setAsDropDown())
        asMenuItem.setName('asItemSelected')
        self.menuItemList.append(asMenuItem)
        tpMenuItem = javax.swing.JMenuItem(self.setTiDropDown())
        tpMenuItem.setName('tpItemSelected')
        self.menuItemList.append(tpMenuItem)
        toolsMenu = javax.swing.JMenu(u'Tools')
        toolsMenu.add(jmri.jmrit.operations.setup.OptionAction())
        toolsMenu.add(jmri.jmrit.operations.setup.PrintOptionAction())
        toolsMenu.add(jmri.jmrit.operations.setup.BuildReportOptionAction())
        toolsMenu.add(asMenuItem)
        toolsMenu.add(tpMenuItem)

        helpMenuItem = javax.swing.JMenuItem(u'Window Help...')
        helpMenuItem.setName('helpItemSelected')
        self.menuItemList.append(helpMenuItem)
        helpMenu = javax.swing.JMenu(u'Help')
        helpMenu.add(helpMenuItem)

        psMenuBar = javax.swing.JMenuBar()
        psMenuBar.add(toolsMenu)
        psMenuBar.add(jmri.jmrit.operations.OperationsMenu())
        psMenuBar.add(jmri.util.WindowMenu(uniqueWindow))
        psMenuBar.add(helpMenu)

        uniqueWindow.setName('patternScripts')
        uniqueWindow.setTitle('Pattern Scripts')
        uniqueWindow.addWindowListener(PatternScriptsWindowListener())
        uniqueWindow.setJMenuBar(psMenuBar)
        uniqueWindow.add(self.controlPanel)
        uniqueWindow.pack()
        configPanel = MainScriptEntities.readConfigFile('CP')
        uniqueWindow.setSize(configPanel['PW'], configPanel['PH'])
        uniqueWindow.setLocation(configPanel['PX'], configPanel['PY'])
        uniqueWindow.setVisible(True)

        return

    def getMenuItemList(self):

        return self.menuItemList

    def setAsDropDown(self):
        '''Set the drop down text per the Apply Schedule flag'''

        patternConfig = MainScriptEntities.readConfigFile('PT')
        if patternConfig['SF']['AS']:
            menuText = patternConfig['SF']['AT']
        else:
            menuText = patternConfig['SF']['AF']

        return menuText

    def setTiDropDown(self):
        '''Set the drop down text per the TrainPlayer Include flag'''

        patternConfig = MainScriptEntities.readConfigFile('PT')
        if patternConfig['TF']['TI']:
            menuText = patternConfig['TF']['TT']
        else:
            menuText = patternConfig['TF']['TF']

        return menuText

class Model:

    def __init__(self):

        self.psLog = logging.getLogger('PS.Model')

        return

    def makePatternScriptsPanel(self, pluginPanel):

        subroutineList = self.makeSubroutineList()
        for subroutine in subroutineList:
            pluginPanel.add(subroutine)

        return pluginPanel

    def makeSubroutineList(self):

        subroutineList = []
        controlPanelConfig = MainScriptEntities.readConfigFile('CP')
        for subroutineIncludes, isIncluded in controlPanelConfig['SI'].items():
            if (isIncluded):
                xModule = __import__(subroutineIncludes, fromlist=['Controller'])
                startUp = xModule.Controller.StartUp()
                startUp.validateSubroutineConfig()
                subroutineFrame = startUp.makeSubroutineFrame()
                subroutineList.append(subroutineFrame)
                self.psLog.info(subroutineIncludes + ' subroutine added to control panel')

        return subroutineList

class Controller(jmri.jmrit.automat.AbstractAutomaton):

    def init(self):

        self.logger = Logger()
        self.logger.startLogger()

        self.trainsTableModel = jmri.jmrit.operations.trains.TrainsTableModel()
        self.builtTrainListener = BuiltTrainListener()
        self.trainsTableListener = TrainsTableListener(self.builtTrainListener)

        self.menuItemList = []

        return

    def handle(self):

        yTimeNow = time.time()
        self.psLog = logging.getLogger('PS.Controller')

        MainScriptEntities.initialLogMessage()
        self.runValidations()
        self.addPatternScriptsButton()

        self.psLog.info('Current Pattern Scripts directory: ' + SCRIPT_ROOT)
        self.psLog.info('Main script run time (sec): ' + ('%s' % (time.time() - yTimeNow))[:6])
        print('Current Pattern Scripts directory: ' + SCRIPT_ROOT)
        print(SCRIPT_NAME + ' ' + str(SCRIPT_REV))

        return False

    def runValidations(self):

        MainScriptEntities.validateFileDestinationDirestories()
        MainScriptEntities.validateStubFile(SCRIPT_ROOT)
        MainScriptEntities.readConfigFile()
        if not MainScriptEntities.validateConfigFile(SCRIPT_ROOT):
            MainScriptEntities.backupConfigFile()
            self.psLog.warning('PatternConfig.json.bak file written')
            MainScriptEntities.writeNewConfigFile()
            self.psLog.warning('New PatternConfig.JSON file created for this profile')
        if MainScriptEntities.readConfigFile('PT')['TF']['TI']: # TrainPlayer Include
            ExportToTrainPlayer.CheckTpDestination().directoryExists()

        return

    def addPatternScriptsButton(self):
        '''The Pattern Scripts button on the PanelPro frame'''

        self.patternScriptsButton = View(None).makePsButton()
        self.patternScriptsButton.setText('Pattern Scripts')
        self.patternScriptsButton.setName('psButton')
        self.patternScriptsButton.actionPerformed = self.patternScriptsButtonAction
        Apps.buttonSpace().add(self.patternScriptsButton)
        Apps.buttonSpace().revalidate()

        return

    def addTrainsTableListener(self):

        self.trainsTableModel.addTableModelListener(self.trainsTableListener)

        return

    def removeTrainsTableListener(self):

        self.trainsTableModel.removeTableModelListener(self.trainsTableListener)

        return

    def addBuiltTrainListener(self):

        trainList = MainScriptEntities.TM.getTrainsByIdList()
        for train in trainList:
            train.addPropertyChangeListener(self.builtTrainListener)

        return

    def removeBuiltTrainListener(self):

        trainList = MainScriptEntities.TM.getTrainsByIdList()
        for train in trainList:
            train.removePropertyChangeListener(self.builtTrainListener)

        return

    def patternScriptsButtonAction(self, MOUSE_CLICKED):

        self.patternScriptsButton.setText('Restart Pattern Scripts')
        self.patternScriptsButton.actionPerformed = self.patternScriptsButtonRestartAction
        self.buildThePlugin()

        return

    def patternScriptsButtonRestartAction(self, MOUSE_CLICKED):

        self.removeTrainsTableListener()
        self.removeBuiltTrainListener()
        self.closePsWindow()
        self.logger.stopLogger()
        self.logger.startLogger()
        self.buildThePlugin()
        self.psLog.info('Pattern Scripts plugin restarted')

        return

    def closePsWindow(self):

        for frameName in jmri.util.JmriJFrame.getFrameList():
            frame = jmri.util.JmriJFrame.getFrame(frameName)
            if frame.getName() == 'patternScripts':
                updateWindowParams(frame)
                frame.setVisible(False)
                frame.dispose()

        return

    def buildThePlugin(self):

        if MainScriptEntities.readConfigFile('PT')['TF']['TI']: # TrainPlayer Include
            self.addTrainsTableListener()
            self.addBuiltTrainListener()

        emptyPluginPanel = View(None).makePluginPanel()

        # patternScriptsPlugin = Model()
        populatedPluginPanel = Model().makePatternScriptsPanel(emptyPluginPanel)

        scrollPanel = View(None).makeScrollPanel(populatedPluginPanel)
        patternScriptsWindow = View(scrollPanel)
        patternScriptsWindow.makePatternScriptsWindow()
        self.menuItemList = patternScriptsWindow.getMenuItemList()
        self.parseMenuItemList()

        return

    def parseMenuItemList(self):
        '''Use the pull down item names as the attribute to set the listener: asItemSelected, tpItemSelected, helpItemSelected'''

        for menuItem in self.menuItemList:
            menuItem.addActionListener(getattr(self, menuItem.getName()))

        return

    def asItemSelected(self, AS_ACTIVATE_EVENT):
        '''menu item-Tools/Apply Schedule'''

        patternConfig = MainScriptEntities.readConfigFile()

        if patternConfig['PT']['SF']['AS']:
            patternConfig['PT']['SF'].update({'AS': False})
            AS_ACTIVATE_EVENT.getSource().setText(patternConfig['PT']['SF']['AF'])
            self.psLog.info('Apply Schedule turned off')
            print('Apply Schedule turned off')
        else:
            patternConfig['PT']['SF'].update({'AS': True})
            AS_ACTIVATE_EVENT.getSource().setText(patternConfig['PT']['SF']['AT'])
            self.psLog.info('Apply Schedule turned on')
            print('Apply Schedule turned on')

        MainScriptEntities.writeConfigFile(patternConfig)

        return

    def tpItemSelected(self, TP_ACTIVATE_EVENT):
        '''menu item-Tools/Enable Trainplayer'''

        patternConfig = MainScriptEntities.readConfigFile()

        if patternConfig['PT']['TF']['TI']: # If enabled, turn it off
            patternConfig['PT']['TF'].update({'TI': False})
            TP_ACTIVATE_EVENT.getSource().setText(patternConfig['PT']['TF']['TF'])

            self.trainsTableModel.removeTableModelListener(self.trainsTableListener)
            self.removeBuiltTrainListener()

            self.psLog.info('TrainPlayer support deactivated')
            print('TrainPlayer support deactivated')
        else:
            patternConfig['PT']['TF'].update({'TI': True})
            TP_ACTIVATE_EVENT.getSource().setText(patternConfig['PT']['TF']['TT'])

            ExportToTrainPlayer.CheckTpDestination().directoryExists()
            self.trainsTableModel.addTableModelListener(self.trainsTableListener)
            self.addBuiltTrainListener()

            self.psLog.info('TrainPlayer support activated')
            print('TrainPlayer support activated')

        MainScriptEntities.writeConfigFile(patternConfig)

        return

    def helpItemSelected(self, OPEN_HELP_EVENT):
        '''menu item-Help/Window help...'''

        helpStubPath = MainScriptEntities.getStubPath()
        jmri.util.HelpUtil.openWebPage(helpStubPath)

        return

Controller().start()
