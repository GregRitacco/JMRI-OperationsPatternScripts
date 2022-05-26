# coding=utf-8
# © 2021, 2022 Greg Ritacco

import jmri

from codecs import open as codecsOpen
from json import loads as jsonLoads, dumps as jsonDumps
from xml.etree import ElementTree as ET

from psEntities import PatternScriptEntities

SCRIPT_NAME = 'OperationsPatternScripts.TrackPattern.ModelEntities'
SCRIPT_REV = 20220101

def testSelectedItem(selectedItem):
    """Catches user edit of locations"""

    allLocations = PatternScriptEntities.getAllLocations() #String list
    if selectedItem in allLocations:
        return selectedItem
    else:
        return allLocations[0]

def getAllTracksForLocation(location):
    """Sets all tracks to false"""

    jmriTrackList = PatternScriptEntities.LM.getLocationByName(location).getTracksByNameList(None)
    trackDict = {}
    for track in jmriTrackList:
        trackDict[unicode(track.getName(), PatternScriptEntities.ENCODING)] = False

    return trackDict

def initializeConfigFile():
    """initialize or reinitialize the pattern tracks part of the config file
    on first use, reset, or edit of a location name
    """

    newConfigFile = PatternScriptEntities.readConfigFile()
    subConfigfile = newConfigFile['PT']
    allLocations  = getAllLocations()
    subConfigfile.update({'AL': allLocations})
    subConfigfile.update({'PL': allLocations[0]})
    subConfigfile.update({'PT': makeInitialTrackList(allLocations[0])})
    newConfigFile.update({'PT': subConfigfile})

    return newConfigFile

def getTracksByLocation(trackType):

    patternLocation = PatternScriptEntities.readConfigFile('PT')['PL']
    allTracksList = []
    try: # Catch on the fly user edit of config file error
        for track in PatternScriptEntities.LM.getLocationByName(patternLocation).getTracksByNameList(trackType):
            allTracksList.append(unicode(track.getName(), PatternScriptEntities.ENCODING))
        return allTracksList
    except AttributeError:
        return allTracksList

def updateTrackCheckBoxes(trackCheckBoxes):
    """Returns a dictionary of track names and their check box status"""

    dict = {}
    for item in trackCheckBoxes:
        dict[unicode(item.text, PatternScriptEntities.ENCODING)] = item.selected

    return dict

def getGenericTrackDetails(locationName, trackName):
    """The loco and car lists are sorted at this level, used to make the JSON file"""

    genericTrackDetails = {}
    genericTrackDetails['trackName'] = trackName
    genericTrackDetails['length'] =  PatternScriptEntities.LM.getLocationByName(locationName).getTrackByName(trackName, None).getLength()
    genericTrackDetails['locos'] = sortLocoList(getLocoListForTrack(trackName))
    genericTrackDetails['cars'] = sortCarList(getCarListForTrack(trackName))

    return genericTrackDetails

def sortLocoList(locoList):
    """backupConfigFile() is a bit of user edit protection
    Sort order of PatternScriptEntities.readConfigFile('PT')['SL'] is top down"""

    sortLocos = PatternScriptEntities.readConfigFile('PT')['SL']
    for sortKey in sortLocos:
        locoList.sort(key=lambda row: row[sortKey])

    PatternScriptEntities.backupConfigFile()
    return locoList

def getRsOnTrains():
    """Make a list of all rolling stock that are on built trains"""

    builtTrainList = []
    for train in PatternScriptEntities.TM.getTrainsByStatusList():
        if train.isBuilt():
            builtTrainList.append(train)

    listOfAssignedRs = []
    for train in builtTrainList:
        listOfAssignedRs += PatternScriptEntities.CM.getByTrainList(train)
        listOfAssignedRs += PatternScriptEntities.EM.getByTrainList(train)

    return listOfAssignedRs

def getLocoListForTrack(track):
    """Creates a generic locomotive list for a track, used to make the JSON file"""

    location = PatternScriptEntities.readConfigFile('PT')['PL']
    locoList = getLocoObjects(location, track)

    return [getDetailsForLocoAsDict(loco) for loco in locoList]

def getLocoObjects(location, track):

    locoList = []
    allLocos = PatternScriptEntities.EM.getByModelList()

    return [loco for loco in allLocos if loco.getLocationName() == location and loco.getTrackName() == track]

