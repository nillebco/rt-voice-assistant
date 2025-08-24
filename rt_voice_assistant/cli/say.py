# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "onnxruntime",
#     "kokoro-onnx",
#     "sounddevice",
# ]
# ///

import os
import signal
import sys

import sounddevice as sd

from ..bricks.tts import get_tts_engine

VOICE=os.getenv("VOICE", "af_heart")
LANGUAGE=os.getenv("LANGUAGE", "en-us")

tts = get_tts_engine()
running = True


def handle_sigint(sig, frame):
    global running
    running = False


signal.signal(signal.SIGINT, handle_sigint)

if len(sys.argv) > 1:
    text = " ".join(sys.argv[1:])
    samples, sample_rate = tts.create(text, voice=VOICE, language=LANGUAGE)
    sd.play(samples, sample_rate)
    sd.wait()
    exit(0)

print("Press Ctrl+D or enter an empty line to exit.")
while running:
    text = sys.stdin.readline().strip()
    if not text:
        break

    samples, sample_rate = tts.create(text, voice=VOICE, language=LANGUAGE)
    sd.play(samples, sample_rate)
    sd.wait()
