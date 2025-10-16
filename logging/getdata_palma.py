import time
import asyncio
import signal
import traceback
from datetime import datetime

from nuovacintura5 import *  # HappySleep_belt, Realtime_Heartbreath

# record[0] = [timestamp_hr, heartrate, breathrate]
# record[1] = [moving, presence]
record = [
    [0, 0, 0],
    [0, 0]
]


def raw_write(values_tuple, file):
    # Scrive i campioni RAW con l'ultimo HR/BR valido (se < ~7s), altrimenti 0
    print("raw_write:", values_tuple)
    global record
    now = time.time()
    use_hr = (now - record[0][0]) < 7.1
    hr = record[0][1] if use_hr else 0
    br = record[0][2] if use_hr else 0
    moving = record[1][0]
    presence = record[1][1]
    for v in values_tuple:
        file.write(f"{now},{v},{hr},{br},{moving},{presence}\n")


def aggr_write(obj: Realtime_Heartbreath, file):
    print("aggr_write chiamata")  # <-- stampa di debug
    # ...resto del codice...
    # Evita di usare __str__ dell'oggetto, stampa i campi effettivi
    print("aggr_write:", obj.heartrate, obj.breathrate, obj.moving, obj.presence, obj.local_timestamp)
    global record
    if obj.heartrate > 40:
        record[0][0] = obj.local_timestamp
        record[0][1] = obj.heartrate
        record[0][2] = obj.breathrate
    record[1][0] = obj.moving
    record[1][1] = obj.presence
    file.write(f"{obj.local_timestamp},{obj.device_timestamp},{obj.heartrate},{obj.breathrate},{obj.moving},{obj.presence}\n")


async def sync_files(*args):
    try:
        while True:
            await asyncio.sleep(600)
            for f in args:
                f.flush()
    except asyncio.CancelledError:
        pass


async def off_all_streams(belt: HappySleep_belt):
    async def try_off(fn, label):
        try:
            await asyncio.wait_for(fn(), timeout=3)
            print(label, "OFF ok")
        except Exception as e:
            print(label, "OFF skip/timeout:", e)

    await try_off(belt.turn_realtime_heartbreath_off, "HR/BR")
    await try_off(belt.turn_realtime_raw_bcg_off, "RAW")
    await try_off(belt.turn_realtime_temperature_humidity_off, "TEMP")


async def start_streams(belt: HappySleep_belt, aggrcb, aggrfile, rawcb, rawfile):
    # 1) spegni tutto per pulire lo stato device
    await off_all_streams(belt)

    # 2) sincronizza ora
    await asyncio.wait_for(belt.set_time(), timeout=3)
    print("Time set")

    # 3) prova HR/BR; se non conferma, prosegui comunque
    try:
        await asyncio.wait_for(belt.turn_realtime_heartbreath_on(aggrcb, aggrfile), timeout=5)
        print("Realtime heartbreath ON")
    except Exception as e:
        print("HR/BR ON failed:", repr(e))
        traceback.print_exc()

    # 4) RAW con timeout: se fallisce, propaghiamo l'errore
    await asyncio.wait_for(belt.turn_realtime_raw_bcg_on(rawcb, rawfile), timeout=5)
    print("Realtime raw BCG ON")


async def main():
    closing_event = asyncio.Event()
    duplicate_event = False

    def handler(signum, frame):
        nonlocal duplicate_event
        if not duplicate_event:
            duplicate_event = True
            print("Interruption treated")
            closing_event.set()
        else:
            raise SystemExit(1)

    signal.signal(signal.SIGINT, handler)

    datestr = datetime.now().strftime("%F_%H-%M-%S")

    # Sostituisci con il tuo MAC se diverso
    belt = HappySleep_belt("EE:D9:D4:30:EE:F8")

    rawcsv = open(f"raw_{datestr}.csv", "w", buffering=1)
    aggrcsv = open(f"aggr_{datestr}.csv", "w", buffering=1)

    rawcsv.write("t_local,bcg_raw,hr,br,moving,presence\n")
    aggrcsv.write("t_local,t_device,hr,br,moving,presence\n")

    syncjob = asyncio.create_task(sync_files(rawcsv, aggrcsv))

    try:
        print("Connecting...")
        await belt.connect()
        print("Connected:", belt.is_connected)

        try:
            await start_streams(belt, aggr_write, aggrcsv, raw_write, rawcsv)
        except (asyncio.TimeoutError, Exception) as e:
            print("Handshake timeout/error: cycling BLE session:", repr(e))
            traceback.print_exc()
            await belt.disconnect()
            await asyncio.sleep(2)
            await belt.connect()
            print("Re-connected:", belt.is_connected)
            await start_streams(belt, aggr_write, aggrcsv, raw_write, rawcsv)

        await closing_event.wait()

    except Exception as e:
        print("Errore:", repr(e))
        traceback.print_exc()
    finally:
        syncjob.cancel()
        try:
            await syncjob
        except asyncio.CancelledError:
            pass
        try:
            await off_all_streams(belt)
        except Exception:
            pass
        try:
            await belt.disconnect()
        except Exception:
            pass
        rawcsv.close()
        aggrcsv.close()


