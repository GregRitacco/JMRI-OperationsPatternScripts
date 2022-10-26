# coding=utf-8
# © 2021, 2022 Greg Ritacco

from opsEntities import PSE
import apps
import jmri.jmrit
import jmri.util.swing

SCRIPT_NAME = 'OperationsPatternScripts.o2oSubroutine.ModelEntities'
SCRIPT_REV = 20220101

_psLog = PSE.LOGGING.getLogger('OPS.o2o.ModelEntities')

def tpDirectoryExists():
    """Checks for the Reports folder in TraipPlayer."""

    tpDirectory = PSE.OS_PATH.join(PSE.JMRI.util.FileUtil.getHomePath(), 'AppData', 'Roaming', 'TrainPlayer', 'Reports')

    if PSE.JAVA_IO.File(tpDirectory).isDirectory():
        _psLog.info('TrainPlayer destination directory OK')
        return True
    else:
        _psLog.warning('TrainPlayer Reports destination directory not found')
        print('TrainPlayer Reports destination directory not found')
        return

def selectCarTypes(industries):
    """For each track in industries, first deselect all the RS types,
        then select just the RS types used by that track, leaving unused types  deselected.
        Used by:
        Model.NewLocationsAndTracks.addCarTypesToSpurs
        Model.UpdateLocationsAndTracks.addCarTypesToSpurs
        """
# Deselect all type names for each industry track
    locationList = []
    for id, industry in industries.items():
        locationList.append(industry['location'] + ';' + industry['track'])

    locationList = list(set(locationList))
    for location in locationList:
        locTrack = location.split(';')
        location = PSE.LM.getLocationByName(locTrack[0])
        track = location.getTrackByName(locTrack[1], None)
        for typeName in track.getTypeNames():
            track.deleteTypeName(typeName)

# Select only those types used at the industry.
    for id, industry in industries.items():
        track = PSE.LM.getLocationByName(industry['location']).getTrackByName(industry['track'], None)
        track.addTypeName(industry['type'])

    return





def makeNewSchedule(id, industry):
    """Used by:
        Model.NewLocationsAndTracks.newSchedules
        Model.UpdateLocationsAndTracks
        """

    scheduleLineItem = industry['schedule']
    schedule = PSE.SM.newSchedule(scheduleLineItem[0])
    scheduleItem = schedule.addItem(scheduleLineItem[1])
    scheduleItem.setReceiveLoadName(scheduleLineItem[2])
    scheduleItem.setShipLoadName(scheduleLineItem[3])

    return

def makeNewTrack(trackId, trackData):
    """Set spur length to 'spaces' from TP.
        Deselect all types for spur tracks.
        Used by:
        Model.NewLocationsAndTracks.newLocations
        Model.UpdateLocationsAndTracks.addNewTracks
        """

    _psLog.debug('makeNewTrack')

    o2oConfig = PSE.readConfigFile('o2o')
    jmriTrackType = o2oConfig['TR'][trackData['type']]

    location = PSE.LM.getLocationByName(trackData['location'])
    location.addTrack(trackData['track'], jmriTrackType)

    setTrackAttribs(trackData)
    
    return

def setTrackAttribs(trackData):
    """Mini controller to set the attributes for each JMRI track type.
        Used by:
        makeNewTrack
        Model.UpdateLocationsAndTracks.updateTrackType
        """

    if trackData['type'] == 'industry':
        setTrackTypeIndustry(trackData)

    if trackData['type'] == 'interchange':
        setTrackTypeInterchange(trackData)

    if trackData['type'] == 'staging':
        setTrackTypeStaging(trackData)

    if trackData['type'] == 'class yard':
        setTrackTypeClassYard(trackData)

    if trackData['type'] == 'XO reserved':
        setTrackTypeXoReserved(trackData)

    return

def setTrackTypeIndustry(trackData):
    """Settings for TP 'industry' track types.
        Used by:
        makeNewTrack
        """

    location = PSE.LM.getLocationByName(trackData['location'])
    track = location.getTrackByName(trackData['track'], None)

    track.setSchedule(PSE.SM.getScheduleByName(trackData['label']))

    return track

def setTrackTypeInterchange(trackData):
    """Settings for TP 'interchange' track types.
        Used by:
        makeNewTrack
        """

    return

