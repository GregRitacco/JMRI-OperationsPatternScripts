# coding=utf-8
# © 2023 Greg Ritacco

"""
PSE is an abbreviation for Pattern Script Entities.
Support methods and package constants for all Pattern Script subroutines.
"""

import jmri as JMRI
from java import io as JAVA_IO
import java.awt as JAVA_AWT
import java.nio.file as JAVA_NIO
import java.beans as JAVA_BEANS # Called by the listeners
import javax.swing as JAVX_SWING

import logging as LOGGING
import apps as APPS
import time as TIME
from HTMLParser import HTMLParser as HTML_PARSER
from json import loads as jsonLoadS, dumps as jsonDumpS
from codecs import open as codecsOpen

"""
Ghost imports from MainScript:
    PSE.PLUGIN_ROOT = PLUGIN_ROOT
    PSE.SCRIPT_DIR = SCRIPT_DIR
    PSE.JMRI = jmri
    PSE.SYS = sys
    PSE.OS_PATH = OS_PATH
    PSE.BUNDLE = mainScript/handle/Bundle.getBundleForLocale()
    PSE.ENCODING = PSE.readConfigFile('Main Script')['CP']['SE']
Ghost imports from Bundle:
    PSE.BUNDLE_DIR = PSE.OS_PATH.join(PSE.PLUGIN_ROOT, 'opsBundle')
"""

PROFILE_PATH = JMRI.util.FileUtil.getProfilePath()
BUNDLE = {}
REPORT_ITEM_WIDTH_MATRIX = {}
TRACK_NAME_CLICKED_ON = ''

# Dealers choice, both work OK:
J_BUNDLE = JMRI.jmrit.operations.setup.Setup()
# SB = JMRI.jmrit.operations.setup.Bundle()
# SB.handleGetMessage('road')

SCRIPT_NAME = 'OperationsPatternScripts.opsEntities.PSE'
SCRIPT_REV = 20230201

OM = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.OperationsManager)
PM = JMRI.InstanceManager.getDefault(JMRI.util.gui.GuiLafPreferencesManager)
TM = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.trains.TrainManager)
RM = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.routes.RouteManager)
LM = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.locations.LocationManager)
DM = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.locations.divisions.DivisionManager)
CM = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.rollingstock.cars.CarManager)
KM = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.rollingstock.cars.KernelManager)
SM = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.locations.schedules.ScheduleManager)
EM = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.rollingstock.engines.EngineManager)
ZM = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.rollingstock.engines.ConsistManager)

OMX = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.setup.OperationsSetupXml)
TMX = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.trains.TrainManagerXml)
RMX = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.routes.RouteManagerXml)
LMX = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.locations.LocationManagerXml)
CMX = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.rollingstock.cars.CarManagerXml)
EMX = JMRI.InstanceManager.getDefault(JMRI.jmrit.operations.rollingstock.engines.EngineManagerXml)

_psLog = LOGGING.getLogger('OPS.OE.PSE')


class Logger:
    """Homebrew logging."""

    def __init__(self, logPath):

        logFileFormat = LOGGING.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.psFileHandler = LOGGING.FileHandler(logPath, mode='w', encoding='utf-8')
        self.psFileHandler.setFormatter(logFileFormat)

        return

    def startLogger(self, log):

        psLog = LOGGING.getLogger(log)
        psLog.setLevel(10)
        psLog.addHandler(self.psFileHandler)

        return

    def stopLogger(self, log):

        psLog = LOGGING.getLogger(log)
        psLog.removeHandler(self.psFileHandler)

        return

    def initialLogMessage(self, log):

        log.debug('Initialize log file - DEBUG level test message')
        log.info('Initialize log file - INFO level test message')
        log.warning('Initialize log file - WARNING level test message')
        log.error('Initialize log file - ERROR level test message')
        log.critical('Initialize log file - CRITICAL level test message')

        return


"""Logging Methods"""


def makePatternLog():
    """
    creates a pattern log for display based on the log level, as set by getBuildReportLevel.
    Called by:
    MainScript.Controller.logItemSelected
    """

    outputPatternLog = ''
    buildReportLevel = JMRI.jmrit.operations.setup.Setup.getBuildReportLevel()

    loggingIndex = logIndex()
    logLevel = loggingIndex[buildReportLevel]

    fileName = 'PatternScriptsLog.txt'
    targetPath = OS_PATH.join(PROFILE_PATH, 'operations', 'buildstatus', fileName)
    patternLogFile = genericReadReport(targetPath)
    for thisLine in patternLogFile.splitlines():

        if loggingIndex['9'] in thisLine and int(buildReportLevel) > 0: # critical
            outputPatternLog += thisLine + '\n'
        if loggingIndex['7'] in thisLine and int(buildReportLevel) > 0: # error
            outputPatternLog += thisLine + '\n'
        if loggingIndex['5'] in thisLine and int(buildReportLevel) > 0: # warning
            outputPatternLog += thisLine + '\n'
        if loggingIndex['3'] in thisLine and int(buildReportLevel) > 2: # info
            outputPatternLog += thisLine + '\n'
        if loggingIndex['1'] in thisLine and int(buildReportLevel) > 4: # debug
            outputPatternLog += thisLine + '\n'

    return outputPatternLog