def getDetailsForLocoAsDict(locoObject):
    """backupConfigFile() is a bit of user edit protection
    Mimics jmri.jmrit.operations.setup.Setup.getEngineAttributes()
    [u'Road', u'Number', u'Type', u'Model', u'Length', u'Weight', u'Consist',
    u'Owner', u'Track', u'Location', u'Destination', u'Comment']
    """

    listOfAssignedRs = getRsOnTrains()
    locoDetailDict = {}

    locoDetailDict[u'Road'] = locoObject.getRoadName()
    locoDetailDict[u'Number'] = locoObject.getNumber()
    locoDetailDict[u'Type'] = locoObject.getTypeName()
    locoDetailDict[u'Model'] = locoObject.getModel()
    locoDetailDict[u'Length'] = locoObject.getLength()
    locoDetailDict[u'Weight'] = locoObject.getWeightTons()
    try:
        locoDetailDict[u'Consist'] = locoObject.getConsist().getName()
    except:
        locoDetailDict[u'Consist'] = 'Single'
    locoDetailDict[u'Owner'] = str(locoObject.getOwner())
    locoDetailDict[u'Track'] = locoObject.getTrackName()
    locoDetailDict[u'Location'] = locoObject.getLocation().getName()
    locoDetailDict[u'Destination'] = locoObject.getDestinationName()
    locoDetailDict[u'Comment'] = locoObject.getComment()
# Not part of JMRI engine attributes
    if locoObject in listOfAssignedRs: # Flag to mark if RS is on a built train
        locoDetailDict[u'On Train'] = True
    else:
        locoDetailDict[u'On Train'] = False
    locoDetailDict[u'Set to'] = '[  ] '
    locoDetailDict[u'PUSO'] = u'SL'
    locoDetailDict[u'Load'] = u'O'
    locoDetailDict[u'FD&Track'] = PatternScriptEntities.readConfigFile('PT')['DS']
    locoDetailDict[u' '] = u' ' # Catches KeyError - empty box added to getDropEngineMessageFormat

    PatternScriptEntities.backupConfigFile()
    return locoDetailDict

def sortCarList(carList):
    """backupConfigFile() is a bit of user edit protection
    Sort order of PatternScriptEntities.readConfigFile('PT')['SC'] is top down"""

    sortCars = PatternScriptEntities.readConfigFile('PT')['SC']
    for sortKey in sortCars:
        carList.sort(key=lambda row: row[sortKey])

    PatternScriptEntities.backupConfigFile()
    return carList

def getCarListForTrack(track):
    """A list of car attributes as a dictionary"""

    location = PatternScriptEntities.readConfigFile('PT')['PL']
    carList = getCarObjects(location, track)

    return [getDetailsForCarAsDict(car) for car in carList]

def getCarObjects(location, track):

    allCars = PatternScriptEntities.CM.getByIdList()

    return [car for car in allCars if car.getLocationName() == location and car.getTrackName() == track]

