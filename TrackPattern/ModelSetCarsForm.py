# coding=utf-8
# © 2021 Greg Ritacco

import jmri
import java.awt
import logging
from codecs import open as codecsOpen
from json import loads as jsonLoads, dumps as jsonDumps

from psEntities import MainScriptEntities
from TrackPattern import ModelEntities
from TrackPattern import ExportToTrainPlayer

scriptName = 'OperationsPatternScripts.TrackPattern.ModelSetCarsForm'
scriptRev = 20220101
psLog = logging.getLogger('PS.TP.ModelSetCarsForm')

def testValidityOfForm(setCarsForm, textBoxEntry):

    psLog.debug('testValidityOfForm')

    locoCount = len(setCarsForm['locations'][0]['tracks'][0]['locos'])
    carCount = len(setCarsForm['locations'][0]['tracks'][0]['cars'])

    if len(textBoxEntry) == locoCount + carCount:
        return True
    else:
        psLog.critical('mismatched input list and car roster lengths')
        return False

def setRsToTrack(setCarsForm, textBoxEntry):

    psLog.debug('setRsToTrack')

    trackData = []
    ignoreTrackLength = MainScriptEntities.readConfigFile('TP')['PI']

    location = setCarsForm['locations'][0]['locationName']
    locationObject = MainScriptEntities._lm.getLocationByName(unicode(location, MainScriptEntities.setEncoding()))
    allTracksAtLoc = ModelEntities.getTracksByLocation(location, None)
    fromTrack = unicode(setCarsForm['locations'][0]['tracks'][0]['trackName'], MainScriptEntities.setEncoding())

    userInputList = []
    for userInput in textBoxEntry:
        userInputList.append(unicode(userInput.getText(), MainScriptEntities.setEncoding()))

    i = 0
    setCount = 0

    for loco in setCarsForm['locations'][0]['tracks'][0]['locos']:

        toTrack = fromTrack
        if userInputList[i]:
            toTrack = userInputList[i]

        locoObject = MainScriptEntities._em.newRS(loco['Road'], loco['Number'])
        toTrackObject = locationObject.getTrackByName(unicode(toTrack, MainScriptEntities.setEncoding()), None)

        if not unicode(toTrack, MainScriptEntities.setEncoding()) in allTracksAtLoc: # Catches invalid track typed into box
            return

        if toTrack == fromTrack:
            return

        if ignoreTrackLength:
            trackLength = toTrackObject.getLength()
            toTrackObject.setLength(9999)
            setResult = locoObject.setLocation(locationObject, toTrackObject)
            toTrackObject.setLength(trackLength)
        else:
            setResult = locoObject.setLocation(locationObject, toTrackObject)

        if setResult == 'okay':
            setCount += 1

        i += 1
    jmri.jmrit.operations.rollingstock.engines.EngineManagerXml.save()

    for car in setCarsForm['locations'][0]['tracks'][0]['cars']:

        toTrack = fromTrack
        if userInputList[i]:
            toTrack = userInputList[i]

        carObject = MainScriptEntities._cm.newRS(car['Road'], car['Number'])
        toTrackObject = locationObject.getTrackByName(unicode(toTrack, MainScriptEntities.setEncoding()), None)

        if not unicode(toTrack, MainScriptEntities.setEncoding()) in allTracksAtLoc: # Catches invalid track typed into box
            return

        if toTrack == fromTrack:
            return

        if ignoreTrackLength:
            trackLength = toTrackObject.getLength()
            toTrackObject.setLength(9999)
            setResult = carObject.setLocation(locationObject, toTrackObject)
            toTrackObject.setLength(trackLength)
        else:
            setResult = carObject.setLocation(locationObject, toTrackObject)

        if setResult == 'okay':
            setCount += 1
            if toTrackObject.getTrackType() == 'Spur':
                carObject.setMoves(carObject.getMoves() + 1)
                carObject.updateLoad()
                applySchedule(toTrackObject, carObject)
                # applyReturnWhen(carObject)

        i += 1
    jmri.jmrit.operations.rollingstock.cars.CarManagerXml.save()

    psLog.info('Rolling stock count: ' + str(setCount) + ', processed from track: ' + fromTrack)

    return

def applySchedule(toTrackObject, carObject):
    '''If the to-track is a spur, try to set the load/empty requirement for the track'''

    location = MainScriptEntities.readConfigFile('TP')['PL']
    schedule = getSchedule(location, toTrackObject.getName())
    if schedule:
        carType = carObject.getTypeName()
        carObject.setLoadName(schedule.getItemByType(carType).getShipLoadName())
        carObject.setDestination(schedule.getItemByType(carType).getDestination(), schedule.getItemByType(carType).getDestinationTrack(), True) # force set dest
        schedule.getItemByType(carType).setHits(schedule.getItemByType(carType).getHits() + 1)

        return

