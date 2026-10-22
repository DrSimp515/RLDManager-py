from __future__ import annotations
import struct
import threading
import os
from typing import Optional, Callable


def _rst(script: bytes) -> int:
    return struct.unpack_from("<I", script, 0x10)[0]


def _quick_filter(seed: int, rst: int) -> bool:
    state = seed & 0xFFFFFFFF
    slots = {0: 0, 1: 0, 0x18D: 0}
    for i in range(0x18E):
        if i in slots:
            product = (state * 0x10DCD + 1) & 0xFFFFFFFF
            slots[i] = (state & 0xFFFF0000) | ((product >> 16) & 0xFFFF)
        state = (state * 0x1C587629 + 0x10DCE) & 0xFFFFFFFF

    mixed = ((slots[1] ^ slots[0]) & 0x7FFFFFFF) ^ slots[0]
    carry = mixed & 1
    mixed = (mixed >> 1) & 0x7FFFFFFF
    if carry:
        mixed ^= 0x9908B0DF
    mixed ^= slots[0x18D]
    mixed ^= (mixed >> 11)
    mixed ^= (mixed & 0xFF3A58AD) << 7
    mixed ^= (mixed & 0xFFFFDF8C) << 15
    key = ((mixed >> 18) ^ mixed ^ seed) & 0xFFFFFFFF
    return (key ^ rst) < 0xF


def _scan_python(script: bytes, stop: threading.Event, on_progress: Optional[Callable]) -> Optional[int]:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from rld_engine import RLD

    rst = _rst(script)
    total = 0xFFFFFFFF
    workers = os.cpu_count() or 4
    chunk = 4096

    def test_range(start: int, end: int) -> Optional[int]:
        for seed in range(start, end):
            if stop.is_set():
                return None
            if _quick_filter(seed, rst):
                try:
                    r = RLD(bytes(script), seed)
                    if len(r.import_strings()) >= 2:
                        return seed
                except Exception:
                    pass
        return None

    with ThreadPoolExecutor(max_workers=workers) as pool:
        cursor = 0
        while cursor < total and not stop.is_set():
            futures = []
            for _ in range(workers):
                if cursor >= total:
                    break
                end = min(cursor + chunk, total)
                futures.append(pool.submit(test_range, cursor, end))
                cursor = end
            for future in as_completed(futures):
                if stop.is_set():
                    return None
                result = future.result()
                if result is not None:
                    stop.set()
                    return result
            if on_progress:
                on_progress(cursor, total)
    return None


def _build_numba_scanner():
    import numpy as np
    from numba import njit, prange

    @njit(parallel=True, cache=True, fastmath=True)
    def _batch(seeds: np.ndarray, rst: np.uint32) -> np.int64:
        hit = np.int64(-1)
        for i in prange(len(seeds)):
            if hit >= 0:
                continue
            seed = np.uint32(seeds[i])
            state = seed
            v0 = np.uint32(0)
            v1 = np.uint32(0)
            v18d = np.uint32(0)
            for j in range(np.int32(0x18E)):
                product = np.uint32(state * np.uint32(0x10DCD) + np.uint32(1))
                val = (state & np.uint32(0xFFFF0000)) | (product >> np.uint16(16))
                if j == 0:
                    v0 = val
                elif j == 1:
                    v1 = val
                elif j == np.int32(0x18D):
                    v18d = val
                state = state * np.uint32(0x1C587629) + np.uint32(0x10DCE)
            mixed = ((v1 ^ v0) & np.uint32(0x7FFFFFFF)) ^ v0
            carry = mixed & np.uint32(1)
            mixed = (mixed >> np.uint32(1)) & np.uint32(0x7FFFFFFF)
            if carry:
                mixed ^= np.uint32(0x9908B0DF)
            mixed ^= v18d
            mixed ^= (mixed >> np.uint32(11))
            mixed ^= (mixed & np.uint32(0xFF3A58AD)) << np.uint32(7)
            mixed ^= (mixed & np.uint32(0xFFFFDF8C)) << np.uint32(15)
            key = ((mixed >> np.uint32(18)) ^ mixed ^ seed)
            if (key ^ rst) < np.uint32(0xF):
                hit = np.int64(seed)
        return hit

    def scan(script: bytes, stop: threading.Event, on_progress: Optional[Callable]) -> Optional[int]:
        from rld_engine import RLD
        rst = np.uint32(_rst(script))
        total = 0xFFFFFFFF
        batch = 1 << 20
        cursor = 0
        while cursor < total and not stop.is_set():
            end = min(cursor + batch, total)
            seeds = np.arange(cursor, end, dtype=np.uint32)
            hit = _batch(seeds, rst)
            if hit >= 0:
                seed = int(hit)
                try:
                    r = RLD(bytes(script), seed)
                    if len(r.import_strings()) >= 2:
                        stop.set()
                        return seed
                except Exception:
                    pass
            cursor = end
            if on_progress:
                on_progress(cursor, total)
        return None

    return scan