def logIndex():
    """
    Moved here but may be put back into configFile.
    Called by:
    PSE.makePatternLog
    """

    loggingIndex = {"9": "- CRITICAL -", "7": "- ERROR -", "5": "- WARNING -", "3": "- INFO -", "1": "- DEBUG -"}

    return loggingIndex


"""GUI Methods"""


def repaintPatternScriptsWindow():
    """
    Repaints the Pattern Scripts window.
    Called by:
    All Show/Hide pulldowns.
    """

    frameTitle = getBundleItem('Pattern Scripts')
    targetPanel = getComponentByName(frameTitle, 'subroutinePanel')
    targetPanel.removeAll()
    targetPanel = addActiveSubroutines(targetPanel)
    targetPanel.validate()
    targetPanel.repaint()

    return

def restartAllSubroutines():

    for subroutine in getSubroutineDirs():
        subroutine = 'Subroutines.' + subroutine
        restartSubroutineByName(subroutine)

    return

def restartSubroutineByName(subRoutineName):
    """
    Finds the named subroutine in the plugin and restarts it.
    subroutineName: Subroutines.<subroutine>
    """

    frameName = getBundleItem('Pattern Scripts')
    subroutine = getComponentByName(frameName, subRoutineName)
    if subroutine:

        package = __import__(subRoutineName, globals(), locals(), ['Controller'], 0)
        # restart = package.Controller.StartUp(subroutine)
        restart = package.Controller.StartUp()
        subroutinePanel = restart.getSubroutineGui()
        restart.startUpTasks()

        subroutine.removeAll()
        subroutine.add(subroutinePanel)

        subroutine.validate()
        subroutine.repaint()

        print('Restarted: ' + subRoutineName)
    else:
        print('Not currently active: ' + subRoutineName)
        
    return

def validateSubroutines():
    """Checks that each active subroutine has a True/False entry in ['Main Scripts']['CP']."""

    configFile = readConfigFile()

    for subroutine in getSubroutineDirs():
        subroutineName = 'Subroutines.' + subroutine
        try:
            configFile['Main Script']['CP'][subroutineName]
        except:
            print('Exception at: PSE.validateSubroutines')
            configFile['Main Script']['CP'][subroutineName] = True

    writeConfigFile(configFile)

    return

def addActiveSubroutines(targetPanel):
    """Adds the activated subroutines to the subroutinePanel of Pattern Scripts."""

    configFile = readConfigFile()



# Catch dynamic add or removal of a subroutine
    for subroutine in getSubroutineDirs():
        subroutineName = 'Subroutines.' + subroutine
        try:
            configFile['Main Script']['CP'][subroutineName]
        except:
            print('Exception at: PSE.addActiveSubroutines')
            configFile['Main Script']['CP'][subroutineName] = True

    writeConfigFile(configFile)
    configFile = readConfigFile()

    for subroutine in getSubroutineDirs():
        subroutineName = 'Subroutines.' + subroutine
        package = __import__(subroutineName, fromlist=['Controller'], level=-1)
        startUp = package.Controller.StartUp()
        startUp.startUpTasks()
        if configFile[subroutine]['SV']:
            subroutineFrame = startUp.getSubroutineFrame()
            targetPanel.add(subroutineFrame)


    targetPanel.add(JAVX_SWING.Box.createVerticalGlue())

    return targetPanel

def closePsWindow():
    """Called by:
    
        """

    frameName = getBundleItem('Pattern Scripts')
    window = JMRI.util.JmriJFrame.getFrame(frameName)

    if window:
        updateWindowParams(window)
        window.setVisible(False)
        window.dispose()

    return

def getComponentByName(frameTitle, componentName):
    """
    Gets a frame by title.
    Searches a frame for a component by name.
    Uses crawler() to find a component in a frame.
    """

    global CRAWLER
    CRAWLER = []
    frame = JMRI.util.JmriJFrame.getFrame(frameTitle)

    crawler(frame)

    if len(CRAWLER) == 0:
        print(componentName + ' not found in ' + frameTitle)
        return

    for component in CRAWLER:
        if component.getName() == componentName:
            return component

    return

def crawler(frame):
    """Recursively returns all the components in a frame."""

    for component in frame.getComponents():
        CRAWLER.append(component)

        crawler(component)

    return

