import numpy
import tensorflow._api.v2.compat.v1 as tensorflow
from models import deeper_fcn
from analytical_methods import *

aggregated = numpy.genfromtxt("../aggr_24-03-23.csv", delimiter=",")
raw = numpy.genfromtxt("../newraw_24-03-23.csv", delimiter=",")

input = []
output = []
movement_detected = []

################### CREATE DATA SET
### FOR EACH AGGREGATE DATA FETCH A 400 ARRAY OF RAW DATA
### HAVING THE HIGHEST TIMESTAMP LESS THAN THE AGGREGATE TIMESTAMP

last_index = 0
for aggrindex, tuple in enumerate(aggregated):
    if tuple[2] == 0:
        continue
    timestamp = tuple[0]

    while raw[last_index][6]<timestamp:
        last_index+=1

    if last_index < 400 :
        continue

    input.append(raw[last_index-400:last_index,1])
    output.append(tuple[2])

    #in the last 8 seconds, had the user moved
    hasmoved = False
    i = 0
    while timestamp-aggregated[aggrindex-i][0] < 8:
        if aggregated[aggrindex-i][4] > 0:
            hasmoved = True
        i+=1
    movement_detected.append(hasmoved)



tinput = numpy.expand_dims(input, axis=2)
output = numpy.array(output)
print("data shapes: ", tinput.shape, output.shape)

#tensorflow
tensorflow.logging.set_verbosity(tensorflow.logging.ERROR)
config = tensorflow.ConfigProto()
tensorflow.keras.backend.set_session(tensorflow.Session(config=config))


with open("output/deeper_fcn1/model.json", "r") as fp:
    json = fp.read()
model = tensorflow.keras.models.model_from_json(json)
model.load_weights("output/deeper_fcn1/weights")

result = model.predict(tinput)

print ("| {:^18} | {:^5} | moved | {:^18} | {:^18} |".format("IA", "belt", "choi", "choe"))
for i in range (1340,1400):
    print("| {:<18} | {:<5} | {:^5} | {:<18} | {:<18} |".format(result[i][0],output[i],movement_detected[i],diff_mean_choi(input[i]), diff_mean_choe(input[i])))