def setTrackTypeStaging(trackData):
    """Settings for TP 'staging' track types.
        Used by:
        makeNewTrack
        """

    o2oConfig =  PSE.readConfigFile('o2o')

    location = PSE.LM.getLocationByName(trackData['location'])
    track = location.getTrackByName(trackData['track'], None)

    track.setAddCustomLoadsAnySpurEnabled(o2oConfig['SM']['SCL'])
    track.setRemoveCustomLoadsEnabled(o2oConfig['SM']['RCL'])
    track.setLoadEmptyEnabled(o2oConfig['SM']['LEE'])

    return track

def setTrackTypeClassYard(trackData):
    """Settings for TP 'class yard' track types.
        Used by:
        makeNewTrack
        """

    return

def setTrackTypeXoReserved(trackData):
    """Settings for TP 'XO reserved' track types.
        XO tracks are spurs with all train directions turned off.
        All car types are selected.
        Used by:
        makeNewTrack
        """

    track = setTrackTypeIndustry(trackData)
    track.setTrainDirections(0)
    for type in track.getTypeNames():
        track.addTypeName(type)

    return track

def getWorkEvents():
    """Gets the o2o work events file
        Used by:
        ModelWorkEvents.ConvertPtMergedForm.getWorkEvents
        ModelWorkEvents.o2oWorkEvents.getWorkEvents
        """

    reportName = PSE.BUNDLE['o2o Work Events']
    fileName = reportName + '.json'
    targetPath = PSE.OS_PATH.join(PSE.PROFILE_PATH, 'operations', 'jsonManifests', fileName)

    workEventList = PSE.genericReadReport(targetPath)
    jsonFile = PSE.loadJson(workEventList)

    return jsonFile

def getTpExport(fileName):
    """Generic file getter, fileName includes .txt
        Used by:
        ModelImport.TrainPlayerImporter.getTpReportFiles
        """

    targetPath = PSE.OS_PATH.join(PSE.JMRI.util.FileUtil.getHomePath(), 'AppData', 'Roaming', 'TrainPlayer', 'Reports', fileName)

    if PSE.JAVA_IO.File(targetPath).isFile():
        tpExport = PSE.genericReadReport(targetPath).split('\n')
        return tpExport
    else:
        return False

def parseCarId(carId):
    """Splits a TP car id into a JMRI road name and number
        Used by:
        ModelImport.TrainPlayerImporter.getAllTpRoads
        ModelNew.NewRollingStock.makeTpRollingStockData
        ModelNew.NewRollingStock.newCars
        ModelNew.NewRollingStock.newLocos
        """

    rsRoad = ''
    rsNumber = ''

    for character in carId:
        if character.isspace() or character == '-':
            continue
        if character.isdecimal():
            rsNumber += character
        else:
            rsRoad += character

    return rsRoad, rsNumber

def getSetToLocationAndTrack(locationName, trackName):
    """Used by:
        ModelNew.NewRollingStock.newCars
        ModelNew.NewRollingStock.newLocos
        """

    try:
        location = PSE.LM.getLocationByName(locationName)
        track = location.getTrackByName(trackName, None)
        return location, track
    except:
        print('Location and track not found: ', locationName, trackName)
        return None, None

def closeTroublesomeWindows():
    """Close all the 'Troublesome' windows when the New JMRI Railroad button is pressed.
        Used by:
        o2oSubroutine.Model.newJmriRailroad
        o2oSubroutine.Model.updateJmriRailroad
        """

    for frameName in PSE.JMRI.util.JmriJFrame.getFrameList():
        if not 'JmriJFrame' in frameName.__str__():
            frameName.dispose()

    return

def getTpRailroadData():
    """Add error handling"""

    tpRailroad = []

    reportName = 'tpRailroadData'
    fileName = reportName + '.json'
    targetPath = PSE.OS_PATH.join(PSE.PROFILE_PATH, 'operations', fileName)

    try:
        PSE.JAVA_IO.File(targetPath).isFile()
        _psLog.info('tpRailroadData.json OK')
    except:
        _psLog.warning('tpRailroadData.json not found')
        return

    report = PSE.genericReadReport(targetPath)
    tpRailroad = PSE.loadJson(report)

    return tpRailroad
