# requires: sounddevice soundfile numpy silero-vad webrtcvad

import queue
import signal
import sys
from datetime import datetime

import numpy as np
import sounddevice as sd
import soundfile as sf
import webrtcvad

# --- Config ---
SAMPLERATE = 16000  # 44_100 or 48_000 are common, pywebrtcvad uses 8000, 16000, 32000 or 48000 Hz, silero uses 8000 or 16000
CHANNELS = 1  # 1=mono, 2=stereo
BLOCKSIZE = 1024  # frames per callback; smaller = lower latency
DTYPE = "int16"  # matches 16-bit WAV
FILENAME = f"capture_{datetime.now().strftime('%Y%m%d-%H%M%S')}.wav"

# Thread-safe queue to shuttle audio from callback to main thread
q = queue.Queue(maxsize=100)

# Graceful shutdown flag
running = True

# Global VAD instances (created once)
vad_silero = None
silero_iter = None
_silero_buf = np.zeros(0, dtype=np.float32)
SILERO_MIN_SAMPLES = 512 if SAMPLERATE == 16000 else 256

vad_webrtc = None  # for WebRTC VAD


def handle_sigint(sig, frame):
    global running
    running = False


signal.signal(signal.SIGINT, handle_sigint)


def audio_callback(indata, frames, time, status):
    """Called by sounddevice in a high-priority audio thread."""
    if status:
        # Over/underruns, etc.
        print(f"[Audio status] {status!s}", file=sys.stderr)
    # Copy needed because indata is reused by the host
    q.put(indata.copy(), block=False)


def process_chunk(chunk: np.ndarray):
    """
    Place your real-time logic here. `chunk` shape: (frames, channels).
    This example prints a simple RMS level (dBFS) about once per second.
    """
    # Convert int16 -> float32 in [-1, 1]
    x = chunk.astype(np.float32) / np.iinfo(np.int16).max
    rms = np.sqrt(np.mean(x**2) + 1e-12)
    dbfs = 20 * np.log10(rms + 1e-12)
    return dbfs


def process_vad_silero(chunk: np.ndarray) -> bool:
    """
    Stream Silero VAD with 512-sample hops @16 kHz.
    Keeps internal buffer to guarantee min size.
    """
    global vad_silero, silero_iter, _silero_buf

    # Init once
    if vad_silero is None:
        from silero_vad import load_silero_vad, VADIterator
        vad_silero = load_silero_vad()
        silero_iter = VADIterator(vad_silero, sampling_rate=SAMPLERATE)

    # Ensure mono int16 -> float32 [-1, 1] 1-D
    if chunk.ndim > 1:
        chunk = chunk[:, 0]
    if chunk.dtype != np.int16:
        chunk = chunk.astype(np.int16)
    x = chunk.astype(np.float32) / 32768.0

    # Append to rolling buffer
    _silero_buf = np.concatenate([_silero_buf, x])

    speech_detected = False
    # Feed fixed-size slices to Silero (>=512)
    while len(_silero_buf) >= SILERO_MIN_SAMPLES:
        frame = _silero_buf[:SILERO_MIN_SAMPLES]
        _silero_buf = _silero_buf[SILERO_MIN_SAMPLES:]

        # NOTE: do NOT reuse the WebRTC batcher here; call Silero directly
        out = silero_iter(frame, return_seconds=False)
        if out is not None:  # Silero returns dict when a segment closes
            speech_detected = True

    # Do NOT call reset_states() every chunk; only when you want to flush
    return speech_detected


def _is_speech_webrtc(chunk_bytes: list[bytes]):
    try:
        is_speech = vad_webrtc.is_speech(chunk_bytes, SAMPLERATE)
        return is_speech
    except Exception as e:
        print(f"WebRTC VAD processing error: {e}")
        return False


def process_vad_webrtc(chunk: np.ndarray):
    """
    Process the audio chunk using WebRTC VAD.
    Ensures WebRTC VAD requirements:
    - 16-bit mono PCM audio
    - Supported sample rates: 8000, 16000, 32000, or 48000 Hz
    - Frame duration: 10, 20, or 30 ms
    """
    global vad_webrtc

    # Initialize VAD once
    if vad_webrtc is None:
        vad_webrtc = webrtcvad.Vad()
        vad_webrtc.set_mode(1)  # Aggressiveness level 0-3

    # Ensure we have mono audio (take first channel if stereo)
    if chunk.ndim > 1 and chunk.shape[1] > 1:
        chunk = chunk[:, 0]

    # Ensure 16-bit PCM format
    if chunk.dtype != np.int16:
        chunk = chunk.astype(np.int16)
    
    # Calculate frame duration in milliseconds
    frame_duration_ms = (len(chunk) / SAMPLERATE) * 1000
    
    # WebRTC VAD only accepts 10, 20, or 30 ms frames
    # If our frame doesn't match, we need to adjust
    if frame_duration_ms not in [10, 20, 30]:
        # Find the closest supported frame duration
        target_durations = [10, 20, 30]
        closest_duration = min(target_durations, key=lambda x: abs(x - frame_duration_ms))
        
        # Calculate how many samples we need for the target duration
        target_samples = int((closest_duration / 1000) * SAMPLERATE)
        
        # Pad or truncate to match target duration
        if len(chunk) < target_samples:
            # Pad with zeros if too short
            padded_chunk = np.zeros(target_samples, dtype=np.int16)
            padded_chunk[:len(chunk)] = chunk
            chunk = padded_chunk
        else:
            # Truncate if too long
            chunk = chunk[:target_samples]
        
        frame_duration_ms = closest_duration
    
    # Convert to bytes for WebRTC VAD
    chunk_bytes = chunk.tobytes()
    
    return _is_speech_webrtc(chunk_bytes)


def main():
    global running
    print(f"Recording -> {FILENAME}\nPress Ctrl+C to stop.")

    # Open an incremental writer; no need to know total duration
    with (
        sf.SoundFile(
            FILENAME,
            mode="w",
            samplerate=SAMPLERATE,
            channels=CHANNELS,
            subtype="PCM_16",
        ) as wav,
        sd.InputStream(
            samplerate=SAMPLERATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=BLOCKSIZE,
            callback=audio_callback,
            latency="low",  # hint; driver may choose nearest
        ),
    ):
        meter_accum = 0
        meter_every = SAMPLERATE // BLOCKSIZE  # ~1s

        i = 0
        while running:
            try:
                chunk = q.get(timeout=0.5)  # ndarray[int16] (frames, channels)
            except queue.Empty:
                continue

            # Write chunk to disk (non-blocking wrt audio thread)
            wav.write(chunk)

            # Live processing hook
            dbfs = process_chunk(chunk)
            meter_accum += dbfs
            i += 1
            if i % meter_every == 0:
                avg_dbfs = meter_accum / meter_every
                print(f"Level ~ {avg_dbfs:6.1f} dBFS")
                meter_accum = 0

            is_speech = process_vad_silero(chunk)
            if is_speech:
                print("Silero: Speech detected")

            is_speech = process_vad_webrtc(chunk)
            if is_speech:
                print("WebRTC: Speech detected")

    print("\nStopped. File closed.")


if __name__ == "__main__":
    main()