if __name__ == "__main__":
    asyncio.run(main())


# import time, asyncio, signal
# from nuovacintura5 import *
# from datetime import datetime

# record = [
#     [0, 0, 0], # timestamp, heartrate, breathrate
#     [0, 0]  # timestamp, moving, presence
# ]

# def raw_write( tuple, file ):
#     print("raw_write chiamata", tuple) #VERIFICO SE VIENE CHIAMATA LA CALLBACK
#     global record
#     now = time.time()
#     if record[0][0]-now<7.1:   #if last proper heartrate is older than 7 seconds report 0
#         for i in tuple:
#             file.write("{},{},{},{},{},{}\n".format(now, i, record[0][1], record[0][2], record[1][0], record[1][1]))
#     else:
#         for i in tuple:
#             file.write("{},{},{},{},{},{}\n".format(now, i, 0, 0, record[1][0], record[1][1]))

# def aggr_write ( obj : Realtime_Heartbreath, file):
#     print("aggr_write chiamata", obj)#VERIFICO SE VIENE CHIAMATA LA CALLBACK
#     global record
#     if obj.heartrate > 40:
#         record[0][0] = obj.local_timestamp  #timestamp is that of last proper heartrate;
#         record[0][1] = obj.heartrate
#         record[0][2] = obj.breathrate
#     record[1][0] = obj.moving              #moving and presence are always up-to-date
#     record[1][1] = obj.presence
#     file.write("{},{},{},{},{},{}\n".format(obj.local_timestamp, obj.device_timestamp, obj.heartrate, obj.breathrate, obj.moving, obj.presence))

# async def sync_files (*args):  #periodically flush files (write in memory)
#     try:
#         while True:

#             await asyncio.sleep(600)
#             for file in args:
#                 file.flush()
#     except asyncio.CancelledError:
#         pass

    

# async def main():

#     closing_event = asyncio.Event() #modules will wait for this event to exit
#     duplicate_event = False
#     def handler(signum, frame):#CORREZIONE WINDOWS
#         nonlocal duplicate_event
#         if not duplicate_event:
#             duplicate_event = True
#             print("Interruption treated")
#             closing_event.set()
#         else:
#             exit(1)
            
#     signal.signal(signal.SIGINT,handler )#CORREZIONE WINDOWS: # Use signal.signal instead of add_signal_handler for Windows compatibility
    
#     datestr =  datetime.now().strftime("%F_%H-%M-%S")
#     belt=HappySleep_belt("EE:D9:D4:30:EE:F8")
#     rawcsv = open("raw_"+datestr+".csv", "w")
#     aggrcsv = open("aggr_"+datestr+".csv", "w")

#     syncjob = asyncio.create_task(sync_files(rawcsv, aggrcsv))

#     try:
#         print("Connecting...")#AGGIUNTA STAMPE
#         await belt.connect()
#         print("Connected:", belt.is_connected)



#         await belt.set_time() #update time to that of PC
#         print("Time set")




        

# #   # Sequenza OFF→ON per sicurezza
# #         await belt.turn_realtime_heartbreath_off()
# #         await belt.turn_realtime_raw_bcg_off()
# #         await asyncio.sleep(1)  # breve pausa per sicurezza

#         # # Attiva stream e attendi primo pacchetto dati (con timeout)
#         # data_event = asyncio.Event()

#         # def aggr_write_with_event(obj, file):
#         #     aggr_write(obj, file)
#         #     if not data_event.is_set():
#         #         data_event.set()

#         # def raw_write_with_event(t, file):
#         #     raw_write(t, file)
#         #     if not data_event.is_set():
#         #         data_event.set()

#         # # Attiva stream
#         # await belt.turn_realtime_heartbreath_on(aggr_write_with_event, aggrcsv)
#         # await belt.turn_realtime_raw_bcg_on(raw_write_with_event, rawcsv)
#         # print("Stream ON, attendo primo pacchetto dati...")

#         # try:
#         #     await asyncio.wait_for(data_event.wait(), timeout=10)
#         #     print("Primo pacchetto dati ricevuto: OK")
#         # except asyncio.TimeoutError:
#         #     print("Timeout: nessun dato ricevuto!")
#         #     return

#         # print("Realtime raw BCG ON")
#         # await closing_event.wait()
#         # syncjob.cancel()
#         # await syncjob

#         await belt.turn_realtime_heartbreath_on(aggr_write, aggrcsv)


#         await belt.turn_realtime_raw_bcg_on(raw_write, rawcsv)
#         print("Realtime raw BCG ON")
#         await closing_event.wait()
#         syncjob.cancel()
#         await syncjob

#     except Exception as e:
#         print(e)
#     finally:
#         await belt.disconnect()
#         rawcsv.close()
#         aggrcsv.close()

# asyncio.run(main())
