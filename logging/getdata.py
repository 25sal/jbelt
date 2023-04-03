import time, asyncio, signal
from nuovacintura5 import *
from datetime import datetime

record = [
    [0, 0, 0], # timestamp, heartrate, breathrate
    [0, 0]  # timestamp, moving, presence
]

def raw_write( tuple, file ):
    global record
    now = time.time()
    if record[0][0]-now<7.1:   #if last proper heartrate is older than 7 seconds report 0
        for i in tuple:
            file.write("{},{},{},{},{},{}\n".format(now, i, record[0][1], record[0][2], record[1][0], record[1][1]))
    else:
        for i in tuple:
            file.write("{},{},{},{},{},{}\n".format(now, i, 0, 0, record[1][0], record[1][1]))

def aggr_write ( obj : Realtime_Heartbreath, file):
    global record
    if obj.heartrate > 40:
        record[0][0] = obj.local_timestamp  #timestamp is that of last proper heartrate;
        record[0][1] = obj.heartrate
        record[0][2] = obj.breathrate
    record[1][0] = obj.moving              #moving and presence are always up-to-date
    record[1][1] = obj.presence
    file.write("{},{},{},{},{},{}\n".format(obj.local_timestamp, obj.device_timestamp, obj.heartrate, obj.breathrate, obj.moving, obj.presence))

async def sync_files (*args):  #periodically flush files (write in memory)
    try:
        while True:

            await asyncio.sleep(600)
            for file in args:
                file.flush()
    except asyncio.CancelledError:
        pass

    

async def main():

    closing_event = asyncio.Event() #modules will wait for this event to exit
    duplicate_event = False
    def handler():
        nonlocal duplicate_event
        if not duplicate_event:
            duplicate_event = True
            print("Interruption treated")
            closing_event.set()
        else:
            exit(1)
            
    asyncio.get_event_loop().add_signal_handler(signal.SIGINT,handler )

    
    datestr =  datetime.now().strftime("%F_%H-%M-%S")
    belt=HappySleep_belt()
    rawcsv = open("raw_"+datestr+".csv", "w")
    aggrcsv = open("aggr_"+datestr+".csv", "w")

    syncjob = asyncio.create_task(sync_files(rawcsv, aggrcsv))

    try:
        await belt.connect()
        await belt.set_time() #update time to that of PC
        await belt.turn_realtime_heartbreath_on(aggr_write, aggrcsv)
        await belt.turn_realtime_raw_bcg_on(raw_write, rawcsv)
        await closing_event.wait()
        syncjob.cancel()
        await syncjob

    except Exception as e:
        print(e)
    finally:
        await belt.disconnect()
        rawcsv.close()
        aggrcsv.close()

asyncio.run(main())
