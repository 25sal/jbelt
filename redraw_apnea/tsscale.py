import pandas as pd
import numpy as np
import sys


df = pd.read_csv('data/pulsossimetro/1.txt', delimiter='\t', header=None)
# convert first column from millisecond to datetime
df[0] = pd.to_datetime(df[0], unit='us')
# set first column as index
df.set_index(0, inplace=True)
# drop first column
#downsample to 100Hz
df = df.resample('10ms').mean().interpolate()
# reset index
df.reset_index(inplace=True)
# drop first column
df.drop(columns=[0], inplace=True)
# save to txt as integer
df = df.astype(int)
df.to_csv('data/pulsossimetro/2.txt', sep='\t', header=False, index=True)
