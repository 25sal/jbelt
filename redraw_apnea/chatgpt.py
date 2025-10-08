# Re-import required packages after state reset
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, find_peaks, welch
from scipy.interpolate import interp1d


def compute_dhr(file_path, FS):
    
    ecg = np.loadtxt(file_path, delimiter='\t')
    ecg = ecg[:, -1]  # Assuming the last column contains the ECG signal
    duration_sec = len(ecg) / FS

    # ------------------ FILTER & R‑PEAKS -------------------
    b, a = butter(3, [5/(FS/2), 15/(FS/2)], btype='band')
    ecg_filt = filtfilt(b, a, ecg)
    abs_filt = np.abs(ecg_filt)
    pk_idxs, _ = find_peaks(abs_filt, distance=int(0.25 * FS), height=np.percentile(abs_filt, 99))
    
    # RR intervals and HR series
    rr_sec = np.diff(pk_idxs) / FS
    hr_bpm = 60 / rr_sec
    t_hr = pk_idxs[1:] / FS
    df_hr = pd.DataFrame({'hr': hr_bpm}, index=t_hr)
    return df_hr, duration_sec


def compute_edr_pauses(edr_interp, fs):
    edr_diff = pd.Series(edr_interp.values).diff().abs().rolling(int(PAUSE_MIN_SEC*4), center=True).mean()
    t_interp = edr_interp.index
    if edr_diff.dropna().size > 0:
        pause_thresh = np.percentile(edr_diff.dropna(), 10)
        pause_mask = edr_diff < pause_thresh
    else:
        pause_mask = np.array([])

    edr_pauses = []
    in_pause = False
    for i, flag in enumerate(pause_mask):
        if flag and not in_pause:
            start = t_interp[i]
            in_pause = True
        elif not flag and in_pause:
            end = t_interp[i]
            if end - start >= PAUSE_MIN_SEC:
                edr_pauses.append((start, end))
            in_pause = False
    if in_pause:
        end = t_interp[-1]
        if end - start >= PAUSE_MIN_SEC:
            edr_pauses.append((start, end))
    return edr_pauses



def compute_edr(file_path, FS):
    ecg = np.loadtxt(file_path, delimiter='\t')
    ecg = ecg[:, -1]  # Assuming the last column contains the ECG signal
    
    duration_sec = len(ecg) / FS

    # ------------------ FILTER & R‑PEAKS -------------------
    b, a = butter(3, [5/(FS/2), 15/(FS/2)], btype='band')
    ecg_filt = filtfilt(b, a, ecg)
    abs_filt = np.abs(ecg_filt)
    pk_idxs, _ = find_peaks(abs_filt, distance=int(0.25 * FS), height=np.percentile(abs_filt, 99))
    
    # ------------------ EDR & PAUSES -----------------
    r_amp = abs_filt[pk_idxs]
    r_times = pk_idxs / FS
    edr_series = pd.Series(r_amp, index=r_times)
    
    t_interp = np.arange(0, duration_sec, 0.25)
    edr_interp = interp1d(edr_series.index, edr_series.values,
                          bounds_error=False, fill_value="extrapolate")(t_interp)
    edr_series = pd.Series(edr_interp, index=t_interp)
    return edr_series


def compute_deltaHR_and_lfhf(df_hr, duration_sec):
    # Double smoothing
    rr_median = df_hr.index.to_series().diff().median()
    win_pts = max(1, int(5 / rr_median)) if not pd.isna(rr_median) and rr_median != 0 else 1
    hr_s = df_hr['hr'].rolling(win_pts, center=True, min_periods=1).median()
    hr_s = hr_s.rolling(win_pts, center=True, min_periods=1).mean()


    # Compute ΔHR as absolute difference between successive HR values
    delta_hr_vals = np.abs(np.diff(hr_s))
    delta_hr_times = hr_s.index[1:]


    # Interpolate HR at 4 Hz
    f_hr_4hz = interp1d(df_hr.index, df_hr['hr'], bounds_error=False, fill_value="extrapolate")
    t_interp = np.arange(0, duration_sec, 0.25)
    hr_4hz = f_hr_4hz(t_interp)


    # Compute LF/HF ratio over moving windows
    lfhf_series = []
    lfhf_times = []
    LF_BAND = (0.04, 0.15)
    HF_BAND = (0.15, 0.4)
    WIN_HRV_SEC = 60
    step_len = 4  # 1s at 4Hz
    win_len = int(WIN_HRV_SEC * 4)

    for i in range(0, len(hr_4hz) - win_len, step_len):
        segment = hr_4hz[i:i + win_len]
        if np.any(np.isnan(segment)):
            continue
        f, Pxx = welch(segment, fs=4.0, nperseg=min(256, len(segment)))
        lf = np.trapz(Pxx[(f >= LF_BAND[0]) & (f < LF_BAND[1])], f[(f >= LF_BAND[0]) & (f < LF_BAND[1])])
        hf = np.trapz(Pxx[(f >= HF_BAND[0]) & (f <= HF_BAND[1])], f[(f >= HF_BAND[0]) & (f <= HF_BAND[1])])
        if hf > 0:
            lfhf_series.append(lf / hf)
            lfhf_times.append(t_interp[i] + WIN_HRV_SEC / 2)
    
    return delta_hr_times, delta_hr_vals, lfhf_times, lfhf_series