def getDetailsForCarAsDict(carObject):
    """backupConfigFile() is a bit of user edit protection
    Mimics jmri.jmrit.operations.setup.Setup.getCarAttributes()
    [u'Road', u'Number', u'Type', u'Length', u'Weight', u'Load', u'Load Type',
    u'Hazardous', u'Color', u'Kernel', u'Kernel Size', u'Owner', u'Track',
    u'Location', u'Destination', u'Dest&Track', u'Final Dest', u'FD&Track',
    u'Comment', u'SetOut Msg', u'PickUp Msg', u'RWE']
    """

    fdStandIn = PatternScriptEntities.readConfigFile('PT')

    listOfAssignedRs = getRsOnTrains()
    carDetailDict = {}

    carDetailDict[u'Road'] = carObject.getRoadName()
    carDetailDict[u'Number'] = carObject.getNumber()
    carDetailDict[u'Type'] = carObject.getTypeName()
    carDetailDict[u'Length'] = carObject.getLength()
    carDetailDict[u'Weight'] = carObject.getWeightTons()
    if carObject.isCaboose() or carObject.isPassenger():
        carDetailDict[u'Load'] = u'O'
    else:
        carDetailDict[u'Load'] = carObject.getLoadName()
    carDetailDict[u'Load Type'] = carObject.getLoadType()
    carDetailDict[u'Hazardous'] = carObject.isHazardous()
    carDetailDict[u'Color'] = carObject.getColor()
    carDetailDict[u'Kernel'] = carObject.getKernelName()
    allCarObjects =  PatternScriptEntities.CM.getByIdList()
    for car in allCarObjects:
        i = 0
        if (car.getKernelName() == carObject.getKernelName()):
            i += 1
    carDetailDict[u'Kernel Size'] = str(i)
    carDetailDict[u'Owner'] = carObject.getOwner()
    carDetailDict[u'Track'] = carObject.getTrackName()
    carDetailDict[u'Location'] = carObject.getLocationName()
    if not (carObject.getDestinationName()):
        carDetailDict[u'Destination'] = fdStandIn['DS']
        carDetailDict[u'Dest&Track'] = fdStandIn['DT']
    else:
        carDetailDict[u'Destination'] = carObject.getDestinationName()
        carDetailDict[u'Dest&Track'] = carObject.getDestinationName() \
                                     + ', ' + carObject.getDestinationTrackName()
    if not (carObject.getFinalDestinationName()):
        carDetailDict[u'Final Dest'] = fdStandIn['FD']
        carDetailDict[u'FD&Track'] = fdStandIn['FT']
    else:
        carDetailDict[u'Final Dest'] = carObject.getFinalDestinationName()
        carDetailDict[u'FD&Track'] = carObject.getFinalDestinationName() \
                                   + ', ' + carObject.getFinalDestinationTrackName()
    carDetailDict[u'Comment'] = carObject.getComment()
    trackId =  PatternScriptEntities.LM.getLocationByName(carObject.getLocationName()).getTrackById(carObject.getTrackId())
    carDetailDict[u'SetOut Msg'] = trackId.getCommentSetout()
    carDetailDict[u'PickUp Msg'] = trackId.getCommentPickup()
    carDetailDict[u'RWE'] = carObject.getReturnWhenEmptyDestinationName()
# Not part of JMRI car attributes
    if carObject in listOfAssignedRs: # Flag to mark if RS is on a built train
        carDetailDict[u'On Train'] = True
    else:
        carDetailDict[u'On Train'] = False
    carDetailDict[u'Set to'] = '[  ] '
    carDetailDict[u'PUSO'] = u'SC'
    carDetailDict[u' '] = u' ' # Catches KeyError - empty box added to getLocalSwitchListMessageFormat

    PatternScriptEntities.backupConfigFile()
    return carDetailDict

def makeGenericHeader():
    """A generic header info for any switch list, used to make the JSON file"""

    listHeader = {}
    listHeader['railroad'] = unicode(jmri.jmrit.operations.setup.Setup.getRailroadName(), PatternScriptEntities.ENCODING)
    listHeader['trainName'] = u'Train Name Placeholder'
    listHeader['trainDescription'] = u'Train Description Placeholder'
    listHeader['trainComment'] = u'Train Comment Placeholder'
    listHeader['date'] = unicode(PatternScriptEntities.timeStamp(), PatternScriptEntities.ENCODING)
    listHeader['locations'] = []

    return listHeader

def writeWorkEventListAsJson(switchList):
    """The generic switch list is written as a json"""

    switchListName = switchList['trainDescription']
    jsonCopyTo = jmri.util.FileUtil.getProfilePath() \
               + 'operations\\jsonManifests\\' + switchListName + '.json'
    jsonObject = jsonDumps(switchList, indent=2, sort_keys=True)
    with codecsOpen(jsonCopyTo, 'wb', encoding=PatternScriptEntities.ENCODING) as jsonWorkFile:
        jsonWorkFile.write(jsonObject)

    return switchListName

def readJsonWorkEventList(workEventName):

    jsonCopyFrom = jmri.util.FileUtil.getProfilePath() \
                 + 'operations\\jsonManifests\\' + workEventName + '.json'
    with codecsOpen(jsonCopyFrom, 'r', encoding=PatternScriptEntities.ENCODING) as jsonWorkFile:
        jsonEventList = jsonWorkFile.read()
    textWorkEventList = jsonLoads(jsonEventList)

    return textWorkEventList