def getSchedule(locationString, trackString):
    '''Returns a schedule if there is one'''

    track = MainScriptEntities._lm.getLocationByName(locationString).getTrackByName(trackString, 'Spur')

    if track:
        schedule = MainScriptEntities._sm.getScheduleByName(track.getScheduleName())

        return schedule

    return

def exportSetCarsFormToTp(setCarsForm, textBoxEntry):

    psLog.debug('exportSetCarsFormToTp')

    ExportToTrainPlayer.CheckTpDestination().directoryExists()

    jmriExport = ExportToTrainPlayer.ExportJmriLocations()
    locationList = jmriExport.makeLocationList()
    jmriExport.toTrainPlayer(locationList)

    tpSwitchList = ExportToTrainPlayer.TrackPatternTranslationToTp()
    modifiedSwitchList = tpSwitchList.modifySwitchList(setCarsForm, textBoxEntry)
    appendedTpSwitchList = tpSwitchList.appendSwitchList(modifiedSwitchList)
    tpWorkEventProcessor = ExportToTrainPlayer.ProcessWorkEventList()
    tpWorkEventProcessor.writeTpWorkEventListAsJson(appendedTpSwitchList)
    tpSwitchListHeader = tpWorkEventProcessor.makeTpHeader(appendedTpSwitchList)
    tpSwitchListLocations = tpWorkEventProcessor.makeTpLocations(appendedTpSwitchList)
    ExportToTrainPlayer.WriteWorkEventListToTp(tpSwitchListHeader + tpSwitchListLocations).asCsv()

    return

def makeLocationDict(setCarsForm, textBoxEntry):
    '''Replaces car['Set to'] = [ ] with either [Hold] or ["some other valid track"]'''

    psLog.debug('makeLocationDict')

    trackName = setCarsForm['locations'][0]['tracks'][0]['trackName']
    location = setCarsForm['locations'][0]['locationName']
    allTracksAtLoc = ModelEntities.getTracksByLocation(location, None)

    userInputList = []
    for userInput in textBoxEntry:
        userInputList.append(unicode(userInput.getText(), MainScriptEntities.setEncoding()))

    longestTrackString = 6 # 6 is the length of [Hold]
    for track in MainScriptEntities.readConfigFile('TP')['PT']: # Pattern Tracks
        if len(track) > longestTrackString:
            longestTrackString = len(track)

    i = 0
    locoList = []
    for loco in setCarsForm['locations'][0]['tracks'][0]['locos']:
        setTrack = u'Hold'
        userInput = unicode(userInputList[i], MainScriptEntities.setEncoding())
        if userInput in allTracksAtLoc and userInput != trackName:
            setTrack = userInput
        loco['Set to'] = ModelEntities.formatText('[' + setTrack + ']', longestTrackString + 2)
        locoList.append(loco)
        i += 1

    carList = []
    for car in setCarsForm['locations'][0]['tracks'][0]['cars']:
        setTrack = u'Hold'
        userInput = unicode(userInputList[i], MainScriptEntities.setEncoding())
        if userInput in allTracksAtLoc and userInput != trackName:
            setTrack = userInput
        car['Set to'] = ModelEntities.formatText('[' + setTrack + ']', longestTrackString + 2)
        carList.append(car)
        i += 1

    trackDetails = {}
    trackDetails['trackName'] = trackName
    trackDetails['length'] = 1
    trackDetails['locos'] = locoList
    trackDetails['cars'] = carList

    locationDict = {}
    locationDict['locationName'] = location
    locationDict['tracks'] = [trackDetails]

    return locationDict

# def writeTpSwitchListFromJson(switchListName):
#     '''Writes the switch list for TrainPlayer'''
#
#     psLog.debug('writeTpSwitchListFromJson')
#
#     ExportToTrainPlayer.CheckTpDestination().directoryExists()
#     ExportToTrainPlayer.JmriLocationsToTrainPlayer().exportLocations()
#     tpWorkEventList = ExportToTrainPlayer.WorkEventListForTrainPlayer(switchListName).readFromFile()
#     if not tpWorkEventList:
#         psLog.critical('No work event list read in')
#         return
#     tpCsvWorkEventList = ExportToTrainPlayer.CsvListFromFile(tpWorkEventList).makeList()
#     ExportToTrainPlayer.writeWorkEventListToTp(tpCsvWorkEventList).writeAsCsv()
#
#     return

