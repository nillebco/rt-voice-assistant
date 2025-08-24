# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "numpy",
#     "silero-vad",
#     "sounddevice",
#     "soundfile",
#     "openai",
#     "tiktoken",
#     "dotenv",
# ]
# ///

from datetime import datetime
import logging

import numpy as np
import soundfile as sf
import sounddevice as sd

from ..bricks.stt.whispercpp import transcribe
from ..bricks.listen import ListenOptions, listen
from ..bricks.vad.silero import process_prob
from ..bricks.llm import get_client, clean_thinking
from ..bricks.frame_processor import Callbacks, FrameProcessor, FrameProcessorOptions
from ..bricks.audio import prepare_for_write
from ..bricks.tts import get_tts_engine, on_startup as on_startup_tts
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("rt_py.cli.transcribe")
logger.setLevel(logging.DEBUG)

on_startup_tts()


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

        client = get_client()
        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": transcription}],
        )
        text = response.choices[0].message.content
        print(f"Response: {text}")

        audible_text = clean_thinking(text)
        tts = get_tts_engine()
        samples, sample_rate = tts.create(audible_text, voice="af_heart")
        sd.play(samples, sample_rate)
        sd.wait()


    def __call__(self, frame: np.ndarray):
        self.frame_processor.process(frame)


if __name__ == "__main__":
    # WHISPER_CPP_DIR="/Users/nilleb/dev/nillebco/whisper-ane/whisper.cpp" uv run -m rt_py.cli
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
