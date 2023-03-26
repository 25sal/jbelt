import numpy
import tensorflow._api.v2.compat.v1 as tensorflow
from models import deeper_fcn

input = []
output = []

aggregate_files = ["../aggr_24-03-23.csv", "../aggr_26-03-23.csv"]
raw_files = ["../newraw_24-03-23.csv", "../newraw_26-03-23.csv"]
if len(aggregate_files)!=len(raw_files):
    print("aggregate files and raw files should match, not only in number but in generation time")
    exit()

for filenumber in range(0,len(aggregate_files)):
    aggregate = numpy.genfromtxt(aggregate_files[filenumber], delimiter=",")
    raw = numpy.genfromtxt(raw_files[filenumber], delimiter=",")

    print("analizing",aggregate_files[filenumber], "and", raw_files[filenumber], "(they should have matching generation time)")

    ################### CREATE DATA SET
    ### FOR EACH AGGREGATE DATA FETCH A 400 ARRAY OF RAW DATA
    ### HAVING THE HIGHEST TIMESTAMP LESS THAN THE AGGREGATE TIMESTAMP

    last_index = 0
    added_data = 0
    for tuple in aggregate:
        if tuple[2] == 0: #heartrate should not be 0
            continue
        timestamp = tuple[0] #take heartrate timestamp

        while raw[last_index][6]<timestamp:  #in the raw data, find the first bcg value generated after the aggregate data
            last_index+=1

        if last_index < 400 :  #we need at least 400 bcg values
            continue

        input.append(raw[last_index-400:last_index,1]) #take 400 bcg values, the last one should precede the aggregate data in timestamp
        output.append(tuple[2]) #take the expected output for the bcg segment
        added_data+=1
    print("added", added_data, "output/input values")

input = numpy.expand_dims(input, axis=2) #from (n, 400) to (n, 400, 1)
output = numpy.array(output)             #from list to numpy array

print("total data shapes: ", input.shape, output.shape)

#tensorflow
tensorflow.logging.set_verbosity(tensorflow.logging.ERROR)
config = tensorflow.ConfigProto()
tensorflow.keras.backend.set_session(tensorflow.Session(config=config))
enlarge=1
model_params = dict(metrics=["mae", "mape"], enlarge=enlarge)
fit_params = dict(epochs=250, verbose=2)

model = deeper_fcn.create(**model_params)

with open("output/deeper_fcn2/model.json", 'w') as fp:
    fp.write(model.to_json())

model.fit(input, output, **fit_params)
model.save_weights("output/deeper_fcn2/weights")
tensorflow.keras.backend.clear_session()
