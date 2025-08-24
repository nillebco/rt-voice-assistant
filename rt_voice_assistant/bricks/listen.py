import queue
import signal
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

import numpy as np
import sounddevice as sd
import soundfile as sf


@dataclass
class ListenOptions:
    samplerate: int = 16000
    channels: int = 1
    frames_per_callback: int = 1024
    filename: str = f"capture_{datetime.now().strftime('%Y%m%d-%H%M%S')}.wav"
    dtype: str = "int16"
    process_frame: Callable[[np.ndarray], None] = None


DEFAULT_SAMPLING_RATE = 16000
DEFAULT_FRAMES_PER_CALLBACK = 1024
DEFAULT_MAX_SECONDS_CACHE = 10
MAX_SIZE = int(
    DEFAULT_MAX_SECONDS_CACHE * DEFAULT_SAMPLING_RATE / DEFAULT_FRAMES_PER_CALLBACK
)

# Thread-safe queue to shuttle audio from callback to main thread
q = queue.Queue(maxsize=MAX_SIZE)

# Graceful shutdown flag
running = True
processing = False

def handle_sigint(sig, frame):
    global running
    running = False


signal.signal(signal.SIGINT, handle_sigint)


def audio_callback(indata, frames, time, status):
    """Called by sounddevice in a high-priority audio thread."""
    if status:
        # Over/underruns, etc.
        print(f"[Audio status] {status!s}", file=sys.stderr)

    if processing:
        return

    # Copy needed because indata is reused by the host
    try:
        q.put_nowait(indata.copy())
    except queue.Full:
        print("WARN: Queue is full, dropping audio data.", file=sys.stderr)
        # Drop the oldest and enqueue the newest (bounded "ring buffer")
        try:
            _ = q.get_nowait()
        except queue.Empty:
            pass
        # Last attempt; if it fails again, we just drop this frame.
        try:
            q.put_nowait(indata.copy())
        except queue.Full:
            pass  # drop


def listen(options: ListenOptions):
    global running, processing
    print(f"Recording -> {options.filename}\nPress Ctrl+C to stop.")
    if not options.process_frame:
        print("WARN: No process_frame callback provided.")

    # Open an incremental writer; no need to know total duration
    with (
        sf.SoundFile(
            options.filename,
            mode="w",
            samplerate=options.samplerate,
            channels=options.channels,
            subtype="PCM_16",
        ) as wav,
        sd.InputStream(
            samplerate=options.samplerate,
            channels=options.channels,
            dtype=options.dtype,
            blocksize=options.frames_per_callback,
            callback=audio_callback,
            latency="low",  # hint; driver may choose nearest
        ),
    ):
        while running:
            try:
                chunk = q.get(timeout=0.5)  # ndarray[int16] (frames, channels)
            except queue.Empty:
                continue

            # Write chunk to disk (non-blocking wrt audio thread)
            wav.write(chunk)

            if options.process_frame:
                processing = True
                options.process_frame(chunk)
                processing = False

    print("\nStopped. File closed.")