# def writeTextSwitchList(fileName, textSwitchList):
#
#     textCopyTo = jmri.util.FileUtil.getProfilePath() + 'operations\\switchLists\\' + fileName + '.txt'
#     with codecsOpen(textCopyTo, 'wb', encoding=PatternScriptEntities.ENCODING) as textWorkFile:
#         textWorkFile.write(textSwitchList)
#
#     return

def makeInitialTrackList(location):

    trackDict = {}
    for track in PatternScriptEntities.LM.getLocationByName(location).getTracksByNameList(None):
        trackDict[unicode(track, PatternScriptEntities.ENCODING)] = False

    return trackDict

def makeCsvSwitchlist(trackPattern):
    # CSV writer does not support utf-8

    csvSwitchList = u'Operator,Description,Parameters\n' \
                    u'RT,Report Type,' + trackPattern['trainDescription'] + '\n' \
                    u'RN,Railroad Name,' + trackPattern['railroad'] + '\n' \
                    u'LN,Location Name,' + trackPattern['locations'][0]['locationName'] + '\n' \
                    u'PRNTR,Printer Name,\n' \
                    u'YPC,Yard Pattern Comment,' + trackPattern['trainComment'] + '\n' \
                    u'VT,Valid,' + trackPattern['date'] + '\n'
    for track in trackPattern['locations'][0]['tracks']: # There is only one location
        csvSwitchList += u'TN,Track name,' + unicode(track['trackName'], PatternScriptEntities.ENCODING) + '\n'
        for loco in track['locos']:
            csvSwitchList +=  loco['Set to'] + ',' \
                            + loco['PUSO'] + ',' \
                            + loco['Road'] + ',' \
                            + loco['Number'] + ',' \
                            + loco['Type'] + ',' \
                            + loco['Model'] + ',' \
                            + loco['Length'] + ',' \
                            + loco['Weight'] + ',' \
                            + loco['Consist'] + ',' \
                            + loco['Owner'] + ',' \
                            + loco['Track'] + ',' \
                            + loco['Location'] + ',' \
                            + loco['Destination'] + ',' \
                            + loco['Comment'] + ',' \
                            + loco['Load'] + ',' \
                            + loco['FD&Track'] + ',' \
                            + '\n'
        for car in track['cars']:
            csvSwitchList +=  car['Set to'] + ',' \
                            + car['PUSO'] + ',' \
                            + car['Road'] + ',' \
                            + car['Number'] + ',' \
                            + car['Type'] + ',' \
                            + car['Length'] + ',' \
                            + car['Weight'] + ',' \
                            + car['Load'] + ',' \
                            + car['Track'] + ',' \
                            + car['FD&Track'] + ',' \
                            + car['Load Type'] + ',' \
                            + str(car['Hazardous']) + ',' \
                            + car['Color'] + ',' \
                            + car['Kernel'] + ',' \
                            + car['Kernel Size'] + ',' \
                            + car['Owner'] + ',' \
                            + car['Location'] + ',' \
                            + car['Destination'] + ',' \
                            + car['Dest&Track'] + ',' \
                            + car['Final Dest'] + ',' \
                            + car['Comment'] + ',' \
                            + car['SetOut Msg'] + ',' \
                            + car['PickUp Msg'] + ',' \
                            + car['RWE'] \
                            + '\n'

    return csvSwitchList

def appendJsonBody(trainPlayerSwitchList):

    jsonCopyFrom = jmri.util.FileUtil.getProfilePath() \
                 + 'operations\\jsonManifests\\TrainPlayerSwitchlist.json'
    with codecsOpen(jsonCopyFrom, 'r', encoding=PatternScriptEntities.ENCODING) as jsonWorkFile:
        switchList = jsonWorkFile.read()
    jsonSwitchList = jsonLoads(switchList)
    jTemp = jsonSwitchList['locations']
    jTemp.append(trainPlayerSwitchList)
    jsonSwitchList['locations'] = jTemp

    jsonCopyTo = jmri.util.FileUtil.getProfilePath() \
               + 'operations\\jsonManifests\\TrainPlayerSwitchlist.json'
    jsonObject = jsonDumps(jsonSwitchList, indent=2, sort_keys=True)
    with codecsOpen(jsonCopyTo, 'wb', encoding=PatternScriptEntities.ENCODING) as jsonWorkFile:
        jsonWorkFile.write(jsonObject)

    return
