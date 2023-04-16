import os, numpy

def get_files(filedirectory:str="../"):
    """Find couples of bgc and aggregate csv files, when they are
    called with a prefix: \"newraw for bcg and \"aggr for aggregate
    files.

    Args:
        filedirectory: str ; Default = ../
            folder in which is expected to find all files

    Returns:
        newraws: list
            list of bcg files, expressed as string paths to files
        aggregates: list
            list of aggregate files, expressed as string paths to
            files
    """


    newraws = []
    aggregates = []
    
    for entry in os.listdir(filedirectory):
        newraw_filename = filedirectory+entry
        if entry.startswith("newraw_") and os.path.isfile(newraw_filename):
            aggregate_filename = filedirectory+"aggr"+entry[6:] # find aggregate file
            if os.path.isfile(aggregate_filename):
                newraws.append(newraw_filename)
                aggregates.append(aggregate_filename)
                
    return newraws, aggregates

def get_patches(newraw_files: list, aggregate_files):
    """Analyze csv files using proposed algorithm, which requires a column
    for a per-value timestamp in bcg file, in search for bcg patches and
    aggregate values for each patch.
    Outputs a list of bcg patches consisting of 400 bcg values, and other
    lists of values. Each value represents an output for the 400 values
    patch sharing its index.

    Args:
        newraw_files: list
            list of csv files containing bcg values with timestamp 
        aggregate_files: list
            list of csv files containing aggregate values with timestamp
    
    Returns:
        bcg_patches = list
            list of 400 bcg values patches
        hr_values = list
            list of heart rate values, each can be seen as the output of
            the bcg patch sharing its index
        movement_detected = list
            list of booleans, which states whether patients has moved
            while patch was being measured        

    """

    bcg_patches = []
    hr_values = []
    movement_detected = []

    for filenumber in range(0,len(aggregate_files)):
        aggregate = numpy.genfromtxt(aggregate_files[filenumber], delimiter=",")
        raw = numpy.genfromtxt(newraw_files[filenumber], delimiter=",")

        print("analizing",aggregate_files[filenumber], "and", newraw_files[filenumber], "(they should have matching generation time)")

        ################### CREATE DATA SET
        ### FOR EACH AGGREGATE DATA FETCH A 400 ARRAY OF RAW DATA
        ### HAVING THE HIGHEST TIMESTAMP LESS THAN THE AGGREGATE TIMESTAMP

        last_index = 0 #since tuples are ordered, search suitable patch starting from last index
        patch_count_for_this_file = 0

        for aggr_index, tuple in enumerate(aggregate):
            if tuple[2] == 0: #heartrate should not be 0
                continue
            timestamp = tuple[0] #take heartrate timestamp

            while raw[last_index][6] < timestamp:  #in the raw data, find the first bcg value generated after the aggregate data
                last_index+=1

            if last_index < 400 :  #we need at least 400 bcg values
                continue

            bcg_patches.append(raw[last_index-400:last_index,1]) #take 400 bcg values, the last one should precede the aggregate data in timestamp
            hr_values.append(tuple[2]) #take the expected heartrate for the bcg segment

            #################### has the patient moved in the last 8 seconds? ############
            hasmoved = False
            i = 0
            while timestamp-aggregate[aggr_index-i][0] < 8:
                if aggregate[aggr_index-i][4] > 0:
                    hasmoved = True
                    break
                i+=1
            movement_detected.append(hasmoved)

            patch_count_for_this_file+=1

        print("added", patch_count_for_this_file, "output/input values")

    return bcg_patches, hr_values, movement_detected