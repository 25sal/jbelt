import copy
import asyncio
import time
from enum import Enum
from datetime import datetime, timedelta
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from constants import COMMANDS, UUIDS, RESPONSES
from events import ResponseEvent, ResponseResult

verbose=False

if verbose:
    def verboseprint(*args):
        # Print each argument separately so caller doesn't need to
        # stuff everything to be printed into a single string
        
           print(*args)
        
else:   
    verboseprint = lambda *a: None



class Realtime_Heartbreath():
    local_timestamp = None
    heartrate = None
    breathrate = None
    moving = False
    presence = True
    device_timestamp = None

    
    def __str__ (self):
        
            return "{} | Heartrate {} bpm, Breathrate {} bpm, Patient is moving: {}, Patient absent: {}".format(self.last_updated, self.heartrate, self.breathrate, "Yes" if self.moving else "No", "Yes" if self.absent else "No")

    def __bool__(self):
        print(time.time()-self.last_updated)
        return time.time()-self.last_updated<3

    def __init__(self, heartrate, breathrate, moving, presence, seconds):
        self.heartrate=heartrate
        self.breathrate=breathrate
        self.moving=moving
        self.presence = presence
        self.local_timestamp = time.time()
        self.device_timestamp = seconds


class Realtime_Temperature_Humidity():
    last_updated = None
    temperature = None
    humidity = None

    def __str__(self):
        return "{} | Temperature {}°C, Humidity {}%".format(self.last_updated, self.temperature, self.humidity)

    def __bool__(self):
        print(time.time()-self.last_updated)
        return time.time()-self.last_updated<3
    
    def __init__(self, temperature, humidity):
        self.temperature=temperature
        self.humidity=humidity
        self.last_updated = time.time()


    
class Userinfo():

    def __init__(self, gender, age, height, weight):
        self.gender="Male" if gender else "Female"
        self.age=age
        self.height=height
        self.weight=weight

    def __str__(self):
        return "{}, {}y.o, {}cm, {}kg".format(self.gender, self.age, self.height, self.weight)
        return self.gender+", "+str(self.age)+"y.o, "+str(self.height)+"cm, "+str(self.weight)+"kg"

