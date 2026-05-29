import os
import sys
import json
import math
import random
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import scipy.io


# =========================
# Configurable defaults
# =========================
DEFAULT_EXTS = (".mat", ".sigmf-data")


# =========================
# Utilities
# =========================
def rms_normalize(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    p = np.mean(np.abs(x) ** 2)
    return x / (np.sqrt(p) + eps)


def _load_mat_fast(fp: Path) -> Optional[np.ndarray]:
    """
    Load complex waveform from .mat with minimal overhead.
    Tries 'simplify_cells=True' when available (SciPy >= 1.7).
    Accepts 'f_sig' (your key) or 'waveform'.
    Returns complex64 1D array or None.
    """
    try:
        try:
            mat = scipy.io.loadmat(fp, simplify_cells=True)  # SciPy >=1.7
        except TypeError:
            mat = scipy.io.loadmat(fp)  # fallback
        key = 'f_sig' if 'f_sig' in mat else ('waveform' if 'waveform' in mat else None)
        if key is None:
            return None
        arr = np.asarray(mat[key]).squeeze()
        if arr.ndim == 0:
            return None
        # Cast to complex64
        if np.iscomplexobj(arr):
            return arr.astype(np.complex64, copy=False)
        else:
            return arr.astype(np.float32, copy=False).astype(np.complex64)
    except Exception:
        return None


def _load_sigmf_memmap(fp: Path) -> Optional[np.memmap]:
    try:
        return np.memmap(fp, dtype=np.complex64, mode='r')
    except Exception:
        return None


def load_waveform(fp: Path) -> Optional[np.ndarray]:
    if fp.suffix == ".mat":
        return _load_mat_fast(fp)
    if fp.suffix == ".sigmf-data":
        mm = _load_sigmf_memmap(fp)
        if mm is None:
            return None
        # Return a view, not a copy
        return np.asarray(mm)
    return None


def gather_class_files(class_dir: Path, exts: Tuple[str, ...]) -> List[Path]:
    files: List[Path] = []
    for ext in exts:
        files.extend(class_dir.rglob(f"*{ext}"))
    files.sort()
    return files


def _vectorized_sample_indices(total_len: int, sample_size: int, n: int, rng: np.random.Generator) -> np.ndarray:
    """
    Fast vectorized random start indices for windows of size 'sample_size'
    within a 1D array of 'total_len'. Returns shape (n,) int array.
    """
    max_start = total_len - sample_size
    if max_start < 0:
        return np.empty(0, dtype=np.int64)
    # Allow replacement across windows for speed/variety
    return rng.integers(0, max_start + 1, size=n, dtype=np.int64)


# =========================
# Worker
# =========================
def _build_one_split_for_class(
    split_idx: int,
    cname: str,
    files: List[str],
    input_root: str,
    output_root: str,
    num_per_class: int,
    sample_size: int,
    seed: int,
    normalize: bool,
) -> Dict[str, int]:
    """
    Worker executed in a subprocess: builds one split for one class.
    Returns a dict with stats for logging.
    """
    rng = np.random.default_rng(seed + split_idx * 9973 + hash(cname) % 10_000_000)

    out_dir = Path(output_root) / f"split_{split_idx}" / cname
    out_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    trials = 0
    max_trials = num_per_class * 80  # safety limit

    # Pre-shuffle files for locality
    local_files = list(files)
    rng.shuffle(local_files)

    # Batch size: how many windows we try to get from a single loaded file
    # Larger batch reduces loader overhead substantially
    PER_FILE_BATCH = min(64, max(8, num_per_class // 8))

    fcount = len(local_files)
    fidx = 0

    while saved < num_per_class and trials < max_trials and fcount:
        src = Path(local_files[fidx])
        fidx = (fidx + 1) % fcount

        wf = load_waveform(src)
        trials += 1
        if wf is None or wf.size < sample_size:
            continue

        # Vectorized sampling of multiple windows from this file
        n_need = min(PER_FILE_BATCH, num_per_class - saved)
        starts = _vectorized_sample_indices(wf.size, sample_size, n_need, rng)
        if starts.size == 0:
            continue

        # Save windows
        # Construct a stable prefix for file identity
        try:
            rel = src.relative_to(input_root)
            safe_prefix = "__".join(rel.parts)
        except Exception:
            safe_prefix = src.name

        for start in starts:
            window = wf[start:start + sample_size]
            if normalize:
                window = rms_normalize(window)

            out_name = f"{safe_prefix}__s{saved}.mat"
            out_path = out_dir / out_name
            try:
                scipy.io.savemat(out_path, {'waveform': window.reshape(sample_size, 1)})
                saved += 1
                if saved >= num_per_class:
                    break
            except Exception:
                # Skip bad saves and continue
                continue

    return {
        "split": split_idx,
        "class": cname,
        "saved": saved,
        "target": num_per_class,
        "trials": trials,
        "files": fcount,
    }


# =========================
# Orchestrator
# =========================
def create_window_splits_1024_fast(
    input_root: str,
    output_root: str,
    num_splits: int = 27,
    num_per_class: int = 500,
    sample_size: int = 1024,
    seed: int = 813,
    normalize: bool = True,
    exts: Tuple[str, ...] = DEFAULT_EXTS,
    max_workers: Optional[int] = None,
) -> None:
    """
    Faster parallel version:
      - Parallelizes per (split, class) using processes
      - Memmaps .sigmf-data; optimized .mat loading
      - Vectorized random window sampling in batches per file
    """
    input_root_p = Path(input_root)
    output_root_p = Path(output_root)
    if not input_root_p.is_dir():
        raise FileNotFoundError(f"Input root does not exist: {input_root}")

    # Discover class dirs
    class_dirs = [p for p in input_root_p.iterdir() if p.is_dir()]
    if not class_dirs:
        raise RuntimeError(f"No class directories found in {input_root}")

    # Build file pools per class
    class_file_pools: Dict[str, List[str]] = {}
    for cdir in class_dirs:
        files = gather_class_files(cdir, exts)
        class_file_pools[cdir.name] = [str(f) for f in files]

    # Submit tasks
    tasks = []
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        for split_idx in range(1, num_splits + 1):
            for cname, files in class_file_pools.items():
                if not files:
                    print(f"[WARN] Class '{cname}' has 0 files; split {split_idx} will be empty.")
                    continue
                tasks.append(
                    ex.submit(
                        _build_one_split_for_class,
                        split_idx, cname, files,
                        str(input_root_p), str(output_root_p),
                        num_per_class, sample_size, seed, normalize
                    )
                )

        # Collect results
        total_saved = 0
        for fut in as_completed(tasks):
            res = fut.result()
            total_saved += res.get("saved", 0)
            s, c, sv, tgt, tr, nf = (
                res.get("split"), res.get("class"), res.get("saved"),
                res.get("target"), res.get("trials"), res.get("files")
            )
            print(f"[split {s:02d}] {c}: {sv}/{tgt} (trials={tr}, files={nf})")

    print("\nAll splits complete.")
    print(f"Output root: {output_root_p}")


# =========================
# Example run
# =========================
if __name__ == "__main__":
    create_window_splits_1024_fast(
        input_root="/home/sp33752/spenser/trumpet/Measure-Once-Train-Often/data",
        output_root="/home/sp33752/spenser/t-prime-ext/inference_set_908",
        num_splits=27,
        num_per_class=500,
        sample_size=1024,
        seed=813,
        normalize=True,
        max_workers=os.cpu_count(),  # or a smaller number if I/O bound
    )