def openSystemConsole():

    console = APPS.SystemConsole.getConsole()
    console.setVisible(readConfigFile('Main Script')['CP']['OC'])

    return

def openOutputFrame(message):
    """
    The Script Output Window is used to display critical errors.
    Adds the message to the Script Output window.
    https://groups.io/g/jmriusers/message/33745
    https://groups.io/g/jmriusers/message/33747
    """

    bundle = JMRI.jmrit.jython.Bundle()
    frameName = bundle.handleGetMessage('TitleOutputFrame')
    frame = JMRI.util.JmriJFrame.getFrame(frameName)

    if not frame:
        JMRI.jmrit.jython.JythonWindow().actionPerformed(None)

    frame = JMRI.util.JmriJFrame.getFrame(frameName)

    global CRAWLER
    CRAWLER = []
    crawler(frame)
    for component in CRAWLER:
        if component.getClass() == JAVX_SWING.JTextArea:
           component.text += message + '\n'
           break

    return

def closeOutputFrame():

    bundle = JMRI.jmrit.jython.Bundle()
    frameName = bundle.handleGetMessage('TitleOutputFrame')
    frame = JMRI.util.JmriJFrame.getFrame(frameName)

    if frame:
        frame.setVisible(False)
        frame.dispose()

    return

def closeSubordinateWindows(level):
    """
    Close all but the top level windows.
    Called by:
    """

    console = APPS.Bundle().handleGetMessage('TitleConsole')
    patternScripts = getBundleItem('Pattern Scripts')
    trainsTable = JMRI.jmrit.operations.trains.Bundle().handleGetMessage('TitleTrainsTable')
    routesTable = JMRI.jmrit.operations.routes.Bundle().handleGetMessage('TitleRoutesTable')
    locationsTable = JMRI.jmrit.operations.locations.Bundle().handleGetMessage('TitleLocationsTable')

    if level == 1:
        keepTheseWindows = [console, 'PanelPro', patternScripts]

    if level == 2:
        keepTheseWindows = [console, 'PanelPro', patternScripts, locationsTable]

    if level == 3:
        keepTheseWindows = [console, 'PanelPro', patternScripts, routesTable, trainsTable, locationsTable]
    
    for frame in JMRI.util.JmriJFrame.getFrameList():
        if frame.getTitle() in keepTheseWindows:
            continue
        else:
            frame.setVisible(False)
            frame.dispose()

    return

def closeTopLevelWindows():

    console = APPS.Bundle().handleGetMessage('TitleConsole')
    patternScripts = getBundleItem('Pattern Scripts')    

    keepTheseWindows = [console, 'PanelPro', patternScripts]
    
    for frame in JMRI.util.JmriJFrame.getFrameList():
        if frame.getTitle() in keepTheseWindows:
            continue
        else:
            frame.setVisible(False)
            frame.dispose()

    return

def getPsButton():
    """
    Gets the Pattern Scripts button on the PanelPro frame.
    Called by:
    Listeners.PatternScriptsWindow.windowClosed
    Listeners.PatternScriptsWindow.windowOpened
    """

    buttonSpaceComponents = APPS.Apps.buttonSpace().getComponents()
    for component in buttonSpaceComponents:
        if component.getName() == 'psButton':
            return component
        else:
            return None

def closeSetCarsWindows():
    """
    Close all the Set Cars windows when the Pattern Scripts window is closed.
    Called by:
    MainScript.Controller.closePsWindow
    Listeners.PatternScriptsWindow.windowClosing
    """

    for frame in JMRI.util.JmriJFrame.getFrameList():
        if frame.getName() == 'setCarsWindow':
            frame.setVisible(False)
            frame.dispose()

    return

def closeOpsWindows(windowName):
    """
    Close all the windows of a certain name.
    Called by:
    MainScript.Controller.closePsWindow
    Listeners.PatternScriptsWindow.windowClosing
    controllerSetCarsForm.setRsButton
    """

    for frame in JMRI.util.JmriJFrame.getFrameList():
        if frame.getName() == windowName:
            frame.setVisible(False)
            frame.dispose()

    return

def updateWindowParams(window):
    """
    Setting JmriJFrame(True, True) has no effect that I can figure.
    Called by:
    MainScript.Controller.closePsWindow
    Listeners.PatternScriptsWindow.windowClosing
    """

    configPanel = readConfigFile()
    configPanel['Main Script']['CP'].update({'PH': window.getHeight()})
    configPanel['Main Script']['CP'].update({'PW': window.getWidth()})
    configPanel['Main Script']['CP'].update({'PX': window.getX()})
    configPanel['Main Script']['CP'].update({'PY': window.getY()})
    writeConfigFile(configPanel)

    return


"""Utility Methods"""


def resetBuiltTrains():
    """
    Resets all the trains that are built.
    """

    for train in TM.getTrainsByStatusList():
        if train.isBuilt():
            train.reset()

    return

