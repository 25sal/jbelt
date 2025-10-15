import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("logging/raw_2025-10-15_15-12-59.csv", header=None)
df.columns = ["timestamp", "bcg", "aggr_heartrate", "aggr_breathrate", "aggr_moving", "aggr_presence"]
df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
df = df.set_index('datetime')
print(df.head())
df['bcg'].plot(label='bcg')
plt.show()

