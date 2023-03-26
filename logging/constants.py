class Immutable(type):

    def __call__(*args):
        raise Exception("You can't create instance of immutable object")

    def __setattr__(*args):
        raise Exception("You can't modify immutable object")


class UUIDS(object):

    __metaclass__ = Immutable

    DATA_TO_DEVICE = "0000fff6-0000-1000-8000-00805f9b34fb"
    #"FFF6"
    DATA_FROM_DEVICE = "0000fff7-0000-1000-8000-00805f9b34fb"
    #"FFF7"


class RESPONSES(object):

    __metaclass__ = Immutable

    #from 3.1 Set Time
    SET_TIME_OK = b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x01'
    SET_TIME_ERROR = b'\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x81'

    #from 3.2 Get Time
    GET_TIME_HEADER = b'\x41' # follows the payload
    GET_TIME_ERROR = b'\xc1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\xc1'

    #from 3.3 Set user personal information
    SET_USERINFO_OK = b'\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x02'
    SET_USERINGO_ERROR = b'\x82\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x82'

    #from 3.4 Get user personal information
    GET_USERINFO_HEADER = b'\x42' # follows the payload
    GET_USERINFO_ERROR = b'\xc2\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\xc2'

    #from 3.5 Get heart rate breathing storage data
    GET_HEARTRATE_HEADER = b'\x17'# follows the payload
    GET_HEARTRATE_LAST = b'\x17\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x16'

    #from 3.6 Get out of bed? Meaning bed time
    GET_BEDTIME_HEADER = b'\x14' # follows the payload
    GET_BEDTIME_LAST = b'\x14\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x13'
    
    #from 3.6bis rollover data
    GET_ROLLOVER_HEADER = b'\x15' #follows the payload
    GET_ROLLOVER_LAST = b'\x15\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x14'
    
    #from 3.7 set device ID code
    SET_DEVICEID_OK = b'\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x05'
    SET_DEVICEID_ERROR = b'\x85\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x85' 

    #from 3.8 real time heart rate and breathing mode control
    GET_REALTIME_HEARTBREATH_HEADER = b'\x11' # follows the payload
    GET_REALTIME_HEARTBREATH_OK = b'\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x11'
    GET_REALTIME_HEARTBREATH_ERROR = b'\xc1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\xc1'

    #from 3.9 restore facory sleep settings
    RESTORE_FACTORY_OK = b'\x12\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x12'
    RESTORE_FACTORY_ERROR = b'\x92\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x92'

    #from 3.10 read device power
    GET_POWER_HEADER = b'\x13'
    GET_POWER_ERROR = b'\x93\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x93'

    #from 3.11 MAC address
    GET_MACADDR_HEADER = b'\x22'
    GET_MACADDR_ERROR = b'\xa2\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\xa2'

    #from 3.12 read the firmware version number
    GET_FIRMVER_HEADER = b'\27'
    GET_FIRMVER_ERROR = b'\xa7\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\xa7'

    #from 3.13 mcu soft reset
    SOFTRESET_OK = b'\x2e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x2E'
    SOFTRESET_ERROR = b'\xae\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\xae'

    #from 3.14
    # not added because firmware upgrade is not documented
    # and info is not consistent (the error and success message are equal)

    # from 3.15 set device name
    SET_DEVICENAME_OK = b'\x3D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x3D'
    SET_DEVICENAME_ERROR = b'\xBD\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\xBD'

    #from 3.16 get device name
    GET_DEVICENAME_HEADER = b'\x3e'
    GET_DEVICENAME_ERROR = b'\xBE\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\xBE'

    #from 3.17 get debug data
    GET_DEBUGDATA_HEARTRATE_HEADER = b'\x03\x00'
    GET_DEBUGDATA_TURNOVER_HEADER = b'\x03\x01'
    GET_DEBUGDATA_BEDTIME_HEADER = b'\x03\x02'

    #from 3.18 get raw data
    GET_RAWDATA_OK = b'\x16\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x16'
    GET_RAWDATA_HEADER = b'\x16'
    GET_RAWDATA_ERROR = b'\xc6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\xc6'

    #from 3.19 delete historical data
    DELETE_HISTORICALDATA_OK = b'\x28\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x28'
    DELETE_HISTORICALDATA_ERROR = b'\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\xb8'

    #from 3.20 temperature and humidity
    GET_TEMPERATURE_OK = b'\x0d\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x0d'
    GET_TEMPERATURE_ERROR = b'\x0d\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x0c'
    GET_TEMPERATURE_HEADER = b'\x0d'

    #from 3.21 delete all data
    DELETE_ALL_DATA_OK = b'\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x04'
    DELETE_ALL_DATA_ERROR = b'\x04\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x03'

class COMMANDS(object):
    
    __metaclass__ = Immutable
    
    #from 3.1 set time
    SET_TIME_HEADER = b'\x01' # follow the payload

    #from 3.2 get time
    GET_TIME = b'\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x41'

    #from 3.3 set user personal information
    SET_USERINFO_HEADER = b'\x02' # follow the payload

    #from 3.4 get user personal information
    GET_USERINFO = b'\x42\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x42'

    #from 3.5 get heart rate breathing storage data
    GET_HEARTRATE_HEADER = b'\x17' # follow the payload

    #from 3.6 bed time data
    GET_BEDTIME_HEADER = b'\x14' # follow the payload

    #from 3.6bis rollover data
    GET_ROLLOVER_HEADER = b'\x15' # follow the payload

    #from 3.7 set device id code
    SET_DEVICEID_HEADER = b'\x05' # follow the payload

    #from 3.8 real time heart rate and breathing mod control
    GET_REALTIME_HEARTBREATH_ON = b'\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x12'
    GET_REALTIME_HEARTBREATH_OFF = b'\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x11'

    #from 3.9 restore factory sleep settings
    _RESTORE_FACTORY = b'\x12\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x12'

    #from 3.10 read device power
    GET_POWER = b'\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x13'

    #from 3.11 read mac address
    GET_MACADDR = b'\x22\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x22'

    #from 3.12 read firmware version number
    GET_FIRMVER = b'\x27\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x27'

    #from 3.13 mcu soft reset
    SOFTRESET = b'\x2e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x2E'

    #from 3.14 firmware upgrade command
    #omitted since further instructions are missing

    #from 3.15 set bluetooth device name
    SET_DEVICENAME_HEADER = b'\x3d' # follows the payload

    #from 3.16 read bluetooth device name
    GET_DEVICENAME = b'\x3e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x3E'

    #from 3.17 debug data
    GET_DEBUGDATA_ON = b'\x03\x05\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x09'
    GET_DEBUGDATA_OFF = b'\x03\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x08'

    #from 3.18 get sleep raw data
    GET_RAWDATA_ON = b'\x16\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x17'
    GET_RAWDATA_OFF = b'\x16\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x16'

    #From 3.19 delete historical data
    _DELETE_HISTORICALDATA = b'\x28\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x28'

    #from 3.20 temperature and humidity
    GET_TEMPERATURE_ON = b'\x0d\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x0e'
    GET_TEMPERATURE_OFF = b'\x0d\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x0d'

    #from 3.21 delete all data
    _DELETE_ALL_DATA = b'\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\00\x00\x04'