_CUDA_KERNEL = r"""
extern "C" __global__
void rld_key_filter(
    const unsigned int* seeds,
    unsigned int rst,
    unsigned int* out,
    int n
) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= n || out[0] != 0xFFFFFFFFu) return;

    unsigned int seed = seeds[tid];
    unsigned int state = seed;
    unsigned int v0 = 0, v1 = 0, v18d = 0;

    for (int i = 0; i < 0x18E; i++) {
        unsigned int product = state * 0x10DCDu + 1u;
        unsigned int val = (state & 0xFFFF0000u) | ((product >> 16) & 0xFFFFu);
        if (i == 0)     v0   = val;
        if (i == 1)     v1   = val;
        if (i == 0x18D) v18d = val;
        state = state * 0x1C587629u + 0x10DCEu;
    }

    unsigned int mixed = ((v1 ^ v0) & 0x7FFFFFFFu) ^ v0;
    unsigned int carry = mixed & 1u;
    mixed = (mixed >> 1) & 0x7FFFFFFFu;
    if (carry) mixed ^= 0x9908B0DFu;
    mixed ^= v18d;
    mixed ^= (mixed >> 11);
    mixed ^= (mixed & 0xFF3A58ADu) << 7;
    mixed ^= (mixed & 0xFFFFDF8Cu) << 15;
    unsigned int key = (mixed >> 18) ^ mixed ^ seed;

    if ((key ^ rst) < 0xFu)
        atomicCAS(out, 0xFFFFFFFFu, seed);
}
"""

def _build_cuda_scanner():
    import cupy as cp
    import numpy as np
    kernel = cp.RawKernel(_CUDA_KERNEL, "rld_key_filter")

    def scan(script: bytes, stop: threading.Event, on_progress: Optional[Callable]) -> Optional[int]:
        from rld_engine import RLD
        rst = np.uint32(_rst(script))
        out = cp.full(1, 0xFFFFFFFF, dtype=cp.uint32)
        total = 0xFFFFFFFF
        batch = 1 << 23
        threads = 256
        cursor = 0
        while cursor < total and not stop.is_set():
            end = min(cursor + batch, total)
            seeds_gpu = cp.asarray(np.arange(cursor, end, dtype=np.uint32))
            n = int(end - cursor)
            blocks = (n + threads - 1) // threads
            kernel((blocks,), (threads,), (seeds_gpu, rst, out, np.int32(n)))
            cp.cuda.Stream.null.synchronize()
            hit = int(out[0].get())
            if hit != 0xFFFFFFFF:
                try:
                    r = RLD(bytes(script), hit)
                    if len(r.import_strings()) >= 2:
                        stop.set()
                        return hit
                except Exception:
                    out[0] = cp.uint32(0xFFFFFFFF)
            cursor = end
            if on_progress:
                on_progress(cursor, total)
        return None

    return scan


_active_backend: str = ""
_active_scan = None


def _resolve_backend():
    global _active_backend, _active_scan
    if _active_scan is not None:
        return

    try:
        import cupy as cp
        cp.array([1])
        _active_scan = _build_cuda_scanner()
        _active_backend = "cuda"
        return
    except Exception:
        pass

    try:
        import numba  # noqa
        import numpy  # noqa
        _active_scan = _build_numba_scanner()
        _active_backend = "numba"
        return
    except Exception:
        pass

    _active_scan = _scan_python
    _active_backend = "python"


def active_backend() -> str:
    _resolve_backend()
    return _active_backend


def scan(script: bytes, stop: threading.Event, on_progress: Optional[Callable] = None) -> Optional[int]:
    _resolve_backend()
    return _active_scan(script, stop, on_progress)