def remoteCalls(call):
    """
    Applies 'call' to entries in ConfigFile()['Main Script']['CP']
    'call' is one of the remote calls in each subroutine RemoteCalls module.
    activatedCalls, deActivatedCalls, refreshCalls Etc.
    """

    cpItems = readConfigFile()['Main Script']['CP']

    # for item, value in cpItems.items():
    for item in cpItems:
        if 'Subroutines.' in item:
            try:
                package = __import__(item, fromlist=['RemoteCalls'], level=-1)
                getattr(package.RemoteCalls, call)()
            except ImportError:
                pass
                # print(item + ' not found')

        # package = __import__(xModule, globals(), locals(), fromlist=['RemoteCalls'], level=-1)
    return

def psLocale():
    """
    Dealers choice, both work.
    Called by:
    Bundle
    Translaters
    """

    return PM.getLocale().toString()
    # return unicode(PM.getLocale(), ENCODING)

def occuranceTally(listOfOccurances):
    """
    Tally the occurances of a word in a list and return a dictionary.
    Home grown version of collections.Counter.
    Called by:
    ModelEntities.getKernelTally
    ViewEntities.makeTextReportLocations
    o2o.ModelEntities
    """

    dict = {}
    while len(listOfOccurances):
        occurance = listOfOccurances[-1]
        tally = 0
        for i in xrange(len(listOfOccurances) - 1, -1, -1): # run list from bottom up
            if listOfOccurances[i] == occurance:
                tally += 1
                listOfOccurances.pop(i)
        dict[occurance] = tally

    return dict

def locationNameLookup(locationName):
    """
    A default location 'Unreported' is exported by Trainplayer for all RS not on a labeled track.
    This method returns the translated word for 'Unreported'.
    All other locations are passed through.
    """

    if locationName == 'Unreported':
        locationName = getBundleItem('Unreported')

    return locationName

def getAllDivisionNames():
    """
    JMRI sorts the list.
    Called by:
    Model.updatePatternLocation
    """

    divisionNames = []
    for item in DM.getDivisionsByNameList():
        divisionNames.append(unicode(item.getName(), ENCODING))

    return divisionNames

def getLocationNamesByDivision(divisionName):

    locationsByDivision = []

    if divisionName == None:
        for location in LM.getList():
            if not location.getDivisionName():
                locationsByDivision.append(location.getName())
    else:
        for location in LM.getList():
            if location.getDivisionName() == divisionName:
                locationsByDivision.append(location.getName())

    return locationsByDivision

def getDivisionForLocation(locationName):

    location = LM.getLocationByName(locationName)
    division = location.getDivision()
    if division:
        divisionName = division.getName()
    else:
        divisionName = ''

    return divisionName

def getAllLocationNames():
    """
    JMRI sorts the list, returns list of location names.
    Called by:
    o2o.Model.UpdateLocationsAndTracks
    PSE.getAllTrackIds
    Podel.updatePatternLocation
    Model.updateLocations
    ModelEntities.testSelectedItem
    o2oSubroutine.Model.UpdateLocationsAndTracks.addNewLocations
    """

    locationNames = []
    for item in LM.getLocationsByNameList():
        locationNames.append(unicode(item.getName(), ENCODING))

    return locationNames

def getAllTracks():
    """
    All track objects for all locations.
    Called by:
    Model.UpdateLocationsAndTracks
    ModelEntities.setNonSpurTrackLength
    Model.updatePatternLocation
    """

    trackList = []
    for location in LM.getList():
        trackList += location.getTracksByNameList(None)

    return trackList

def getRailroadName():
    """
    Returns either a standard or extended railroad name or the JMRI railroad name.
    """
    configFile = readConfigFile()
    OSU = JMRI.jmrit.operations.setup
    railroadName = unicode(OSU.Setup.getRailroadName(), ENCODING)
    
    if configFile['Main Script']['CP']['EH']:
        
        if configFile['Main Script']['LD']['RN']:
            railroadName = configFile['Main Script']['LD']['RN']
        if configFile['Main Script']['LD']['JN']:
            railroadName = configFile['Main Script']['LD']['JN']

    return railroadName


"""Formatting Methods"""


def validTime(epochTime=0):
    """
    Valid Time, get local time adjusted for time zone and dst.
    Called by:
    o2oSubroutine.ModelImport.TrainPlayerImporter.processFileHeaders
    o2oSubroutine.ModelWorkEvents.jmriManifestConversion.convertHeader
    PatternTracksSubroutine.ModelEntities.initializeReportHeader
    Nov 15, 2022 11:53 AM PST vs Valid 11/15/2022 11:54
    """

    year = getYear()
    time = getTime(epochTime)

    if JMRI.jmrit.operations.setup.Setup.is12hrFormatEnabled():
        return TIME.strftime('Valid %b %d, ' + year + ', %I:%M %p', time)
    else:
        return TIME.strftime('Valid %b %d, ' + year + ', %H:%M', time)

    # return TIME.strftime('%m/%d/%Y %I:%M', TIME.gmtime(epochTime - timeOffset))
    # return TIME.strftime('%a %b %d %Y %I:%M %p %Z', TIME.gmtime(epochTime - timeOffset))
    # return TIME.strftime('%b %d, ' + year + ' %I:%M %p %Z', TIME.gmtime(epochTime - timeOffset))

