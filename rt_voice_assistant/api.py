import argparse
import logging
import os
import subprocess
import tempfile
import uuid
from contextlib import asynccontextmanager
from tempfile import NamedTemporaryFile

import soundfile as sf
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    File,
    Query,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.websockets import WebSocketState

from .bricks.stt.whispercpp import transcribe
from .bricks.tts import get_tts_engine
from .bricks.tts import on_startup as on_startup_tts

load_dotenv()

app = FastAPI(
    title="RealTime Voice Assistant API",
    description="RealTime Voice Assistant API",
    root_path="/api/v1",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    on_startup_tts()
    yield


class TTSRequest(BaseModel):
    text: str
    voice: str = "af_heart"  # Default voice


async def _prepare_wav_input(file: UploadFile):
    """
    Prepares a WAV file for transcription.
    If the input file is not WAV, it converts it to WAV using ffmpeg.
    Returns the path to the temporary WAV file and the path of the original temp file if conversion occurred.
    """
    original_temp_name = None
    input_wav_path = None

    # Check if it's already a WAV file
    if file.content_type in ["audio/wav", "audio/x-wav"]:
        with NamedTemporaryFile(delete=False, suffix=".wav") as temp_input_wav:
            temp_input_wav.write(await file.read())
            temp_input_wav.flush()
            input_wav_path = temp_input_wav.name
    else:
        # Handle other audio formats (WebM, MP3, MP4, etc.)
        # Determine file extension from filename or content type
        if file.filename:
            original_suffix = os.path.splitext(file.filename)[1]
        elif file.content_type:
            # Map common content types to extensions
            content_type_to_ext = {
                "audio/webm": ".webm",
                "audio/mp4": ".m4a",
                "audio/mpeg": ".mp3",
                "audio/ogg": ".ogg",
                "audio/flac": ".flac",
                "audio/aac": ".aac",
            }
            original_suffix = content_type_to_ext.get(file.content_type, ".tmp")
        else:
            original_suffix = ".tmp"

        with NamedTemporaryFile(
            delete=False, suffix=original_suffix
        ) as temp_original_file:
            temp_original_file.write(await file.read())
            temp_original_file.flush()
            original_temp_name = temp_original_file.name

        with NamedTemporaryFile(delete=False, suffix=".wav") as temp_converted_wav:
            input_wav_path = temp_converted_wav.name

        # FFmpeg command to convert any audio format to WAV
        # -f format detection is automatic, so we don't need to specify input format
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-i",
            original_temp_name,  # Input file
            "-ar",
            "16000",  # Sample rate: 16kHz
            "-ac",
            "1",  # Channels: mono
            "-c:a",
            "pcm_s16le",  # Audio codec: 16-bit PCM
            input_wav_path,
        ]

        logging.info(
            f"Converting {file.content_type or 'unknown'} file to WAV: {' '.join(ffmpeg_cmd)}"
        )

        try:
            process_handle = subprocess.run(
                ffmpeg_cmd, check=True, capture_output=True, text=True
            )
            logging.info(f"FFmpeg conversion successful: {process_handle.stdout}")
        except subprocess.CalledProcessError as e:
            logging.error(f"FFmpeg conversion failed: {e.stderr}")
            raise

    return input_wav_path, original_temp_name


@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech and return audio file."""
    try:
        tts = get_tts_engine()

        samples, sample_rate = tts.create(request.text, voice=request.voice)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            sf.write(temp_file.name, samples, sample_rate)
            temp_file_path = temp_file.name

        return FileResponse(
            temp_file_path, media_type="audio/wav", filename="tts_output.wav"
        )

    except Exception as e:
        logging.exception("TTS generation failed")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@app.post("/audio/transcriptions")
async def transcribe_audio(
    file: UploadFile = File(...),
    model: str = Query("base"),
    language: str = Query("en"),
):
    input_wav_path, original_temp_file_path = await _prepare_wav_input(file)

    return {
        "text": transcribe(
            model=model,
            language=language,
            input_wav_path=input_wav_path,
        ),
    }


@app.websocket("/wss/audio/transcriptions")
async def websocket_audio(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_bytes()
            if not data:
                break

            utterance_filename = f"data/out-{uuid.uuid4()}.wav"
            with open(utterance_filename, "wb") as f:
                f.write(data)

            full_text = transcribe(
                model="small",
                language="en",
                input_wav_path=utterance_filename,
            )

            message_to_send = {"text": full_text}
            await websocket.send_text(str(message_to_send))

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    finally:
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()


if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(
        description="Run the RealTime Voice Assistant API server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5555,
        help="Port to run the server on (default: 5555)",
    )
    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port)
