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

import logging
import os
from datetime import datetime

import numpy as np
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv

from ..bricks.audio import prepare_for_write
from ..bricks.frame_processor import Callbacks, FrameProcessor, FrameProcessorOptions
from ..bricks.listen import ListenOptions, listen
from ..bricks.llm import clean_thinking, get_client, trim_to_budget
from ..bricks.stt.whispercpp import transcribe
from ..bricks.tts import get_tts_engine
from ..bricks.tts import on_startup as on_startup_tts
from ..bricks.vad.silero import process_prob

load_dotenv()

logger = logging.getLogger("rt_py.cli.transcribe")
logger.setLevel(logging.DEBUG)

on_startup_tts()

MODEL = os.getenv("MODEL", "openai/gpt-4o")
URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    f"You are a concise, helpful assistant. Today it's {datetime.now().strftime('%Y-%m-%d')}.",
)
VOICE = os.getenv("VOICE", "af_heart")
LANGUAGE = os.getenv("LANGUAGE", "en-us")

HISTORY = []


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

        client = get_client(url=URL)
        HISTORY.append({"role": "user", "content": transcription})
        messages = trim_to_budget(HISTORY, SYSTEM_PROMPT, budget=6000)
        print(f"Messages: {messages}")
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )
        text = response.choices[0].message.content
        print(f"Response: {text}")

        audible_text = clean_thinking(text)
        HISTORY.append({"role": "assistant", "content": audible_text})
        tts = get_tts_engine()
        samples, sample_rate = tts.create(audible_text, voice=VOICE, lang=LANGUAGE)
        sd.play(samples, sample_rate)
        sd.wait()

    def __call__(self, frame: np.ndarray):
        self.frame_processor.process(frame)


if __name__ == "__main__":
    # WHISPER_CPP_DIR="/Users/nilleb/dev/nillebco/whisper-ane/whisper.cpp" uv run -m rt_voice_assistant.cli
    if not os.path.isdir("audios"):
        os.mkdir("audios")

    transcriber = Transcriber(filename_fmt="audios/voice_{}.wav")
    options = ListenOptions(
        samplerate=16000,
        channels=1,
        frames_per_callback=512,
        filename=f"audios/capture_{datetime.now().strftime('%Y%m%d-%H%M%S')}.wav",
        dtype="int16",
        process_frame=transcriber,
    )
    listen(options)