def timeStamp():
    """Returns the time in format: YYYY.MO.DY.24.MN.SC"""

    return TIME.strftime('%Y.%m.%d.%H.%M.%S', getTime())

def getTime(epochTime=0):

    if epochTime == 0:
        epochTime = TIME.time()

    if TIME.localtime(epochTime).tm_isdst and TIME.daylight: # If local dst and dst are both 1
        timeOffset = TIME.altzone
    else:
        timeOffset = TIME.timezone # in seconds

    return TIME.gmtime(epochTime - timeOffset)

def getYear():
    """Either the current year or the entry in settings: year modeled."""

    railroadYear = JMRI.jmrit.operations.setup.Setup.getYearModeled()
    if railroadYear:
        return railroadYear
    else:
        return TIME.strftime('%Y', TIME.gmtime(TIME.time()))

def convertJmriDateToEpoch(jmriTime):
    """
    Example: "date" : "2022-02-26T17:16:17.807+0000"
    Example: "date" : "1915-04-24T20:55:40.227+00:00"
    Called by:
    o2oSubroutine.ModelWorkEvents.jmriManifestConversion.convertHeader
    """
    try:
        epochTime = TIME.mktime(TIME.strptime(jmriTime, "%Y-%m-%dT%H:%M:%S.%f+0000"))
    except ValueError:
        pass
    try:
        epochTime = TIME.mktime(TIME.strptime(jmriTime, "%Y-%m-%dT%H:%M:%S.%f+00:00"))
    except ValueError:
        pass
    

    if TIME.localtime(epochTime).tm_isdst and TIME.daylight: # If local dst and dst are both 1
        epochTime -= TIME.altzone
    else:
        epochTime -= TIME.timezone # in seconds

    return epochTime

def formatText(item, length):
    """
    Truncate each item to its defined length in configFile.json and add a space at the end.
    Called by:
    PatternTracksSubroutine.ViewEntities.merge
    PatternTracksSubroutine.ViewEntities.loopThroughRs
    """

    if isinstance(item, bool): # Hazardous is a boolean
        item = 'HazMat'
    if len(item) < length:
        xItem = item.ljust(length)
    else:
        xItem = item[:length]

    return xItem + u' '

def getShortLoadType(car):
    """
    Replaces empty and load with E, L, or O for occupied.
    JMRI defines custom load type as empty but default load type as Empty, hence the 'or' statement.
    Load, Empty, Occupied and Unknown are translated by the bundle.
    Called by:
    ViewEntities.modifyTrackPatternReport
    ModelWorkEvent.o2oSwitchListConversion.parsePtRs
    ModelWorkEvents.jmriManifestConversion.parseRS
    """

    try:
        rs = CM.getByRoadAndNumber(car['road'], car['number']) # Pattern scripts nomenclature
    except:
        rs = CM.getByRoadAndNumber(car['road'], car['number']) # JMRI nomenclature

    lt =  getBundleItem('unknown').upper()[0]
    if rs.getLoadType() == 'empty' or rs.getLoadType() == 'Empty':
        lt = getBundleItem('empty').upper()[0]

    if rs.getLoadType() == 'load' or rs.getLoadType() == 'load':
        lt = getBundleItem('load').upper()[0]

    if rs.isCaboose() or rs.isPassenger():
        lt = getBundleItem('occupied').upper()[0]

    return lt
    # return 'L'

def makeReportItemWidthMatrix():
    """The attribute widths (AW) for each of the rolling stock attributes is defined in the report matrix (RM) of the config file."""

    reportMatrix = {}
    attributeWidths = readConfigFile('Patterns')['RM']['AW']

    for aKey, aValue in attributeWidths.items():
        reportMatrix[aKey] = aValue

    global REPORT_ITEM_WIDTH_MATRIX
    REPORT_ITEM_WIDTH_MATRIX = reportMatrix

    return


"""File Handling Methods"""


def makeBuildStatusFolder():
    """
    The buildStatus folder is created first so the log file can be written.
    Called by:
    MainScript.Controller
    """

    targetDirectory = OS_PATH.join(PROFILE_PATH, 'operations', 'buildstatus')
    if not JAVA_IO.File(targetDirectory).isDirectory():
        JAVA_IO.File(targetDirectory).mkdirs()

    return

