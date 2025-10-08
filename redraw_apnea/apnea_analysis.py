# Importazione delle librerie
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

# Caricamento del file CSV
file_path = "data/dataset5/2.txt"
df = pd.read_csv(file_path, header=None, sep="\t")

# Estrazione del segnale ECG
ecg_signal = df.iloc[:, -1]

# Rilevamento dei picchi R
peaks, _ = find_peaks(ecg_signal, distance=600, height=np.mean(ecg_signal))
print("Numero di picchi R rilevati:", len(peaks))
# Calcolo degli intervalli RR in secondi
rr_intervals_seconds = np.diff(peaks) / 1000

# Calcolo della probabilità di apnea con una funzione sigmoide basata sullo z-score degli intervalli RR
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

rr_mean = np.mean(rr_intervals_seconds)
rr_std = np.std(rr_intervals_seconds)
rr_z_scores = (rr_intervals_seconds - rr_mean) / rr_std
rr_apnea_probability = sigmoid(rr_z_scores)

# Interpolazione della probabilità di apnea lungo tutto il segnale
peak_times = peaks[:-1] / 1000  # Tempi dei picchi in secondi
interp_func = interp1d(peak_times, rr_apnea_probability, kind='linear', fill_value="extrapolate")

time_axis = np.arange(0, len(ecg_signal) / 1000, 0.001)  # Asse temporale in secondi
apnea_probability_interpolated = interp_func(time_axis)

# Aggiornamento del DataFrame
df['Apnea_Probability'] = apnea_probability_interpolated

#import ace_tools as tools; tools.display_dataframe_to_user(name="Interpolated Apnea Probability Data", dataframe=df)

# Definizione degli intervalli di trattenuta del respiro dalla timeline fornita
breath_holding_intervals = [
    (60, 90),    # Trattenuta durante inspirazione
    (150, 180),  # Trattenuta durante espirazione
    (240, 270),  # Trattenuta durante inspirazione
    (330, 360)   # Trattenuta durante espirazione
]

# Visualizzazione del grafico della probabilità di apnea con i periodi di trattenuta
plt.figure(figsize=(15, 8))

# Tracciamento della probabilità di apnea
plt.plot(time_axis, df['Apnea_Probability'], label='Probabilità di Apnea', color='red', linewidth=2)

# Evidenziazione dei periodi di trattenuta del respiro
for start, end in breath_holding_intervals:
    plt.axvspan(start, end, color='yellow', alpha=0.3, label='Trattenuta del respiro' if start == 60 else "")

plt.xlabel('Tempo (s)')
plt.ylabel('Probabilità di Apnea')
plt.title('Probabilità di Apnea e Periodi di Trattenuta del Respiro')
plt.ylim(0, 1)
plt.legend(loc='upper right')
plt.grid(True)
plt.show()
