import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, find_peaks, welch
from scipy.interpolate import interp1d

# ------------------ PARAMETERS ------------------
FS = 1000                       # sampling frequency (Hz)
BP_LOW, BP_HIGH = 5, 15         # band‑pass for QRS
ROLL_SEC = 5                    # smoothing window (s)
MIN_CYCLE_SEC, MAX_CYCLE_SEC = 20, 60
DELTA_HR_THRESH = 3             # bpm excursion for loose CVHR
PAUSE_MIN_SEC = 10              # min length of pause in EDR
LF_BAND = (0.04, 0.15)
HF_BAND = (0.15, 0.4)
LFHF_RATIO = 2                  # LF/HF threshold
WIN_HRV_SEC, STEP_HRV_SEC = 60, 10

# ------------------ LOAD DATA -------------------
ecg = np.loadtxt('data/dataset5/2.txt', delimiter='\t')
ecg = ecg[:,-1]  
duration_sec = len(ecg)/FS
    
# ------------------ FILTER & R‑PEAKS -------------
b, a = butter(3, [BP_LOW/(FS/2), BP_HIGH/(FS/2)], btype='band')
ecg_filt = filtfilt(b, a, ecg)
ecg_filt = ecg
abs_filt = np.abs(ecg_filt)
pk_idxs, _ = find_peaks(abs_filt,
                        distance=int(0.25*FS),
                        height=np.percentile(abs_filt, 99))

# Guard against empty detection
if len(pk_idxs) < 3:
    print("Insufficient R-peaks detected.")
    deltaHR_intervals = []
    edr_pauses = []
    lfhf_intervals = []
else:
    # ------------------ HR SERIES --------------------
    rr_sec = np.diff(pk_idxs) / FS
    hr_bpm = 60 / rr_sec
    t_hr = pk_idxs[1:] / FS
    df_hr = pd.DataFrame({'hr': hr_bpm}, index=t_hr)

    # Rolling median + mean (double smoothing)
    rr_median = df_hr.index.to_series().diff().median()
    if pd.isna(rr_median) or rr_median == 0:
        win_pts = 1
    else:
        win_pts = max(1, int(ROLL_SEC / rr_median))
    hr_s = df_hr['hr'].rolling(win_pts, center=True, min_periods=1).median()
    hr_s = hr_s.rolling(win_pts, center=True, min_periods=1).mean()

    # ------------------ ΔHR ≥ 3 bpm CVHR -------------
    deltaHR_intervals = []
    if len(hr_s) > 0:
        mins, _ = find_peaks(-hr_s, distance=int(10/rr_median) if rr_median > 0 else 1)
        maxs, _ = find_peaks(hr_s,  distance=int(10/rr_median) if rr_median > 0 else 1)
        i_max = 0
        for i_min in mins:
            while i_max < len(maxs) and maxs[i_max] < i_min:
                i_max += 1
            if i_max >= len(maxs):
                break
            idx_min, idx_max = i_min, maxs[i_max]
            amp = hr_s.iloc[idx_max] - hr_s.iloc[idx_min]
            dt  = hr_s.index[idx_max] - hr_s.index[idx_min]
            if amp >= DELTA_HR_THRESH and MIN_CYCLE_SEC <= dt <= MAX_CYCLE_SEC:
                deltaHR_intervals.append((float(hr_s.index[idx_min]), float(hr_s.index[idx_max])))

    # ------------------ EDR & PAUSES -----------------
    r_amp = abs_filt[pk_idxs]
    r_times = pk_idxs / FS
    edr_series = pd.Series(r_amp, index=r_times)

    t_interp = np.arange(0, duration_sec, 0.25)
    edr_interp = interp1d(edr_series.index, edr_series.values,
                          bounds_error=False, fill_value="extrapolate")(t_interp)

    edr_diff = pd.Series(edr_interp).diff().abs().rolling(int(PAUSE_MIN_SEC*4), center=True).mean()
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

    # ------------------ LF/HF > 2 INTERVALS ----------
    f_interp_hr = interp1d(df_hr.index, df_hr['hr'],
                           bounds_error=False, fill_value="extrapolate")
    hr_4hz = f_interp_hr(t_interp)
    lfhf_intervals = []
    for i in range(0, len(t_interp) - WIN_HRV_SEC*4, STEP_HRV_SEC*4):
        win = hr_4hz[i:i+WIN_HRV_SEC*4]
        if np.any(np.isnan(win)):
            continue
        f, Pxx = welch(win, fs=4.0, nperseg=min(256, len(win)))
        lf = np.trapz(Pxx[(f >= LF_BAND[0]) & (f < LF_BAND[1])], f[(f >= LF_BAND[0]) & (f < LF_BAND[1])])
        hf = np.trapz(Pxx[(f >= HF_BAND[0]) & (f <= HF_BAND[1])], f[(f >= HF_BAND[0]) & (f <= HF_BAND[1])])
        if hf > 0 and lf/hf > LFHF_RATIO:
            mid = t_interp[i] + WIN_HRV_SEC/2
            lfhf_intervals.append((mid-WIN_HRV_SEC/2, mid+WIN_HRV_SEC/2))

# ------------------ PLOT -------------------------
trattenute = [(60000, 90000), (150000, 180000), (240000, 270000), (330000, 360000)]
plt.figure(figsize=(12, 5))
if len(pk_idxs) >= 3:
    plt.plot(hr_s.index, hr_s.values, label='HR (smoothed)')
    for s, e in deltaHR_intervals:
        plt.axvspan(s, e, alpha=0.2, color='orange', label='ΔHR ≥ 3 bpm' if s == deltaHR_intervals[0][0] else None)
    for s, e in edr_pauses:
        plt.axvspan(s, e, alpha=0.2, color='green', label='EDR pause' if s == edr_pauses[0][0] else None)
    for s, e in lfhf_intervals[:10]:  # show first 10 to avoid overplotting
        plt.axvspan(s, e, alpha=0.1, color='red', label='LF/HF > 2' if s == lfhf_intervals[0][0] else None)
    
    for start, end in trattenute:
        plt.axvspan(start/1000, end/1000, color='yellow', alpha=0.5)
    
    plt.xlabel('Time (s)')
    plt.ylabel('HR (bpm)')
    plt.title('Apnea / Respiratory Pause Detection – Dataset 5')
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.show()

summary = {
    "Recording_duration_s": duration_sec,
    "R_peaks_detected": int(len(pk_idxs)),
    "ΔHR_intervals_s": deltaHR_intervals,
    "EDR_pause_intervals_s": edr_pauses,
    "LFHF_intervals_s": lfhf_intervals[:10]  # truncate for brevity
}
summary