# def applyReturnWhen(carObject):
#
#     carLoadType = carObject.getLoadType()
#
#     if carObject.getReturnWhenLoadedDestName() and carLoadType == 'Load':
#         location, track = parseDestination(carObject.getReturnWhenLoadedDestName())
#         carObject.setFinalDestination(location)
#         carObject.setFinalDestinationTrack(track)
#
#     if carObject.getReturnWhenEmptyDestName() and carLoadType == 'Empty':
#         location, track = parseDestination(carObject.getReturnWhenEmptyDestName())
#         carObject.setFinalDestination(location)
#         carObject.setFinalDestinationTrack(track)
#
#     return

# def parseDestination(destination):
#     '''destination(track)'''
#
#     locationName, locationTrack = destination.split('(', 1)
#
#     location = MainScriptEntities._lm.getLocationByName(locationName)
#     track = location.getTrackByName(locationTrack[:-1], None)
#
#     return location, track

# def applySchedule(carObject, scheduleObject=None):
#     '''Mini "controller" to plug in additional schedule methods.
#     The schedule is applied when setting into a spur.
#     Increment move count only when set to a spur.'''
#
#     if not scheduleObject:
#
#         return
#
#     if (MainScriptEntities.readConfigFile('TP')['AS']): # apply schedule flag
#         applyLoadRubric(carObject, scheduleObject)
#         applyFdRubric(carObject, scheduleObject)
#         carObject.setMoves(carObject.getMoves() + 1)
#
#     return

# def applyLoadRubric(carObject, scheduleObject=None):
#     '''Apply loads by schedule, RWE/RWL, custom L/E, then default'''
#
#     carType = carObject.getTypeName()
# # Toggle the default loads if used
#     if (carObject.getLoadName() == _defaultLoadLoad):
#         carObject.setLoadName(MainScriptEntities._defaultLoadEmpty)
#     elif (carObject.getLoadName() == MainScriptEntities._defaultLoadEmpty):
#         carObject.setLoadName(MainScriptEntities._defaultLoadLoad)
# # Toggle the custom loads
#     try: # first try to apply the schedule
#         carObject.setLoadName(scheduleObject.getItemByType(carType).getShipLoadName())
#         scheduleObject.getItemByType(carType).setHits(scheduleObject.getItemByType(carType).getHits() + 1)
#     except:
#         try: # apply values from RWE or RWL
#             if (carObject.getLoadType() == 'Empty'): # toggle the load
#                 carObject.setLoadName(carObject.getReturnWhenLoadedLoadName())
#             else:
#                 carObject.setLoadName(carObject.getReturnWhenEmptyLoadName())
#         except:
#             try: # apply values from custom empty
#                 if (carObject.getLoadType() == 'Empty'): # toggle the load
#                     carObject.setLoadName(MainScriptEntities._carTypeByLoadDict.get(carType))
#                 else:
#                     carObject.setLoadName(MainScriptEntities._carTypeByEmptyDict.get(carType))
#             except: # when all else fails, apply the default loads
#                 if (carObject.getLoadType() == 'Empty'): # toggle the load
#                     carObject.setLoadName(MainScriptEntities._defaultLoadLoad)
#                 else:
#                     carObject.setLoadName(MainScriptEntities._defaultLoadEmpty)
#
#     return
#
# def applyFdRubric(carObject, scheduleObject=None):
#     '''For spurs only, sets the values for the cars destination and track from the schedule or RWE/RWL'''
#
#     patternIgnore = MainScriptEntities.readConfigFile('TP')['PI']
#     carType = carObject.getTypeName()
#     carObject.setFinalDestination(None)
#     carObject.setFinalDestinationTrack(None)
#
#     try: # first try to apply the schedule
#         trySchedule = carObject.setDestination(scheduleObject.getItemByType(carType).getDestination(), scheduleObject.getItemByType(carType).getDestinationTrack())
#         if (trySchedule.startswith('rolling')):
#             trySchedule = carObject.setDestination(scheduleObject.getItemByType(carType).getDestination(), scheduleObject.getItemByType(carType).getDestinationTrack(), patternIgnore)
#             if (trySchedule != 'okay'):
#                 psLog.warning('Schedule destination not applied: ' + trySchedule)
#         elif (trySchedule != 'okay'):
#             psLog.warning('Schedule destination not applied: ' + trySchedule)
#     except:
#         if (carObject.getLoadType() == 'Load'): # load has already been toggled
#             applyRWL = carObject.setDestination(carObject.getReturnWhenLoadedDestination(), carObject.getReturnWhenLoadedDestTrack(), patternIgnore)
#             if (applyRWL != 'okay'):
#                 psLog.info('RWL destination not applied: ' + applyRWL)
#         if (carObject.getLoadType() == 'Empty'): # load has already been toggled
#             applyRWE = carObject.setDestination(carObject.getReturnWhenEmptyDestination(), carObject.getReturnWhenEmptyDestTrack(), patternIgnore)
#             if (applyRWE != 'okay'):
#                 psLog.info('RWE destination not applied: ' + applyRWE)
#
#     return
