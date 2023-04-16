import numpy
import tensorflow._api.v2.compat.v1 as tensorflow
from models import deeper_fcn, stacked_cnn_rnn_improved, rnn_gru
import data_utils

raw_files, aggr_files = data_utils.get_files()
print("Found", len(raw_files), "couples")
bcg_patches, hr_values, _ = data_utils.get_patches(raw_files, aggr_files)

input = numpy.expand_dims(bcg_patches, axis=2) #from (n, 400) to (n, 400, 1)
output = numpy.array(hr_values)             #from list to numpy array

print("total data shapes: ", input.shape, output.shape)

#tensorflow
tensorflow.logging.set_verbosity(tensorflow.logging.ERROR)
config = tensorflow.ConfigProto()
tensorflow.keras.backend.set_session(tensorflow.Session(config=config))
enlarge=4
model_params = dict(metrics=["mae", "mape"], enlarge=enlarge)
fit_params = dict(epochs=250, verbose=2)

model = deeper_fcn.create(**model_params)

with open("output/deeper_fcn4/model.json", 'w') as fp:
    fp.write(model.to_json())

model.fit(input, output, **fit_params)
model.save_weights("output/deeper_fcn4/weights")
tensorflow.keras.backend.clear_session()