class HappySleep_belt(BleakClient) :

    __belt_epoch = datetime(2000, 1, 1, 0,0,0).timestamp()
    

    ## the structure of the api is simple:
    ## send commands on a single characteristic, and receive notifications from a single characteristic
    disconnect_event = asyncio.Event()

    __default_callback = verboseprint
    __default_callback_args = (None,)
    __default_callback_kwargs = dict()

    is_realtime_heartbreath_on = False
    __realtime_heartbreath_callback = __default_callback
    __realtime_heartbreath_callback_args = __default_callback_args
    __realtime_heartbreath_callback_kwargs = __default_callback_kwargs

    is_realtime_temperature_humidity_on = False
    __realtime_humitemp_callback = __default_callback
    __realtime_humitemp_callback_args = __default_callback_args
    __realtime_humitemp_callback_kwargs = __default_callback_kwargs

    is_realtime_raw_bcg_on = False
    __realtime_raw_bcg_callback = __default_callback
    __realtime_raw_bcg_callback_args = __default_callback_args
    __realtime_raw_bcg_callback_kwargs = __default_callback_kwargs

    def __trigger_disconnect_event(self, *args, **kwargs):
        self.disconnect_event.set()

    def __init__ (self, MAC_address : str = None):
        super(HappySleep_belt, self).__init__(MAC_address if MAC_address else "EC:39:40:ED:A0:B9", disconnected_callback=self.__trigger_disconnect_event)
        self.__connection_lock = asyncio.Lock()
        self.__realtime_heartbreath_event = ResponseEvent()
        self.__realtime_heartbreath_lock = asyncio.Lock()
        self.__power_event = ResponseEvent()
        self.__power_lock = asyncio.Lock()
        self.__time_event = ResponseEvent()
        self.__time_lock = asyncio.Lock()
        self.__userinfo_event = ResponseEvent()
        self.__userinfo_lock = asyncio.Lock()
        self.__realtime_humitemp_event = ResponseEvent()
        self.__realtime_humitemp_lock = asyncio.Lock()
        self.__realtime_raw_bcg_event = ResponseEvent()
        self.__realtime_raw_bcg_lock = asyncio.Lock()
        self.__storage_heartbreath_event = ResponseEvent()
        self.__storage_heartbreath_lock = asyncio.Lock()

    async def __send(self, packet):
        verboseprint("Sending packet:", ", ".join(hex(b) for b in packet))
        await self.write_gatt_char(UUIDS.DATA_TO_DEVICE, packet, True)

    def __calculate_crc(self,array:bytearray):
        sum = 0
        # add every byte
        for b in array:
            sum += b

        # in little endian, we can take the less significative byte easily at index 0
        sum = sum.to_bytes(2, 'little')

        return sum[0].to_bytes(1)
        

    def __fill_command(self, incomplete:bytearray):
        length = len(incomplete)
        if length > 15:
            raise Exception("bytearray larger than 15")

        command = incomplete[:]

        # pad the incomplete command
        for i in range(0, 15-length):
            command+=b'\x00'

        command += self.__calculate_crc(incomplete)

        return command

    def __decode_name(self, array):
        return array.decode('ascii')

    def __BCD_decode(self, n:int):
        #CODIFICA BCD:
        # IL BYTE \x12 significa 12 e non 16*1+2
        # la divisione senza resto non è commutativa!
        return (n//16)*10+n%16

    def __time_encode(self, now : datetime):
        yy = ((now.year-2000)//10)*16+(now.year-2000)%10
        MM = (now.month//10)*16+now.month%10
        dd = (now.day//10)*16+now.day%10
        hh = (now.hour//10)*16+now.hour%10
        mm = (now.minute//10)*16+now.minute%10
        ss = (now.second//10)*16+now.second%10

        bcd_encoded = bytearray()
        bcd_encoded += yy.to_bytes(1)+MM.to_bytes(1)+dd.to_bytes(1)+hh.to_bytes(1)+mm.to_bytes(1)+ss.to_bytes(1)
        return bcd_encoded
    
    def __decode_date(self, array:bytearray):
        return datetime(
            2000+self.__BCD_decode(array[0]),
            self.__BCD_decode(array[1]),
            self.__BCD_decode(array[2]),
            self.__BCD_decode(array[3]),
            self.__BCD_decode(array[4]),
            self.__BCD_decode(array[5])
        )

    async def connect(self):

        await self.__connection_lock.acquire()
        #declaring here so that, by using nonlocal, the callback can access to self
        # bleak library does not allow other parameters
        async def callback_notification(sender: BleakGATTCharacteristic, data:bytearray):
            verboseprint(datetime.now(), "|", ', '.join(hex(b) for b in data))
            nonlocal self

            if (data[0]).to_bytes(1) == RESPONSES.GET_DEVICENAME_HEADER:
                verboseprint(_decode_name(data[1:15]))

            #from 3.1 set time
            elif data == RESPONSES.SET_TIME_OK:
                verboseprint("Time set ok")
                self.__time_event.set(ResponseResult.SUCCESS)
            elif data == RESPONSES.SET_TIME_ERROR:
                verboseprint("Time not set")
                self.__time_event.set(ResponseResult.FAILURE)

            #from 3.2 get time
            elif data == RESPONSES.GET_TIME_ERROR:
                verboseprint("Time packet received error")
                self.__time_event.set(ResponseResult.FAILURE)
            elif data[0].to_bytes(1) == RESPONSES.GET_TIME_HEADER:
                verboseprint("Time packet received")
                self.__time_event.set(ResponseResult.SUCCESS, self.__decode_date(data[1:15]))

            #from 3.3 set user information
            elif data == RESPONSES.SET_USERINGO_ERROR:
                verboseprint("userinfo set request failed")
                self.__userinfo_event.set(ResponseResult.FAILURE)
            elif data == RESPONSES.SET_USERINFO_OK:
                verboseprint("packet received : userinfo set ok")
                self.__userinfo_event.set(ResponseResult.SUCCESS)

            #from 3.4 get user information
            elif data == RESPONSES.GET_USERINFO_ERROR:
                verboseprint("Userinfo request error")
                self.__userinfo_event.set(ResponseResult.FAILURE)
            elif data[0].to_bytes(1) == RESPONSES.GET_USERINFO_HEADER:
                verboseprint("Userinfo received", data[1], data[2], data[3], data[4])
                self.__userinfo_event.set(ResponseResult.SUCCESS, Userinfo(data[1], data[2], data[3], data[4]))


            elif data[0].to_bytes(1) == RESPONSES.GET_HEARTRATE_HEADER:
                self.__decode_storage_heartbreath(data)

            #from 3.8 real time heart rate and breathing mode control
            elif data == RESPONSES.GET_REALTIME_HEARTBREATH_ERROR:
                print("Error setting realtime heart rate and breath controll")
                self.__realtime_heartbreath_event.set(ResponseResult.FAILURE)
            elif data == RESPONSES.GET_REALTIME_HEARTBREATH_OK:
                self.__realtime_heartbreath_event.set(ResponseResult.SUCCESS)
                verboseprint("Set up realtime heart rate and breath control success")
            elif data[0].to_bytes(1) == RESPONSES.GET_REALTIME_HEARTBREATH_HEADER:
                verboseprint("heart rate and breath control packet received:")
                if self.is_realtime_heartbreath_on: #and self.__realtime_heartbreath_callback is not None:
                   
                        self.__realtime_heartbreath_callback(
                            Realtime_Heartbreath(data[1],data[2], data[3], data[4], self.__seconds_decode(data[5:9])),
                            *self.__realtime_heartbreath_callback_args,
                            **self.__realtime_heartbreath_callback_kwargs
                            )
                else: #device restarted with realtime data on: turn it off
                    verboseprint("but realtime heartbreath is off")
            
            #from 3.10 read device power
            elif data == RESPONSES.GET_POWER_ERROR:
                verboseprint("Power packet, error")
                self.__power_event.set(ResponseResult.FAILURE)
            elif data[0].to_bytes(1) == RESPONSES.GET_POWER_HEADER:
                verboseprint("Power packet received, success")
                self.__power_event.set(ResponseResult.SUCCESS, data[1]/8*100)

                
            #from 3.18 get sleep raw data
            elif data == RESPONSES.GET_RAWDATA_ERROR:
                verboseprint("Error setting realtime ballistocardiography data stream")
                self.__realtime_raw_bcg_event.set(ResponseResult.FAILURE)
            elif data == RESPONSES.GET_RAWDATA_OK:
                verboseprint("Setting realtime ballistocardiography data stream success")
                self.__realtime_raw_bcg_event.set(ResponseResult.SUCCESS)
            elif data[0].to_bytes(1) == RESPONSES.GET_RAWDATA_HEADER:
                verboseprint("bcg raw data packet received")
                if self.is_realtime_raw_bcg_on and self.__realtime_raw_bcg_callback is not None:
                    self.__realtime_raw_bcg_callback( 
                        (   # a tuple
                                int.from_bytes(data[1:3], 'big'),
                                int.from_bytes(data[3:5], 'big'),
                                int.from_bytes(data[5:7], 'big'),
                                int.from_bytes(data[7:9], 'big'),
                                int.from_bytes(data[9:11], 'big'),
                                int.from_bytes(data[11:13], 'big'),
                                int.from_bytes(data[13:15], 'big'),
                                int.from_bytes(data[15:17], 'big'),
                                int.from_bytes(data[17:19], 'big')
                        ),
                        *self.__realtime_raw_bcg_callback_args,
                        **self.__realtime_raw_bcg_callback_kwargs
                    )

                else: #device must have been restarted with realtime data on : turn it off
                    verboseprint("but realtime bcg is off")

            #from 3.20 real time temperature and humidity
            elif data == RESPONSES.GET_TEMPERATURE_ERROR:
                print("Error setting realtime temperature and humidity controll")
                self.__realtime_humitemp_event.set(ResponseResult.FAILURE)
            #elif data == RESPONSES.GET_TEMPERATURE_OK:
            #THIS CHECK DOES NOT WORK (SEE UPDATED REFERENCE)
            elif data[0].to_bytes(1) == RESPONSES.GET_TEMPERATURE_HEADER and data[3:15] == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' :
                self.__realtime_humitemp_event.set(ResponseResult.SUCCESS)
                verboseprint("Set up temperature and humidity on success")
            elif data[0].to_bytes(1) == RESPONSES.GET_TEMPERATURE_HEADER:
                verboseprint("temperature and humidity packet received ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                if self.is_realtime_temperature_humidity_on and self.__realtime_humitemp_callback is not None:
                    if asyncio.iscoroutinefunction(self.__realtime_humitemp_callback):
                        await self.__realtime_humitemp_callback(
                            Realtime_Temperature_Humidity(data[1]+data[2]*0.01, data[3]+data[4]*0.01),
                            *self.__realtime_humitemp_callback_args,
                            **self.__realtime_humitemp_callback_kwargs
                            )
                    else:
                        self.__realtime_humitemp_callback(
                            Realtime_Temperature_Humidity(data[1]+data[2]*0.01, data[3]+data[4]*0.01),
                            *self.__realtime_humitemp_callback_args,
                            **self.__realtime_humitemp_callback_kwargs
                            )
                else: #device must have been restarted with realtime data on: now turn off
                    verboseprint("but realtime temp is off. Turning off stream...")
            
            else:
                pass


        
        try:
            await super().connect()
            await super().start_notify(UUIDS.DATA_FROM_DEVICE, callback_notification)
            self.disconnect_event.clear()
            self.__connection_lock.release()

        except Exception as e:
            await self.disconnect()
            self.__connection_lock.release()
            print(e)
            raise

    async def disconnect(self):
        await self.__connection_lock.acquire()

        if self.is_realtime_heartbreath_on:
            await self.turn_realtime_heartbreath_off()
            self.is_realtime_heartbreath_on = False
            self.__realtime_heartbreath_callback = self.__default_callback
            self.__realtime_heartbreath_callback_args = self.__default_callback_args
            self.__realtime_heartbreath_callback_kwargs = self.__default_callback_kwargs
        if self.is_realtime_temperature_humidity_on:
            await self.turn_realtime_raw_bcg_off()
            self.is_realtime_temperature_humidity_on = False
            self.__realtime_humitemp_callback = self.__default_callback
            self.__realtime_humitemp_callback_args = self.__default_callback_args
            self.__realtime_humitemp_callback_kwargs = self.__default_callback_kwargs


        await super().disconnect()

        self.__connection_lock.release()

    async def turn_realtime_heartbreath_on(self, on_data_received:callable, *callback_args, **callback_kwargs):
        await self.__realtime_heartbreath_lock.acquire()
        
        if not self.is_connected:
            self.__realtime_heartbreath_lock.release()
            raise Exception("Not connected!")
                
        try:
            if not self.is_realtime_heartbreath_on:
                

                packet = COMMANDS.GET_REALTIME_HEARTBREATH_ON
                await self.__send(packet)
                result = await self.__realtime_heartbreath_event.wait()
                self.__realtime_heartbreath_event.clear()
                if result[0] == ResponseResult.FAILURE:
                    raise Exception("Setting Failed!")
                elif result[0] == ResponseResult.SUCCESS:
                    self.is_realtime_heartbreath_on = True


        except Exception as e:
            await self.disconnect()
            self.__realtime_heartbreath_lock.release()
            print(e)
            raise #return to caller i think

        # anyway change the callback
        self.__realtime_heartbreath_callback = on_data_received
        self.__realtime_heartbreath_callback_args = callback_args
        self.__realtime_heartbreath_callback_kwargs = callback_kwargs
        #callback registered, now to __user_data_decorator_callback

        self.__realtime_heartbreath_lock.release()




    async def turn_realtime_heartbreath_off(self):
        await self.__realtime_heartbreath_lock.acquire()

        try:
            #if not self.is_realtime_heartbreath_on:
            #    self.__realtime_heartbreath_lock.release()
            #    return

            packet = COMMANDS.GET_REALTIME_HEARTBREATH_OFF
            await self.__send(packet)

            result = await self.__realtime_heartbreath_event.wait()
            self.__realtime_heartbreath_event.clear()

            if result[0] == ResponseResult.FAILURE:
                raise Exception("Setting failed")
        except Exception as e:
            await self.disconnect()
            self.__realtime_heartbreath_lock.release()
            print(e)
            raise #return to caller i think
            
        #unregister calls
        self.is_realtime_heartbreath_on = False
        self.__realtime_heartbreath_callback = self.__default_callback
        self.__realtime_heartbreath_callback_args = self.__default_callback_args
        self.__realtime_heartbreath_callback_kwargs = self.__default_callback_kwargs

        self.__realtime_heartbreath_lock.release()

    async def get_power(self):
        await self.__power_lock.acquire()
        try:
            packet = COMMANDS.GET_POWER
            await self.__send(packet)
            result, value = await self.__power_event.wait()   
            self.__power_event.clear() 
            self.__power_lock.release()
        except Exception as e:
            print(e)
            await self.disconnect()
            self.__power_lock.release()
            raise
        

        if result == ResponseResult.FAILURE:
            raise Exception("Power request failed")
        elif result == ResponseResult.SUCCESS:
            return value
        
    async def get_time(self):
        await self.__time_lock.acquire()
        try:
            packet = COMMANDS.GET_TIME
            await self.__send(packet)
            result, value = await self.__time_event.wait()
            self.__time_event.clear()
            self.__time_lock.release()
        except Exception as e:
            print(e)
            await self.disconnect()
            self.__time_lock.release()
            raise

        if result == ResponseResult.FAILURE:
            raise Exception("Time request failed")
        elif result == ResponseResult.SUCCESS:
            return value

    async def set_time(self, time:datetime = None):
        await self.__time_lock.acquire()
        try:
            packet = COMMANDS.SET_TIME_HEADER[:]
            if not time:
                time=datetime.now()
            packet += self.__time_encode(time)
            packet = self.__fill_command(packet)
            await self.__send(packet)
            result = await self.__time_event.wait()
            self.__time_event.clear()
            self.__time_lock.release()
        except Exception as e:
            print(e)
            await self.disconnect()
            self.__time_lock.release()
            raise

        if result[0] == ResponseResult.FAILURE:
            raise Exception("Time set request failed")
        elif result[0] == ResponseResult.SUCCESS:
            return True

    async def get_user_info(self):
        await self.__userinfo_lock.acquire()
        try:
            packet = COMMANDS.GET_USERINFO
            await self.__send(packet)
            result, value = await self.__userinfo_event.wait()
            self.__userinfo_event.clear()
            self.__userinfo_lock.release()
        except Exception as e:
            print(e)
            await self.disconnect()
            self.__userinfo_lock.release()
            raise

        if result == ResponseResult.FAILURE:
            raise Exception("Userinfo request failed")
        elif result == ResponseResult.SUCCESS:
            return value

    async def set_user_info(self, gender = None, age : int = None, height : int = None, weight : int = None, userinfo : Userinfo = None):
        packet = COMMANDS.SET_USERINFO_HEADER[:]
        if not userinfo:
            if not gender or not age or not height or not weight:
                print ("Missing information")
                return False
            gender = 1 if  gender == 1 or gender == True or gender == "Male" else 0
            packet += gender.to_bytes(1) + age.to_bytes(1) + height.to_bytes(1) + weight.to_bytes(1)
        else:
            packet += userinfo.gender.to_bytes(1)+userinfo.age.to_bytes(1)+userinfo.height.to_bytes(1)+userinfo.weight.to_bytes(1)
        
        await self.__userinfo_lock.acquire()
        packet = self.__fill_command(packet)
        try:
            await self.__send(packet)
            result = await self.__userinfo_event.wait()
            self.__userinfo_event.clear()
            self.__userinfo_lock.release()
        except Exception as e:
            print(e)
            await self.disconnect()
            self.__userinfo_lock.release()
            raise

        if result[0] == ResponseResult.FAILURE:
            raise Exception("User info set request failed")
        elif result[0] == ResponseResult.SUCCESS:
            return True
        
    async def turn_realtime_temperature_humidity_on(self, on_data_received:callable, *callback_args, **callback_kwargs):
        await self.__realtime_humitemp_lock.acquire()
        
        if not self.is_connected:
            self.__realtime_humitemp_lock.release()
            raise Exception("Not connected!")


        try:
            if not self.is_realtime_temperature_humidity_on:
                

                packet = COMMANDS.GET_TEMPERATURE_ON
                await self.__send(packet)
                result = await self.__realtime_humitemp_event.wait()
                self.__realtime_humitemp_event.clear()

                if result[0] == ResponseResult.FAILURE:
                    raise Exception("Setting Failed!")
                elif result[0] == ResponseResult.SUCCESS:
                    self.is_realtime_temperature_humidity_on = True


        except Exception as e:
            await self.disconnect()
            self.__realtime_humitemp_lock.release()
            print(e)
            raise #return to caller i think

        #questo non viene eseguito, il codice non finisce perché non viene rilasciata la  lock
        # anyway change the callback
        self.__realtime_humitemp_callback = on_data_received
        self.__realtime_humitemp_callback_args = callback_args
        self.__realtime_humitemp_callback_kwargs = callback_kwargs
        #callback registered, now to __user_data_decorator_callback

        verboseprint("callback set", self.__realtime_humitemp_callback)
        self.__realtime_humitemp_lock.release()
        verboseprint("and successfully opened faucet ~~~~~~~~~~~~~~~~~~~~")

    async def turn_realtime_temperature_humidity_off(self):
        verboseprint("~~~~~~~~~~~~~~~~~~ CLOSING THE FAUCET FOR SM REASON")
        await self.__realtime_humitemp_lock.acquire()

        try:
            #if not self.is_realtime_temperature_humidity_on:
            #    self.__realtime_humitemp_lock.release()
            #    return

            packet = COMMANDS.GET_TEMPERATURE_OFF
            await self.__send(packet)

            result = await self.__realtime_humitemp_event.wait()
            self.__realtime_humitemp_event.clear()

            if result[0] == ResponseResult.FAILURE:
                raise Exception("Setting failed")
        except Exception as e:
            await self.disconnect()
            self.__realtime_humitemp_lock.release()
            print(e)
            raise #return to caller i think
            
        #unregister calls
        self.is_realtime_temperature_humidity_on = False
        self.__realtime_humitemp_callback = self.__default_callback
        self.__realtime_humitemp_callback_args = self.__default_callback_args
        self.__realtime_humitemp_callback_kwargs = self.__default_callback_kwargs

        self.__realtime_humitemp_lock.release()

    async def turn_realtime_raw_bcg_on(self, on_data_received:callable, *callback_args, **callback_kwargs):
        await self.__realtime_raw_bcg_lock.acquire()
        
        if not self.is_connected:
            self.__realtime_raw_bcg_lock.release()
            raise Exception("Not connected!")


        try:
            if not self.is_realtime_raw_bcg_on:
                
                
                self.is_realtime_raw_bcg_on = True
                packet = COMMANDS.GET_RAWDATA_ON
                await self.__send(packet)
                result = await self.__realtime_raw_bcg_event.wait()
                self.__realtime_raw_bcg_event.clear()

                if result[0] == ResponseResult.FAILURE:
                    raise Exception("Setting Failed!")


        except Exception as e:
            await self.disconnect()
            self.is_realtime_raw_bcg_on = False
            self.__realtime_raw_bcg_lock.release()
            print(e)
            raise #return to caller i think

        #questo non viene eseguito, il codice non finisce perché non viene rilasciata la  lock
        # anyway change the callback
        self.__realtime_raw_bcg_callback = on_data_received
        self.__realtime_raw_bcg_callback_args = callback_args
        self.__realtime_raw_bcg_callback_kwargs = callback_kwargs
        #callback registered, now to __user_data_decorator_callback

        self.__realtime_raw_bcg_lock.release()

    async def turn_realtime_raw_bcg_off(self):
        await self.__realtime_raw_bcg_lock.acquire()

        try:
            #if not self.is_realtime_raw_bcg_on:
            #    self.__realtime_raw_bcg_lock.release()
            #    return

            packet = COMMANDS.GET_RAWDATA_OFF
            await self.__send(packet)

            result = await self.__realtime_raw_bcg_event.wait()
            self.__realtime_raw_bcg_event.clear()

            if result[0] == ResponseResult.FAILURE:
                raise Exception("Setting failed")
        except Exception as e:
            await self.disconnect()
            self.__realtime_raw_bcg_lock.release()
            print(e)
            raise #return to caller i think
            
        #unregister calls
        self.is_realtime_raw_bcg_on = False
        self.__realtime_raw_bcg_callback = self.__default_callback
        self.__realtime_raw_bcg_callback_args = self.__default_callback_args
        self.__realtime_raw_bcg_callback_kwargs = self.__default_callback_kwargs

        self.__realtime_raw_bcg_lock.release()

    async def get_storage_heartbreath(self, n_groups: int):
        await self.__storage_heartbreath_lock.acquire()

        self.__temp_storage_heartbreath = []
        AA = n_groups.to_bytes(1, signed=False)
        try:
            packet = COMMANDS.GET_HEARTRATE_HEADER + AA
            packet = self.__fill_command(packet)
            await self.__send(packet)

            result, value = await self.__storage_heartbreath_event.wait()
            self.__storage_heartbreath_event.clear()

            if result == ResponseResult.FAILURE:
                raise Exception("command failed")
            
            
            self.__storage_heartbreath_lock.release()
            return self.__temp_storage_heartbreath

        except Exception as e:
            await self.disconnect()
            print(e)
            raise

    def __decode_storage_heartbreath(self, packet: bytearray):
        number = packet[1]
        if number%2==0 :
            if number%4==0:
                #un capo-gruppo
                self.__temp_storage_heartbreath.append([])
                date = self.__seconds_decode(packet[2:6])
                self.__temp_storage_heartbreath[-1].append(date)
                
                i=6
            else:
                i=2

            while i<18:
                t = [packet[i], packet[i+1]]
                self.__temp_storage_heartbreath[-1].append(t)
                i+=2
            self.__temp_storage_heartbreath[-1].append([packet[18],])

        else:
            self.__temp_storage_heartbreath[-1][-1].append(packet[2])
            for i in range(3 , 18, 2):
                t  = [packet[i], packet[i+1]]
                self.__temp_storage_heartbreath[-1].append(t)
            
        if number == 99:
            self.__storage_heartbreath_event.set(ResponseResult.SUCCESS, None)
        


    def __seconds_decode(self, data:bytearray):
        belt_time = int.from_bytes(data, 'little', signed=False)
        return belt_time+self.__belt_epoch
            

    def __decode_storage_heartbreath(self, packet: bytearray):
        number = packet[1]
        one_minute = timedelta(minutes=1)
        if number%2==0 :
            if number%4==0:
                #un capo-gruppo
                #self.__temp_storage_heartbreath.append([])
                date = self.__seconds_decode(packet[2:6])
                #self.__temp_storage_heartbreath[-1].append(date)
                
                i=6
            else:
                i=2
                date = self.__temp_storage_heartbreath[-1][0]
                date = date + one_minute

            while i<18:
                t = [date, packet[i], packet[i+1]]
                self.__temp_storage_heartbreath.append(t)
                i+=2
                date = date + one_minute

            self.__temp_storage_heartbreath.append([date, packet[18]])

        else:

            date = self.__temp_storage_heartbreath[-1][0]
            self.__temp_storage_heartbreath[-1].append(packet[2])
            for i in range(3 , 18, 2):
                date = date + one_minute
                t  = [date, packet[i], packet[i+1]]
                self.__temp_storage_heartbreath.append(t)
            
        if number == 99:
            self.__storage_heartbreath_event.set(ResponseResult.SUCCESS, None)
