# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "numpy",
#     "openai-whisper",
#     "silero-vad",
#     "sounddevice",
#     "soundfile",
# ]
# ///

from datetime import datetime
import logging

import numpy as np
import soundfile as sf

from ..bricks.stt.whispercpp import transcribe
from ..bricks.listen import ListenOptions, listen
from ..bricks.vad_silero import process_prob
from ..bricks.frame_processor import Callbacks, FrameProcessor, FrameProcessorOptions

logger = logging.getLogger("rt_py.cli.transcribe")
logger.setLevel(logging.DEBUG)


SR = 16000


def prepare_for_write(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32).reshape(-1)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)

    # remove DC
    x -= np.mean(x)

    # short fades to kill boundary clicks (e.g., VAD cut points)
    fade = int(0.010 * SR)  # 10 ms
    if x.size >= 2 * fade:
        ramp = np.linspace(0.0, 1.0, fade, dtype=np.float32)
        x[:fade] *= ramp
        x[-fade:] *= ramp[::-1]

    # gentle high-pass to reduce rumble (one-pole @ ~80 Hz)
    # y[n] = a*(y[n-1] + x[n] - x[n-1]), a = exp(-2*pi*fc/SR)
    fc = 80.0
    a = np.exp(-2 * np.pi * fc / SR).astype(np.float32)
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


class Transcriber:
    def __init__(self, filename_fmt: str):
        self.frame_processor = FrameProcessor(
            prob_fn=process_prob,
            options=FrameProcessorOptions(
                pre_speech_pad_frames=10,
                redemption_frames=3,
                min_speech_frames=10,
            ),
            cb=Callbacks(
                on_frame_processed=self.on_frame_processed,
                on_vad_misfire=self.on_vad_misfire,
                on_speech_start=self.on_speech_start,
                on_speech_real_start=self.on_speech_real_start,
                on_speech_end=self.on_speech_end,
            ),
        )
        self.filename_fmt = filename_fmt

    def on_frame_processed(self, p_speech: float, frame: np.ndarray):
        pass
        # print(f"Frame processed: {p_speech:.2f}")

    def on_vad_misfire(self):
        logger.info("VAD misfire")

    def on_speech_start(self):
        logger.info("Speech start")

    def on_speech_real_start(self):
        logger.info("Speech real start")

    def on_speech_end(self, frame: np.ndarray):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = self.filename_fmt.format(timestamp)
        
        with sf.SoundFile(
            filename,
            mode="w",
            samplerate=16000,
            channels=1,
            subtype="FLOAT",
        ) as wav:
            wav.write(prepare_for_write(frame))

        transcription = transcribe(
            model="small",
            language="en",
            input_wav_path=filename,
        )
        print(f"Transcription: {transcription}")

    def __call__(self, frame: np.ndarray):
        self.frame_processor.process(frame)


if __name__ == "__main__":
    # WHISPER_CPP_DIR="/Users/nilleb/dev/nillebco/whisper-ane/whisper.cpp" uv run -m rt_py.cli.transcribe
    transcriber = Transcriber(filename_fmt="voice_{}.wav")
    options = ListenOptions(
        samplerate=16000,
        channels=1,
        frames_per_callback=512,
        filename=f"capture_{datetime.now().strftime('%Y%m%d-%H%M%S')}.wav",
        dtype="int16",
        process_frame=transcriber,
    )
    listen(options)
