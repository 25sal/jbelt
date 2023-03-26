import time, asyncio
from datetime import datetime
from nuovacintura5 import *

async def main():
    

    belt = HappySleep_belt()
    try:
        await belt.connect()
        print("Power: "+str(await belt.get_power())+"%")
        #print(await belt.get_storage_heartbreath(0))
        await belt.turn_realtime_heartbreath_off()
        await belt.turn_realtime_raw_bcg_off()
        await belt.turn_realtime_temperature_humidity_off()


    except Exception as e:
        print(e)
    finally:
        await belt.disconnect()
        
asyncio.run(main())