def makeReportFolders():
    """
    Checks/creates the folders this plugin writes to.
    Used By:
    MainScript.Controller
    """

    opsDirectory = OS_PATH.join(PROFILE_PATH, 'operations')
    directories = ['csvManifests', 'csvSwitchLists', 'jsonManifests', 'switchLists', 'manifests']
    x = 0
    for directory in directories:
        targetDirectory = OS_PATH.join(opsDirectory, directory)
        if not JAVA_IO.File(targetDirectory).isDirectory():
            JAVA_IO.File(targetDirectory).mkdirs()
            _psLog.info('Directory created: ' + targetDirectory)
            x += 1

    if x == 0:
        _psLog.info('Destination folders check OK')
    else:
        _psLog.info(str(x) + 'Destination folders created')

    return

def genericReadReport(filePath):
    """
    try/except catches initial read of config file.
    Called by:
    Everything
    """

    try:
        ENCODING
    except UnboundLocalError:
        ENCODING = 'utf-8'

    with codecsOpen(filePath, 'r', encoding=ENCODING) as textWorkFile:
        genericReport = textWorkFile.read()

    return genericReport

def genericWriteReport(filePath, genericReport):
    """
    Called by:
    Everything
    """

    try:
        ENCODING
    except UnboundLocalError:
        ENCODING = 'utf-8'

    with codecsOpen(filePath, 'wb', encoding=ENCODING) as textWorkFile:
        textWorkFile.write(genericReport)

    return

def genericDisplayReport(genericReportPath):
    """
    Dealer's choice, the JMRI or Java version, well, maybe not.
    Called by:
    MainScript.Controller.logItemSelected
    MainScript.Controller.ecItemSelected
    PatternTracksSubroutine.View.trackPatternButton
    PatternTracksSubroutine.ViewSetCarsForm.switchListButton
    """

    targetFile = JAVA_IO.File(genericReportPath)
    JMRI.util.HelpUtil.openWindowsFile(targetFile)

    # JAVA_AWT.Desktop.getDesktop().edit(targetFile)
    # Windows 11 throws error with json file

    return

def loadJson(file):
    """
    Called by:
    Everything
    """

    return jsonLoadS(file)

def dumpJson(file):
    """
    Called by:
    Everything
    """

    return jsonDumpS(file, indent=2, sort_keys=True)


"""Configuration File Methods"""


def validateConfigFile():
    """Checks and corrects the configFile."""

    configFile = OS_PATH.join(PROFILE_PATH, 'operations', 'configFile.json')
# Does one exist?
    if not JAVA_IO.File(configFile).isFile():
        makeNewConfigFile()
# Is it the right version?
    validateConfigFileVersion()
# Are the current subroutines activated?
    activateCurrentSubroutines()
# Does it have all the needed components?
    validateConfigFileComponents()

    return

def validateConfigFileVersion():
    """
    Checks that the config file is the current version.
    Called by:
    OperationsPatternScripts.MainScript.Model
    """

    fileName = 'OPS.json'
    targetPath = OS_PATH.join(PLUGIN_ROOT, 'opsEntities', fileName)
    validConfigFile = loadJson(genericReadReport(targetPath))
    validVersion = validConfigFile['Main Script']['CP']['RV']
    currentVersion = readConfigFile('Main Script')['CP']['RV']

    if currentVersion == validVersion:
        _psLog.info('The configFile.json file is the correct version')
        return True
    else:
        makeNewConfigFile()

        _psLog.warning('configFile  .json version mismatch')
        return False

def validateConfigFileComponents():
    """Checks that each subroutine in the Subroutines folder has a configFile component."""

    configFile = readConfigFile()

    for subroutine in getSubroutineDirs():
        try:
            configFile[subroutine]
        except KeyError:
            chunkPath = OS_PATH.join(PLUGIN_ROOT, 'Subroutines', subroutine, 'config.json')
            configChunk = loadJson(genericReadReport(chunkPath))
            configFile[subroutine] = configChunk

    writeConfigFile(configFile)

    return

def activateCurrentSubroutines():
    """Checks that each active subroutine has a config file entry."""

    configFile = readConfigFile()

    for subroutine in getSubroutineDirs():
        configFile['Main Script']['CP']['Subroutines.' + subroutine] = True

    writeConfigFile(configFile)

    return

def deactivateSubroutines():
    """
    All the subroutines listed in the configFile are set to False.
    validateConfigFileComponents sets those subs in the Subroutines folder to true.
    """

    configFile = readConfigFile()
    cpItems = configFile['Main Script']['CP']
    for item, value in cpItems.items():
        if 'Subroutines.' in item:
            cpItems.update({item: False})

    configFile['Main Script']['CP'].update({'EH':False})

    writeConfigFile(configFile)

    return

