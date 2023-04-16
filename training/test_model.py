import numpy
import tensorflow._api.v2.compat.v1 as tensorflow
from models import deeper_fcn
from analytical_methods import *
import data_utils


input, output, movement_detected = data_utils.get_patches(["../newraw_24-03-23.csv",],["../aggr_24-03-23.csv",])

tinput = numpy.expand_dims(input, axis=2)
output = numpy.array(output)
print("data shapes: ", tinput.shape, output.shape)

#tensorflow
tensorflow.logging.set_verbosity(tensorflow.logging.ERROR)
config = tensorflow.ConfigProto()
tensorflow.keras.backend.set_session(tensorflow.Session(config=config))


with open("output/deeper_fcn4/model.json", "r") as fp:
    json = fp.read()
model = tensorflow.keras.models.model_from_json(json)
model.load_weights("output/deeper_fcn4/weights")

result = model.predict(tinput)

print ("| {:^18} | {:^5} | moved | {:^18} | {:^18} |".format("IA", "belt", "choi", "choe"))
for i in range (1340,1400):
    print("| {:<18} | {:<5} | {:^5} | {:<18} | {:<18} |".format(result[i][0],output[i],movement_detected[i],diff_mean_choi(input[i]), diff_mean_choe(input[i])))
