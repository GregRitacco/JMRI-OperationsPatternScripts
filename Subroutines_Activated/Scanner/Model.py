# coding=utf-8
# © 2023 Greg Ritacco

"""
Scanner subroutine.
"""

from opsEntities import PSE
from opsEntities import Manifest

SCRIPT_NAME = PSE.SCRIPT_DIR + '.' + __name__
SCRIPT_REV = 20230901

_psLog = PSE.LOGGING.getLogger('OPS.SC.Model')

""" Actions called by the plugin listeners """

def resetConfigFileItems():

    return

def initializeSubroutine():

    scannerComboUpdater()
    
    return

def resetSubroutine():

    return

def refreshSubroutine():

    configFile = PSE.readConfigFile()

    scannerComboUpdater(configFile['Scanner']['SI'])

    return

def opsAction1(message=None):
    """
    Generic action called by a plugin listener.
    """

    if message == 'TrainBuilt':
        train = PSE.getNewestTrain()

        manifest = PSE.getTrainManifest(train)
        manifest = extendJmriManifestJson(manifest)
        PSE.saveManifest(manifest, train)

    return

def opsAction2(message=None):
    """
    Writes a new text manifest from the extended manifest.
    """

    if message == 'TrainBuilt':
        train = PSE.getNewestTrain()
        manifest = PSE.getTrainManifest(train)

        textManifest = Manifest.opsTextManifest(manifest)
        manifestName = 'train ({}).txt'.format(train.toString())
        manifestPath = PSE.OS_PATH.join(PSE.PROFILE_PATH, 'operations', 'manifests', manifestName)
        PSE.genericWriteReport(manifestPath, textManifest)

        # Modify the JMRI switch lists here

    return

def opsAction3(message=None):
    """
    Generic action called by a plugin listener.
    """

    return

""" Routines specific to this subroutine """

def extendJmriManifestJson(manifest):

    isSequenceHash, sequenceHash = PSE.getSequenceHash()

    for location in manifest['locations']:
        for car in location['cars']['add']:
            carID = car['road'] + ' ' + car['number']
            sequence = sequenceHash['cars'][carID]
            car['sequence'] = sequence

        for car in location['cars']['remove']:
            carID = car['road'] + ' ' + car['number']
            sequence = sequenceHash['cars'][carID]
            car['sequence'] = sequence

    for location in manifest['locations']:
        cars = location['cars']['add']
        cars.sort(key=lambda row: row['sequence'])

        cars = location['cars']['remove']
        cars.sort(key=lambda row: row['sequence'])

    return manifest

def recordSelection(comboBox):
    """
    Write the combo box selected item to the configfile.
    """

    configFile = PSE.readConfigFile()
    configFile['Scanner'].update({'SI':comboBox.getSelectedItem()})
    PSE.writeConfigFile(configFile)

    return

def validateSequenceData():
    """
    Checks that rsSequenceData.json exists.
    If not then create one.
    """
    
    sequenceFilePath = PSE.OS_PATH.join(PSE.PROFILE_PATH, 'operations', 'rsSequenceData.json')
    if not PSE.JAVA_IO.File(sequenceFilePath).isFile():
        initialSequenceHash = getInitialSequenceHash()
        PSE.genericWriteReport(sequenceFilePath, PSE.dumpJson(initialSequenceHash))

    return

def modifyTrainManifest(train):
    """
    Modifies the existing JMRI manifest, sorts by sequence number.
    """
    
    Manifest.extendJmriManifest(train)

    textManifest = Manifest.opsTextManifest(train)
    manifestName = 'train (' + train.toString() + ').txt'
    manifestPath = PSE.OS_PATH.join(PSE.PROFILE_PATH, 'operations', 'manifests', manifestName)
    PSE.genericWriteReport(manifestPath, textManifest)

    return

def addSequenceToManifest(train):
    """
    Adds an attribute called 'sequence' and it's value to an existing json manifest.
    """

    isSequenceHash, sequenceHash = PSE.getSequenceHash()

    trainName = 'train-' + train + '.json'
    manifestPath = PSE.OS_PATH.join(PSE.PROFILE_PATH, 'operations', 'jsonManifests', trainName)
    manifest = PSE.loadJson(PSE.genericReadReport(manifestPath))

    for location in manifest['locations']:
        for car in location['cars']['add']:
            carID = car['road'] + ' ' + car['number']
            sequence = sequenceHash['cars'][carID]
            car['sequence'] = sequence
        for car in location['cars']['remove']:
            carID = car['road'] + ' ' + car['number']
            sequence = sequenceHash['cars'][carID]
            car['sequence'] = sequence

    PSE.genericWriteReport(manifestPath, PSE.dumpJson(manifest))

    return

