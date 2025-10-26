from datetime import datetime
from typing import Callable

import numpy as np


def sample_process_frame(chunk: np.ndarray):
    """
    Place your real-time logic here. `chunk` shape: (frames, channels).
    This example prints a simple RMS level (dBFS) about once per second.
    """
    print(f"Processing frame: {chunk.shape} {datetime.now()}")


class RMSMeter:
    # 16 because we want to print the message every second
    def __init__(self, every: int = 16):
        self.meter_every = every
        self._meter_accum = 0
        self._meter_now = self.meter_every

    def __call__(self, chunk: np.ndarray):
        self._meter_accum += self.compute_rms(chunk)
        self._meter_now += 1
        if self._meter_now >= self.meter_every:
            print(f"RMS: {self._meter_accum / self.meter_every}")
            self._meter_accum = 0
            self._meter_now = 0

    def compute_rms(self, chunk: np.ndarray):
        x = chunk.astype(np.float32) / np.iinfo(np.int16).max
        rms = np.sqrt(np.mean(x**2) + 1e-12)
        dbfs = 20 * np.log10(rms + 1e-12)
        return dbfs


def multiple_callbacks(callbacks: list[Callable[[np.ndarray], None]]):
    def process_frame(chunk: np.ndarray):
        for callback in callbacks:
            callback(chunk)

    return process_frame
