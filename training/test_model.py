import numpy
import tensorflow._api.v2.compat.v1 as tensorflow
from models import deeper_fcn

aggregated = numpy.genfromtxt("../aggr_24-03-23.csv", delimiter=",")
raw = numpy.genfromtxt("../newraw_24-03-23.csv", delimiter=",")

input = []
output = []

################### CREATE DATA SET
### FOR EACH AGGREGATE DATA FETCH A 400 ARRAY OF RAW DATA
### HAVING THE HIGHEST TIMESTAMP LESS THAN THE AGGREGATE TIMESTAMP

last_index = 0
for tuple in aggregated:
    if tuple[2] == 0:
        continue
    timestamp = tuple[0]

    while raw[last_index][6]<timestamp:
        last_index+=1

    if last_index < 400 :
        continue

    input.append(raw[last_index-400:last_index,1])
    output.append(tuple[2])

input = numpy.expand_dims(input, axis=2)
output = numpy.array(output)
print("data shapes: ", input.shape, output.shape)

#tensorflow
tensorflow.logging.set_verbosity(tensorflow.logging.ERROR)
config = tensorflow.ConfigProto()
tensorflow.keras.backend.set_session(tensorflow.Session(config=config))


with open("output/deeper_fcn1/model.json", "r") as fp:
    json = fp.read()
model = tensorflow.keras.models.model_from_json(json)
model.load_weights("output/deeper_fcn1/weights")

result = model.predict(input)

for i in range (1,500):
    print("IA says", result[i][0],", belt says ",output[i])
