# requires: sounddevice soundfile numpy

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

# Global VAD instance (created once)
vad = None


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


def process_vad(chunk: np.ndarray):
    """
    Process the audio chunk using the VAD.
    Ensures WebRTC VAD requirements:
    - 16-bit mono PCM audio
    - Supported sample rates: 8000, 16000, 32000, or 48000 Hz
    - Frame duration: 10, 20, or 30 ms
    """
    global vad
    
    # Initialize VAD once
    if vad is None:
        vad = webrtcvad.Vad()
        vad.set_mode(1)  # Aggressiveness level 0-3
    
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
    
    try:
        is_speech = vad.is_speech(chunk_bytes, SAMPLERATE)
        return is_speech, frame_duration_ms
    except Exception as e:
        print(f"VAD processing error: {e}")
        return False, frame_duration_ms


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

            is_speech, frame_duration = process_vad(chunk)
            print(f"VAD: {is_speech} (frame: {frame_duration}ms)")

    print("\nStopped. File closed.")


if __name__ == "__main__":
    main()
