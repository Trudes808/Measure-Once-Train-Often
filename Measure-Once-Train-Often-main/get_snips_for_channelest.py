import json
import numpy as np
import scipy.io
from scipy.signal import fftconvolve
from pathlib import Path

# ----------------------------
# Config
# ----------------------------
folder_path = Path('/home/sp33752/spenser/trumpet/Measure-Once-Train-Often/data/OFDM')
base_path   = Path('/home/sp33752/spenser/trumpet/Measure-Once-Train-Often/data/OFDM_snips')
tx_path     = Path('/home/sp33752/spenser/magicalquail/src/waveforms/matwaves/OFDM/OFDM.mat')

# region/symbol geometry (same as your script)
REGION_LEN   = 38400 + 800   # 39200
REGION_STEP  = 38400
FIRST_OFFSET = 38400 - 400   # start relative to ZC peak
MAX_REGIONS_PER_FILE = 100   # cap per file (same behavior)

# ----------------------------
# I/O setup
# ----------------------------
base_path.mkdir(parents=True, exist_ok=True)

# ----------------------------
# Load sync (Tx) once
# ----------------------------
tx_data  = scipy.io.loadmat(tx_path)
signal   = tx_data['f_sig'].ravel()
sync_seq = signal[:7680].astype(np.complex64, copy=False)  # length 7680
zc_len   = sync_seq.size

# Precompute conjugate for correlation
sync_conj = np.conjugate(sync_seq)

# ----------------------------
# Helpers
# ----------------------------
def find_peak_idx(rx):
    """
    Fast cross-correlation using FFT:
    corr[k] = sum_n rx[n+k] * conj(sync[n]), valid for k in [0, len(rx)-len(sync)]
    """
    # Using fftconvolve with 'valid' gives correlation equivalent to
    # np.abs(np.convolve(rx, sync_conj, mode='valid')), but much faster for long vectors.
    corr = fftconvolve(rx, sync_conj[::-1], mode='valid')  # reverse for correlation
    return int(np.argmax(np.abs(corr)))

def extract_regions(rx_len, peak_idx):
    """
    Compute start indices for regions without per-region branching.
    """
    first = peak_idx + FIRST_OFFSET
    # Max possible regions given rx length
    if first >= rx_len:
        return []
    # Compute how many steps fit before running out of samples
    max_by_len = 1 + (rx_len - first - REGION_LEN) // REGION_STEP
    n_regions = int(max(0, min(MAX_REGIONS_PER_FILE, max_by_len)))
    if n_regions == 0:
        return []
    starts = first + REGION_STEP * np.arange(n_regions, dtype=np.int64)
    return starts.tolist()

# ----------------------------
# Process all .sigmf-data files
# ----------------------------
files = sorted([p for p in folder_path.iterdir() if p.suffix == '.sigmf-data'])

saved_data_regions = {}
counter = 1

for fpath in files:
    # Memory-map for speed and low RAM overhead
    try:
        rx_data = np.memmap(fpath, dtype=np.complex64, mode='r')
    except Exception as e:
        print(f"[SKIP] {fpath.name}: memmap failed: {e}")
        continue

    rx_len = rx_data.size
    if rx_len < zc_len:
        print(f"[SKIP] {fpath.name}: RX too short (len={rx_len} < {zc_len}).")
        continue

    # Peak detect with FFT-based correlation
    peak_idx = find_peak_idx(rx_data)
    starts = extract_regions(rx_len, peak_idx)
    if not starts:
        print(f"[SKIP] {fpath.name}: no full regions available after peak={peak_idx}.")
        continue

    # Slice and save regions
    for s in starts:
        e = s + REGION_LEN
        region = np.asarray(rx_data[s:e], dtype=np.complex64)  # memmap slice → ndarray view

        out_name = f"{counter}.mat"
        out_path = base_path / out_name

        # Save as complex128 (your original requirement)
        scipy.io.savemat(out_path.as_posix(), {'chanEstCurrent': region.astype(np.complex128, copy=False)})
        saved_data_regions[out_name] = {
            'source_file': fpath.name,
            'start_index': int(s),
            'peak_idx': int(peak_idx)
        }
        counter += 1

    print(f"[OK] {fpath.name}: saved {len(starts)} regions.")

# Save mapping once
mapping_path = base_path / 'mapping.json'
with mapping_path.open('w') as f:
    json.dump(saved_data_regions, f, indent=2)
print(f"\nDone. Saved {counter-1} regions total. Mapping: {mapping_path}")