def getSubroutineDirs():
    """Returns a list of subroutine names in the Subroutines directory."""

    subroutines = []

    subroutinePath = OS_PATH.join(PLUGIN_ROOT, 'Subroutines')
    dirContents = JAVA_IO.File(subroutinePath).list()

    for item in dirContents:
        dirPath = OS_PATH.join(PLUGIN_ROOT, 'Subroutines', item)
        if JAVA_IO.File(dirPath).isDirectory():
            subroutines.append(item)

    return subroutines

def mergeConfigFiles():
    """Implemented in v3"""
    return

def readConfigFile(subConfig=None):
    """
    tryConfigFile will return the config file if it's ok or a new one otherwise.
    Called by:
    Everything
    """

    configFile = checkConfigFile()

    if not subConfig:
        return configFile
    else:
        return configFile[subConfig]

def checkConfigFile():

    fileName = 'configFile.json'
    targetPath = OS_PATH.join(PROFILE_PATH, 'operations', fileName)

    try:
        loadJson(genericReadReport(targetPath))
    except:
        makeNewConfigFile()
        print('Exception at: PSE.checkConfigFile')
        print('Using new configFile')

    return loadJson(genericReadReport(targetPath))

def makeNewConfigFile():
    """
    Makes a composit ConfigFile.json from OPS.json and each of the subroutine json files.
    For every subroutine, the chunck of config file is named config.json.
    """

    fileName = 'OPS.json'
    targetPath = OS_PATH.join(PLUGIN_ROOT, 'opsEntities', fileName)
    configFile = loadJson(genericReadReport(targetPath))

    subroutines = getSubroutineDirs()
    for subroutine in subroutines:
        dirPath = OS_PATH.join(PLUGIN_ROOT, 'Subroutines', subroutine)
        if JAVA_IO.File(dirPath).isDirectory():
            chunkPath = OS_PATH.join(PLUGIN_ROOT, 'Subroutines', subroutine, 'config.json')
            configChunk = loadJson(genericReadReport(chunkPath))
            configFile[subroutine] = configChunk

    fileName = 'configFile.json'
    targetPath = OS_PATH.join(PROFILE_PATH, 'operations', fileName)
    targetFile = dumpJson(configFile)
    genericWriteReport(targetPath, targetFile)

    return

def tryConfigFile():
    """
    Try/except catches some user edit mistakes.
    Called by:
    PSE.readConfigFile
    """

    try:
        configFile = getConfigFile()
    except ValueError:
        writeNewConfigFile()
        configFile = getConfigFile()
        _psLog.warning('Defective configFile.json found, new file written')
    except IOError:
        writeNewConfigFile()
        configFile = getConfigFile()
        _psLog.warning('No configFile.json found, new file written')

    return configFile

def getConfigFile():
    """
    Called by:
    tryConfigFile
    """

    fileName = 'configFile.json'
    targetPath = OS_PATH.join(PROFILE_PATH, 'operations', fileName)

    return loadJson(genericReadReport(targetPath))

def writeConfigFile(configFile):
    """
    Called by:
    MainScript.Controller
    PSE.updateWindowParams
    PatternTracksSubroutine.Controller.StartUp.yardTrackOnlyCheckBox
    PatternTracksSubroutine.Model
    """

    fileName = 'configFile.json'
    targetPath = OS_PATH.join(PROFILE_PATH, 'operations', fileName)
    targetFile = dumpJson(configFile)
    genericWriteReport(targetPath, targetFile)

    return

def writeNewConfigFile():
    """
    Called by:
    PSE.tryConfigFile
    """

    targetDir = OS_PATH.join(PROFILE_PATH, 'operations')
    JAVA_IO.File(targetDir).mkdir()

    fileName = 'configFile.json'

    targetFile = OS_PATH.join(PLUGIN_ROOT, 'opsEntities', fileName)
    copyFrom = JAVA_IO.File(targetFile).toPath()

    targetFile = OS_PATH.join(PROFILE_PATH, 'operations', fileName)
    copyTo = JAVA_IO.File(targetFile).toPath()

    JAVA_NIO.Files.copy(copyFrom, copyTo, JAVA_NIO.StandardCopyOption.REPLACE_EXISTING)

    return

def deleteConfigFile():
    """
    Called by:
    MainScript.Controller.rsItemSelected
    """

    fileName = 'configFile.json'
    targetFile = OS_PATH.join(PROFILE_PATH, 'operations', fileName)
    JAVA_IO.File(targetFile).delete()

    return


"""Color Handling Methods"""


def getGenericColor(colorName):
    """
    Called by:
    PSE.getCarColor
    PSE.getLocoColor
    PSE.getAlertColor
    """

    colorPalette = readConfigFile('Main Script')['CD']

    r = colorPalette[colorName]["R"]
    g = colorPalette[colorName]["G"]
    b = colorPalette[colorName]["B"]
    a = colorPalette[colorName]["A"]

    return JAVA_AWT.Color(r, g, b, a)

