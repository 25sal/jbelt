from algorithms import choi, heartrate, brueser, choe
import numpy

sampling_frequency = 50.0

def simple_mean_choi(value_array):
    """ apply choi algorithm on the provided array assuming sampling
    frequency of 50Hz, then divides peaks number for observation time

    Returns:
        estimated heartrate in bpm
    """

    observation_time_seconds = float(len(value_array))/sampling_frequency
    indices = choi.choi(value_array, sampling_frequency)
    peak_peak = value_array[indices[0]:indices[-1]]
    observation_time_seconds = float(len(peak_peak))/sampling_frequency
    heartrate_s = float(len(indices))/observation_time_seconds
    heartrate_bpm = heartrate_s * 60.0
    return(heartrate_bpm)

def diff_mean_choi(value_array):
    """ apply choi algorithm on the provided array assuming sampling
    frequency of 50Hz, then uses a differential mean

    Returns:
        estimated heartrate in bpm
    """

    indices = choi.choi(value_array, sampling_frequency)
    return heartrate.heartrate_from_indices(indices, sampling_frequency)
    
def simple_brueser(value_array):
    """ apply brueser algorithm on the provided array assuming sampling
    frequency of 50Hz

    Returns:
        estimated heartrate in bpm
    """

    return brueser.brueser(value_array, sampling_frequency)[0]

def diff_mean_choe(value_array):
    """ apply cho algorithm on the provided array assuming sampling
    frequency of 50Hz, then uses a differential mean

    Returns:
        estimated heartrate in bpm
    """

    indices = choe.choe(value_array, sampling_frequency)
    return heartrate.heartrate_from_indices(indices, sampling_frequency)

def simple_mean_choe(value_array):
    """ apply choe algorithm on the provided array assuming sampling
    frequency of 50Hz, then divides peaks number for observation time

    Returns:
        estimated heartrate in bpm
    """

    observation_time_seconds = float(len(value_array))/sampling_frequency
    indices = choe.choe(value_array, sampling_frequency)
    peak_peak = value_array[indices[0]:indices[-1]]
    observation_time_seconds = float(len(peak_peak))/sampling_frequency
    heartrate_s = float(len(indices))/observation_time_seconds
    heartrate_bpm = heartrate_s * 60.0
    return(heartrate_bpm)
