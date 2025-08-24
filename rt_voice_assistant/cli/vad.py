# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "numpy",
#     "silero-vad",
#     "sounddevice",
#     "soundfile",
#     "webrtcvad",
# ]
# ///

import argparse
from datetime import datetime

import numpy as np

from ..bricks.listen import ListenOptions, listen
from ..bricks.vad.silero import process_prob
from ..bricks.vad.webrtc import process_vad_webrtc


def vad_silero_callback(chunk: np.ndarray):
    is_speech = process_prob(chunk)
    print(f"VAD: {is_speech}")


def vad_webrtc_callback(chunk: np.ndarray):
    is_speech = process_vad_webrtc(chunk)
    print(f"VAD: {is_speech}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vad", type=str, default="silero")
    args = parser.parse_args()

    if args.vad == "webrtc":
        process_frame = vad_webrtc_callback
        frames_per_callback = 480  # 30ms frames @ 16kHz
    elif args.vad == "silero":
        process_frame = vad_silero_callback
        frames_per_callback = 512
    else:
        raise ValueError(f"Invalid VAD: {args.vad}")

    options = ListenOptions(
        samplerate=16000,
        channels=1,
        frames_per_callback=512,
        filename=f"capture_{datetime.now().strftime('%Y%m%d-%H%M%S')}.wav",
        dtype="int16",
        process_frame=vad_silero_callback,
    )
    listen(options)
