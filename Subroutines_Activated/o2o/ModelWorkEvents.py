# coding=utf-8
# © 2023 Greg Ritacco

"""
Creates the TrainPlayer JMRI Report - o2o Workevents.csv file from either PatternTracksSubroutine or BuiltTrainExport
"""

from opsEntities import PSE
from opsEntities import TRE

SCRIPT_NAME = '{}.{}'.format(PSE.SCRIPT_DIR, __name__)
SCRIPT_REV = 20231001

_psLog = PSE.LOGGING.getLogger('OPS.o2o.ModelWorkEvents')

def o2oWorkEvents(manifest):
    """
    Makes an o2o workevents list from a standardized manifest/work event list.
    manifest is a string from the json file.
    """

    _psLog.debug('o2oWorkEvents')
# Header
    o2oWorkEvents = 'HN,' + manifest[u'railroad'].replace('\n', ';') + '\n'
    o2oWorkEvents += 'HT,' + manifest[u'userName'] + '\n'
    o2oWorkEvents += 'HD,' + manifest[u'description'] + '\n'
    o2oWorkEvents += 'HV,{}\n'.format(PSE.convertIsoToValidTime(manifest[u'date']))
    o2oWorkEvents += 'WT,' + str(len(manifest[u'locations'])) + '\n'
# Body
    for i, location in enumerate(manifest['locations'], start=1):
        o2oWorkEvents += u'WE,{},{}\n'.format(str(i), location[u'userName'])
        for loco in location['engines']['add']:
            o2oWorkEvents += u'PL,{}\n'.format(_makeLine(loco))
        for loco in location['engines']['remove']:
            o2oWorkEvents += u'SL,{}\n'.format(_makeLine(loco))
        for car in location['cars']['add']:
            o2oWorkEvents += u'PC,{}\n'.format(_makeLine(car))
        for car in location['cars']['remove']:
            o2oWorkEvents += u'SC,{}\n'.format(_makeLine(car))
        
    return o2oWorkEvents

def _makeLine(rs):
    """
    Helper function to make the rs line for o2oWorkEvents.
    format: TP ID, Road, Number, Car Type, L/E/O, Load or Model, From, To
    """

    try: # Cars
        loadName = rs[u'load']
        lt = TRE.getShortLoadType(rs)
    except: # Locos
        loadName = rs[u'model']
        lt = PSE.getBundleItem(u'Occupied').upper()[0]

    ID = rs['road'] + ' ' + rs['number']
    pu = rs['location'][u'userName'] + ';' + rs['location']['track'][u'userName']
    so = rs['destination'][u'userName'] + ';' + rs['destination']['track'][u'userName']

    line = u'{},{},{},{},{},{},{},{}'.format(ID, rs[u'road'], rs[u'number'], rs[u'carType'], lt, loadName, pu, so)

    return line


def convertOpsSwitchList():
    """
    Mini controller.
    Converts the Patterns switch list-OPS.json into an o2o work events file.
    Called by: Listeners - PROPERTY_CHANGE_EVENT.propertyName == 'patternsSwitchList' 
    """

    opsSwitchList = opsSwitchListConversion()
    if not opsSwitchList.validate():
        return
    
    tpWorkEventsList = opsSwitchList.convert()
    # o2oWorkEvents(tpWorkEventsList).makeList()

    print(SCRIPT_NAME + '.convertOpsSwitchList ' + str(SCRIPT_REV))

    return


class opsSwitchListConversion:
    """
    Converts a switch list generated by the Patterns subroutine into an TrainPlayer/Quick Keys compatable work events list.
    """

    def __init__(self):

        # self.inputFileName = '{}.json'.format(PSE.readConfigFile()['Main Script']['US']['OSL'])
        self.inputFileName = PSE.readConfigFile()['Main Script']['US']['OSL'].format('OPS', 'json')
        self.inputTargetPath = PSE.OS_PATH.join(PSE.PROFILE_PATH, 'operations', 'jsonManifests', self.inputFileName)

        self.opsSwitchList = {}
        self.cars = []
        self.locos = []

        self.tpWorkEventsList = {}

        self.validationResult = True

        return
    
    def validate(self):

        if not PSE.JAVA_IO.File(self.inputTargetPath).isFile():
            print('ALERT: not found-switch list-OPS.json')
            self.validationResult = False

        return self.validationResult

    def convert(self):
        """
        Mini controller.
        """

        self.switchListGetter()
        self.makeTpWorkEventsList()
        # self.addTracksToList()

        return self.tpWorkEventsList
    
    def switchListGetter(self):

        opsSwitchList = PSE.genericReadReport(self.inputTargetPath)
        self.opsSwitchList = PSE.loadJson(opsSwitchList)

        return
    
    def makeTpWorkEventsList(self):

        self.tpWorkEventsList['railroadName'] = self.opsSwitchList['railroad']
        self.tpWorkEventsList['railroadDescription'] = self.opsSwitchList['description']
        self.tpWorkEventsList['trainName'] = self.opsSwitchList['userName']
        self.tpWorkEventsList['trainDescription'] = self.opsSwitchList['userName']
        self.tpWorkEventsList['date'] = self.opsSwitchList['date']
        self.tpWorkEventsList['locations'] = self.opsSwitchList['locations']


        print(self.tpWorkEventsList)
        return

    def addTracksToList(self):

        tracks = []

        for track in self.opsSwitchList['tracks']:
            trackItems = {}
            self.cars = []
            self.locos = []
            for car in track['cars']:
                parsed = self.parsePtRs(car)
                parsed['puso'] = 'SC'
                self.cars.append(parsed)
            for loco in track['locos']:
                parsed = self.parsePtRs(loco)
                parsed['puso'] = 'SL'
                self.locos.append(parsed)
            trackItems['cars'] = self.cars
            trackItems['locos'] = self.locos
            tracks.append(trackItems)

        self.tpWorkEventsList['locations'][0].update({'tracks':tracks})

        return

    def parsePtRs(self, rs):
        """
        The load field is either Load(car) or Model(loco).
        Pattern scripts have only one location.
        Location and Destination are the same.
        """

        parsedRS = {}
        parsedRS['road'] = rs[PSE.SB.handleGetMessage('Road')]
        parsedRS['number'] = rs[PSE.SB.handleGetMessage('Number')]
        parsedRS['carType'] = rs[PSE.SB.handleGetMessage('Type')]
        parsedRS['destination'] = rs[PSE.SB.handleGetMessage('Location')]
        parsedRS['location'] = rs[PSE.SB.handleGetMessage('Location')]
        parsedRS['track'] = rs[PSE.SB.handleGetMessage('Track')]
        try:
            parsedRS['loadType'] = PSE.getShortLoadType(rs)
            parsedRS['load'] = rs[PSE.SB.handleGetMessage('Load')]
        except:
            parsedRS['load'] = rs[PSE.SB.handleGetMessage('Model')]

        if self.parseSetTo(rs['setTo']) == PSE.getBundleItem('Hold'):
            parsedSetTo = rs[PSE.SB.handleGetMessage('Track')]
        else:
            parsedSetTo = self.parseSetTo(rs['setTo'])
        parsedRS['setTo'] = parsedSetTo

        return parsedRS

    def parseSetTo(self, setTo):
        """
        format: [Freight House]   
        """

        return setTo[1:-1].split(']')[0]