def comp_lfhf_intervals(lfhf_times, lfhf_series, threshold=2):
     # check when the derivative of [lfhf_times, lfhf_series] is > 0 for at least 10 seconds
    deriv = np.diff(lfhf_series, prepend=0)
    lfhf_intervals = []
    start = None
    for i in range(len(deriv)):
        if deriv[i] > 0:
            if start is None:
                leftix = i
                start = lfhf_times[i]
        else:
            if start is not None:
                end = lfhf_times[i]
                rightix = i
                if end - start >= 10 and max(lfhf_series[leftix:rightix]) > threshold:
                    lfhf_intervals.append((start, end))
                start = None 
    return lfhf_intervals
    
    
trattenute = {"v1": [(60000, 90000), (120000, 150000), (180000, 210000), (240000, 270000),
                 (480000, 510000), (540000, 570000), (600000, 630000), (660000, 690000)],
              "v2": [(60000, 90000), (150000, 180000), (240000, 270000), (330000, 360000)]
            }
trattenute = trattenute["v2"]  # Use the intervals for v2
v2 = [2, 4, 5, 10,12,14,15,16, 18, 19,20]  # Example V2 values for the plot
v1 = [1]
v2 = [2]
# Reload the uploaded ECG data (file 5.csv)
file_path = 'data/pulsossimetro/'
PAUSE_MIN_SEC = 10              # min length of pause in EDR

events_detected = 0

FS = 100  # Sampling frequency

for id in v2:
    file_path = file_path+f'{id}.txt'
    
    # Compute parameters


    df_hr, duration_sec = compute_dhr(file_path, FS)
    delta_hr_times, delta_hr_vals, lfhf_times, lfhf_series = compute_deltaHR_and_lfhf(df_hr, duration_sec)

    lfhf_intervals = comp_lfhf_intervals(lfhf_times, lfhf_series,1)

    edr = compute_edr(file_path, FS)
    edr_pauses = compute_edr_pauses(edr, FS)





    # Plotting
    fig, axs = plt.subplots(3, 1, figsize=(12, 6), sharex=True)

    axs[0].plot(delta_hr_times, delta_hr_vals, label='ΔHR (bpm)', color='tab:blue')
    axs[0].axhline(3, color='gray', linestyle='--', label='Soglia ΔHR = 3 bpm')
    axs[0].set_ylabel('ΔHR (bpm)')
    axs[0].set_title('ΔHR tra picchi successivi')
    for start, end in trattenute:
        axs[0].axvspan(start/1000, end/1000, color='yellow', alpha=0.5)
    axs[0].legend()
    axs[0].grid(True)

    axs[1].plot(lfhf_times, lfhf_series, label='LF/HF', color='tab:red')
    axs[1].axhline(2, color='gray', linestyle='--', label='Soglia LF/HF = 2')
    axs[1].set_ylabel('LF/HF')
    axs[1].set_xlabel('Tempo (s)')
    axs[1].set_title('LF/HF su finestra mobile (60s, passo 1s)')
    for start, end in trattenute:
        axs[1].axvspan(start/1000, end/1000, color='yellow', alpha=0.5)
    
    if lfhf_intervals is not None:
        for start, end in lfhf_intervals:
            axs[1].axvspan(start, end, alpha=0.1, color='red', label='LF/HF increasing' if start == lfhf_intervals[0][0] else None)
    
    
    axs[1].legend()
    axs[1].grid(True)

    axs[2].plot(edr.index, edr.values, label='EDR', color='tab:green')
    axs[2].set_ylabel('EDR (mV)')
    axs[2].set_xlabel('Tempo (s)')
    axs[2].set_title('EDR (R‑peak amplitudes)')
    for start, end in trattenute:
        axs[2].axvspan(start/1000, end/1000, color='yellow', alpha=0.5)
        
    for s, e in edr_pauses:
        axs[2].axvspan(s, e, alpha=0.2, color='green', label='EDR pause' if s == edr_pauses[0][0] else None)
    
    axs[2].legend()
    axs[2].grid(True)

 
    plt.tight_layout()
    plt.savefig(file_path+f'plot_{id}.png')
    
    
    for  start, end in trattenute:
        # count if this interval overlaps with edr_pauses or with lfhf_intervals
        overlaps_edr = any(e > start and e < end  for s, e in edr_pauses)
        overlaps_lfhf = any(e < end and e > start for s, e in lfhf_intervals)
        if overlaps_edr or overlaps_lfhf:
            events_detected += 1
            
#print in a table format events and average time distances
# for edr, lfhf and total
'''
print(f"\n{'Event Type':<15} {'Count':<10} {'Avg Time Distance (s)':<20}")
print(f"{'-'*15} {'-'*10} {'-'*20}")
print(f"{'EDR Pause':<15} {events_detected_edr:<10} {average_time_distance_edr/events_detected_edr if events_detected_edr > 0 else 0:<20.2f}")
print(f"{'LF/HF > 2':<15} {events_detected_lfhf:<10} {average_time_distance_lfhf/events_detected_lfhf if events_detected_lfhf > 0 else 0:<20.2f}")
print(f"{'Total':<15} {events_detected:<10} {average_time_distance/(events_detected if events_detected > 0 else 1):<20.2f}")
'''