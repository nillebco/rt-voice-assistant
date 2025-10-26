import logging
import os

import numpy as np
import torch
from silero_vad import load_silero_vad, VADIterator

vad_silero = None
silero_iter = None
_silero_buf = np.zeros(0, dtype=np.float32)

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

SAMPLERATE = 16000


# def as_float32(chunk: np.ndarray) -> np.ndarray:
#     # Ensure mono int16 -> float32 [-1, 1] 1-D
#     if chunk.ndim > 1:
#         chunk = chunk[:, 0]
#     if chunk.dtype != np.int16:
#         chunk = chunk.astype(np.int16)
#     return chunk.astype(np.float32) / 32768.0


def as_float32(chunk: np.ndarray) -> np.ndarray:
    """Return mono float32 in [-1,1] without unnecessary requantization."""
    # mono
    if chunk.ndim > 1:
        chunk = chunk[:, 0]

    if chunk.dtype == np.float32:
        x = chunk
    elif np.issubdtype(chunk.dtype, np.floating):
        x = chunk.astype(np.float32)
    elif chunk.dtype == np.int16:
        # Map [-32768, 32767] -> [-1, 1)
        x = chunk.astype(np.float32) / 32768.0
    elif chunk.dtype == np.int32:
        x = chunk.astype(np.float32) / 2147483648.0  # 2**31
    elif chunk.dtype == np.uint8:
        # 8-bit PCM is unsigned: [0,255] -> [-1,1)
        x = (chunk.astype(np.float32) - 128.0) / 128.0
    else:
        # Fallback: normalize by max possible magnitude
        maxmag = np.max(np.abs(chunk)) or 1.0
        x = chunk.astype(np.float32) / maxmag

    return np.clip(x, -1.0, 1.0)


def process_bool(chunk: np.ndarray, sampling_rate: int = SAMPLERATE) -> bool:
    """
    Stream Silero VAD with 512-sample hops @16 kHz.
    Keeps internal buffer to guarantee min size.
    The chunk is expected to be a single channel, mono. 512 samples for 16kHz, 256 for 8kHz.
    """
    global vad_silero, silero_iter, _silero_buf

    # Init once
    if vad_silero is None:
        vad_silero = load_silero_vad()
        silero_iter = VADIterator(vad_silero, sampling_rate=sampling_rate)

    x = as_float32(chunk)

    # Append to rolling buffer
    _silero_buf = np.concatenate([_silero_buf, x])

    speech_detected = False
    logger.debug(f"Processing chunk: {len(_silero_buf)} samples")
    # Feed fixed-size slices to Silero (>=512)
    SILERO_MIN_SAMPLES = 512 if sampling_rate == 16000 else 256

    while len(_silero_buf) >= SILERO_MIN_SAMPLES:
        frame = _silero_buf[:SILERO_MIN_SAMPLES]
        _silero_buf = _silero_buf[SILERO_MIN_SAMPLES:]

        out = silero_iter(frame, return_seconds=False)
        logger.debug(f"VAD: {out}")
        if out is not None:  # Silero returns dict when a segment closes
            speech_detected = True

    return speech_detected


def _get_prob(chunk: np.ndarray, sampling_rate: int = SAMPLERATE) -> float:
    if not torch.is_tensor(chunk):
        try:
            chunk = torch.Tensor(chunk)
        except Exception:
            logger.exception("Error casting audio to tensor")
            raise TypeError("Audio cannot be casted to tensor. Cast it manually")

    return vad_silero(chunk, sampling_rate).item()


def process_prob(chunk: np.ndarray, sampling_rate: int = SAMPLERATE) -> float:
    """
    Stream Silero VAD with 512-sample hops @16 kHz.
    Keeps internal buffer to guarantee min size.
    The chunk is expected to be a single channel, mono. 512 samples for 16kHz, 256 for 8kHz.
    """
    global vad_silero, _silero_buf

    # Init once
    if vad_silero is None:
        vad_silero = load_silero_vad()

    # Ensure mono int16 -> float32 [-1, 1] 1-D
    if chunk.ndim > 1:
        chunk = chunk[:, 0]
    if chunk.dtype != np.int16:
        chunk = chunk.astype(np.int16)
    x = chunk.astype(np.float32) / 32768.0

    # Append to rolling buffer
    _silero_buf = np.concatenate([_silero_buf, x])

    logger.debug(f"Processing chunk: {len(_silero_buf)} samples")
    # Feed fixed-size slices to Silero (>=512)
    SILERO_MIN_SAMPLES = 512 if sampling_rate == 16000 else 256

    while len(_silero_buf) >= SILERO_MIN_SAMPLES:
        frame = _silero_buf[:SILERO_MIN_SAMPLES]
        _silero_buf = _silero_buf[SILERO_MIN_SAMPLES:]

        out = _get_prob(frame, sampling_rate=sampling_rate)
        logger.debug(f"VAD: {out}")

    return out