def resequenceManifest(train):
    """
    Resequences an existing json manifest by its sequence value.
    """

    trainName = 'train-' + train + '.json'
    manifestPath = PSE.OS_PATH.join(PSE.PROFILE_PATH, 'operations', 'jsonManifests', trainName)
    manifest = PSE.loadJson(PSE.genericReadReport(manifestPath))

    for location in manifest['locations']:
        cars = location['cars']['add']
        cars.sort(key=lambda row: row['sequence'])

        cars = location['cars']['remove']
        cars.sort(key=lambda row: row['sequence'])

    PSE.genericWriteReport(manifestPath, PSE.dumpJson(manifest))

    return

def getInitialSequenceHash():

    scannerHash = {}
    locoHash = {}
    carHash = {}

    for loco in PSE.EM.getList():
        id = loco.getRoadName() + ' ' + loco.getNumber()
        locoHash.update({id:8000})

    for car in PSE.CM.getList():
        id =  car.getRoadName() + ' ' + car.getNumber()
        carHash.update({id:8000})
                        
    scannerHash.update({'locos':locoHash})
    scannerHash.update({'cars':carHash})

    return scannerHash

def _updateScannerList():
    """
    Gets the file names in the designated scanner path.
    """

    configFile = PSE.readConfigFile()
    scannerPath = configFile['Scanner']['US']['SP']
    dirContents = PSE.JAVA_IO.File(scannerPath).list()

    pulldownList = []
    for file in dirContents:
        pulldownList.append(file.split('.')[0])

    return pulldownList

def scannerComboUpdater(selected=None):
    """
    Updates the contents of the scanners combo box.
    """

    _psLog.debug('scannerComboUpdater')

    frameName = PSE.getBundleItem('Pattern Scripts')
    frame = PSE.JMRI.util.JmriJFrame.getFrame(frameName)
    component = PSE.getComponentByName(frame, 'sScanner')
    component.removeAllItems()

    pulldownList = _updateScannerList()
    for scanName in pulldownList:
        component.addItem(scanName)

    component.setSelectedItem(selected)
    
    return

def getScannerReportPath():
    """
    Writes the name of the selected scanner report to the config file.
    """

    configFile = PSE.readConfigFile()
    scannerPath = configFile['Scanner']['US']['SP']

    frameName = PSE.getBundleItem('Pattern Scripts')
    frame = PSE.JMRI.util.JmriJFrame.getFrame(frameName)
    component = PSE.getComponentByName(frame, 'sScanner')

    itemSelected = component.getSelectedItem()
    itemSelected = itemSelected + '.txt'
    scannerReportPath = PSE.OS_PATH.join(scannerPath, itemSelected)

    return scannerReportPath

def validateScanReport(scannerReportPath):

    _psLog.debug('validateScanReport')

    return True

def applyScanReport(scannerReportPath):
    """
    Assign a sequence number to the RS in the selected scan report.
    """

    _psLog.debug('applyScanReport')

    sequenceFilePath = PSE.OS_PATH.join(PSE.PROFILE_PATH, 'operations', 'rsSequenceData.json')
    sequenceFile = PSE.loadJson(PSE.genericReadReport(sequenceFilePath))

    locoSequence = 8001
    carSequence = 8001

    scannerReport = PSE.genericReadReport(scannerReportPath)
    splitReport = scannerReport.split('\n')
    splitReport.pop(-1) # Pop off the empty line at the end.
    header = splitReport.pop(0).split(',')

    scannerName = header[0]
    direction = header[1].upper()[0:1]
    if direction == 'W':
        splitReport.reverse()

    print('applyScanReport')

    for item in splitReport:
        rs = item.split(',')
        if rs[1].startswith('ET'):
            continue
        elif rs[1].startswith('E'):
            sequenceFile['locos'].update({rs[0]:locoSequence})
            locoSequence += 1
        else:
            sequenceFile['cars'].update({rs[0]:carSequence})
            carSequence += 1

    PSE.genericWriteReport(sequenceFilePath, PSE.dumpJson(sequenceFile))

    _psLog.debug('applyScanReport for scanner: ' + scannerName)
    print('applyScanReport for scanner: ' + scannerName)

    return