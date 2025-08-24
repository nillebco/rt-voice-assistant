import numpy as np

SR = 16000


def prepare_for_write(x: np.ndarray, sr: int = SR) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32).reshape(-1)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)

    # remove DC
    x -= np.mean(x)

    # short fades to kill boundary clicks (e.g., VAD cut points)
    fade = int(0.010 * sr)  # 10 ms
    if x.size >= 2 * fade:
        ramp = np.linspace(0.0, 1.0, fade, dtype=np.float32)
        x[:fade] *= ramp
        x[-fade:] *= ramp[::-1]

    # gentle high-pass to reduce rumble (one-pole @ ~80 Hz)
    # y[n] = a*(y[n-1] + x[n] - x[n-1]), a = exp(-2*pi*fc/SR)
    fc = 80.0
    a = np.exp(-2 * np.pi * fc / sr).astype(np.float32)
    y = np.empty_like(x)
    prev_y = np.float32(0.0)
    prev_x = np.float32(0.0)
    for i in range(x.size):
        prev_y = a * (prev_y + x[i] - prev_x)
        y[i] = prev_y
        prev_x = x[i]
    x = x - y  # remove low frequencies

    # keep safe headroom
    peak = np.max(np.abs(x)) or 1.0
    if peak > 0.99:
        x *= 0.99 / peak

    return x
