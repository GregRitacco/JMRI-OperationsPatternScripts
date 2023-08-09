# coding=utf-8
# © 2023 Greg Ritacco

"""
Patterns
"""

from opsEntities import PSE
from Subroutines.Patterns import ModelEntities

SCRIPT_NAME = PSE.SCRIPT_DIR + '.' + __name__
SCRIPT_REV = 20230201


_psLog = PSE.LOGGING.getLogger('OPS.PT.Model')

def insertStandins(trackPattern):
    """
    Substitutes in standins from the config file.
    """

    standins = PSE.readConfigFile('Patterns')['RM']

    tracks = trackPattern['tracks']
    for track in tracks:
        for loco in track['locos']:
            destStandin, fdStandin = getStandins(loco, standins)
            loco.update({'destination': destStandin})

        for car in track['cars']:
            destStandin, fdStandin = getStandins(car, standins)
            car.update({'destination': destStandin})
            car.update({'finalDest': fdStandin})
            shortLoadType = PSE.getShortLoadType(car)
            car.update({'loadType': shortLoadType})

    return trackPattern

def getStandins(rs, standins):
    """
    Replaces null destination and fd with the standin from the configFile
    Called by:
    insertStandins
    """

    destStandin = rs['destination']
    if not rs['destination']:
        destStandin = standins['DS']

    try: # No FD for locos
        fdStandin = rs['finalDest']
        if not rs['finalDest']:
            fdStandin = standins['FD']
    except:
        fdStandin = standins['FD']

    return destStandin, fdStandin

def resetConfigFileItems():
    """
    Called from PSE.remoteCalls('resetCalls')
    """

    configFile = PSE.readConfigFile()

    configFile['Patterns'].update({'AD':[]})
    configFile['Patterns'].update({'PD':''})

    configFile['Patterns'].update({'AL':[]})
    configFile['Patterns'].update({'PL':''})

    configFile['Patterns'].update({'PT':{}})
    configFile['Patterns'].update({'PA':False})

    PSE.writeConfigFile(configFile)

    return

def updateConfigFile(controls):
    """
    Updates the Patterns part of the config file
    Called by:
    Controller.StartUp.trackPatternButton
    Controller.StartUp.setCarsButton
    """

    _psLog.debug('updateConfigFile')

    configFile = PSE.readConfigFile()
    configFile['Patterns'].update({"PL": controls[1].getSelectedItem()})
    configFile['Patterns'].update({"PA": controls[2].selected})

    PSE.writeConfigFile(configFile)

    return controls

def makeTrackPattern(selectedTracks):
    """
    Mini controller.
    """

    patternReport = makeReportHeader()
    patternReport['tracks'] = makeReportTracks(selectedTracks)

    return patternReport

def makeReportHeader():

    configFile = PSE.readConfigFile()

    reportHeader = {}
    reportHeader['railroadName'] = PSE.getRailroadName()
    reportHeader['railroadDescription'] = configFile['Patterns']['RD']
    reportHeader['trainName'] = configFile['Patterns']['TN']
    reportHeader['trainDescription'] = configFile['Patterns']['TD']
    reportHeader['trainComment'] = configFile['Patterns']['TC']
    reportHeader['division'] = configFile['Patterns']['PD']
    reportHeader['date'] = unicode(PSE.validTime(), PSE.ENCODING)
    reportHeader['location'] = configFile['Patterns']['PL']

    return reportHeader

def makeReportTracks(selectedTracks):
    """
    Tracks is a list of dictionaries.
    """

    return ModelEntities.getDetailsForTracks(selectedTracks)

def writePatternReport(trackPattern):
    """
    Writes the track pattern report as a json file.
    Called by:
    Controller.StartUp.patternReportButton
    """

    fileName = PSE.getBundleItem('ops-pattern-report') + '.json'    
    targetPath = PSE.OS_PATH.join(PSE.PROFILE_PATH, 'operations', 'jsonManifests', fileName)

    trackPatternReport = PSE.dumpJson(trackPattern)
    PSE.genericWriteReport(targetPath, trackPatternReport)

    return

def resetWorkList():
    """
    The worklist is reset when the Set Cars button is pressed.
    """

    workList = makeReportHeader()
    workList['tracks'] = []

    fileName = PSE.getBundleItem('ops-work-list') + '.json'
    targetPath = PSE.OS_PATH.join(PSE.PROFILE_PATH, 'operations', 'jsonManifests', fileName)
    workList = PSE.dumpJson(workList)
    PSE.genericWriteReport(targetPath, workList)

    return

def appendWorkList(mergedForm):










    tracks = mergedForm['track']

    fileName = PSE.getBundleItem('ops-work-list') + '.json'    
    targetPath = PSE.OS_PATH.join(PSE.PROFILE_PATH, 'operations', 'jsonManifests', fileName)
    currentWorkList = PSE.jsonLoadS(PSE.genericReadReport(targetPath))

    currentWorkList['tracks'].append(tracks)
    currentWorkList = PSE.dumpJson(currentWorkList)

    PSE.genericWriteReport(targetPath, currentWorkList)

    return

def divisionComboBox(selectedItem):
    """
    Updates the config file based on changes to divisions.
    """

    _psLog.debug('divisionComboBox')

    configFile = PSE.readConfigFile()

    selectedItem = str(selectedItem)
    configFile['Patterns'].update({'PD': selectedItem})
    configFile['Patterns'].update({'PL': None})

    PSE.writeConfigFile(configFile)

    return

def locationComboBox(selectedItem):
    """
    """

    _psLog.debug('locationComboBox')

    configFile = PSE.readConfigFile()

    selectedItem = str(selectedItem)
    configFile['Patterns'].update({'PL': selectedItem})

    PSE.writeConfigFile(configFile)

    return