def getColorA():
    """
    Try/Except is a bit of protection against bad edits.
    Called by:
    PatternTracksSubroutine.ViewSetCarsForm.MakeSetCarsEqptRows
    """

    try:
        colorName = readConfigFile('Main Script')['CD']['colorA']
        color = getGenericColor(colorName)
        return color
    except:
        print('Exception at: PSE.getColorA')
        _psLog.warning('colorA definition not found in configFile.json')
        return JAVA_AWT.Color(0, 0, 0, 0)

def getColorB():
    """
    Try/Except is a bit of protection against bad edits.
    Called by:
    PatternTracksSubroutine.ViewSetCarsForm.MakeSetCarsEqptRows
    """

    try:
        colorName = readConfigFile('Main Script')['CD']['colorB']
        color = getGenericColor(colorName)
        return color
    except:
        print('Exception at: PSE.getColorB')
        _psLog.warning('colorB definition not found in configFile.json')
        return JAVA_AWT.Color(0, 0, 0, 0)

def getColorC():
    """
    Try/Except is a bit of protection against bad edits.
    Called by:
    PatternTracksSubroutine.ViewSetCarsForm.MakeSetCarsEqptRows
    """

    try:
        colorName = readConfigFile('Main Script')['CD']['colorC']
        color = getGenericColor(colorName)
        return color
    except:
        print('Exception at: PSE.getColorC')
        _psLog.warning('colorC definition not found in configFile.json')
        return JAVA_AWT.Color(0, 0, 0, 0)


"""Translation Methods"""

def getBundleItem(item):
    """
    Centralized method for translation.
    Retrieves the item from the bundle.
    """

    return unicode(BUNDLE[item], ENCODING)

def translateMessageFormat():
    """
    The messageFormat is in the locale's language, it has to be hashed to the plugin fields.
    Dealers choice, J_BUNDLE.ROAD or SB.handleGetMessage('road').
    Called by:
    PatternTracksSubroutine.ViewEntities.loopThroughRs
    PatternTracksSubroutine.ViewSetCarsForm.MakeSetCarsEqptRows
    """

    rosetta = {}
#Common
    rosetta[J_BUNDLE.ROAD] = 'road'
    rosetta[J_BUNDLE.NUMBER] = 'number'
    rosetta[J_BUNDLE.TYPE] = 'carType'
    rosetta[J_BUNDLE.LENGTH] = 'length'
    rosetta[J_BUNDLE.WEIGHT] = 'weight'
    rosetta[J_BUNDLE.COLOR] = 'color'
    rosetta[J_BUNDLE.DIVISION] = 'division'
    rosetta[J_BUNDLE.LOCATION] = 'location'
    rosetta[J_BUNDLE.TRACK] = 'track'
    rosetta[J_BUNDLE.DESTINATION] = 'destination'
    rosetta[J_BUNDLE.DEST_TRACK] = 'dest&Track'
    rosetta[J_BUNDLE.OWNER] = 'owner'
    rosetta[J_BUNDLE.COMMENT] = 'comment'
    rosetta[J_BUNDLE.TAB] = 'tab'
    rosetta[J_BUNDLE.TAB2] = 'tab2'
    rosetta[J_BUNDLE.TAB3] = 'tab3'
# Cars
    rosetta[J_BUNDLE.LOAD] = 'load'
    rosetta[J_BUNDLE.LOAD_TYPE] = 'loadType'
    rosetta[J_BUNDLE.HAZARDOUS] = 'hazardous'
    rosetta[J_BUNDLE.KERNEL] = 'kernel'
    rosetta[J_BUNDLE.KERNEL_SIZE] = 'kernelSize'
    rosetta[J_BUNDLE.FINAL_DEST] = 'finalDest'
    rosetta[J_BUNDLE.FINAL_DEST_TRACK] = 'fd&Track'
    rosetta[J_BUNDLE.DROP_COMMENT] = 'setOutMsg'
    rosetta[J_BUNDLE.PICKUP_COMMENT] = 'pickupMsg'
    rosetta[J_BUNDLE.RWE] = 'rwe'
    # rosetta[J_BUNDLE.RWL] = 'rwl'
# Locos
    rosetta[J_BUNDLE.MODEL] = 'model'
    rosetta[J_BUNDLE.CONSIST] = 'consist'
    rosetta[J_BUNDLE.DCC_ADDRESS] = 'dccAddress'
# Unique to this plugin
    rosetta['onTrain'] = 'onTrain'
    rosetta['setTo'] = 'setTo'
    rosetta['puso'] = 'puso'
    rosetta[' '] = ' '

    return rosetta
