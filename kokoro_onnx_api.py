import os
import platform
import tempfile
import urllib.request
from contextlib import asynccontextmanager
import logging
import onnxruntime as ort
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from kokoro_onnx import Kokoro
from pydantic import BaseModel


def download_model_files():
    """Download model files if they don't exist."""
    model_urls = {
        "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
        "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
    }

    for filename, url in model_urls.items():
        if not os.path.exists(filename):
            print(f"Downloading {filename}...")
            try:
                urllib.request.urlretrieve(url, filename)
                print(f"Successfully downloaded {filename}")
            except Exception as e:
                print(f"Error downloading {filename}: {e}")
                return False
        else:
            print(f"{filename} already exists")
    return True

tts = None

def get_tts_engine():
    """Get the TTS engine based on platform."""
    global tts

    if tts is None:
        if platform.system() == "Darwin":
            providers = ["CoreMLExecutionProvider", "CPUExecutionProvider"]
            session = ort.InferenceSession("kokoro-v1.0.onnx", providers=providers)
            tts = Kokoro.from_session(session, voices_path="voices-v1.0.bin")
        else:
            tts = Kokoro(
                model_path="kokoro-v1.0.onnx",
                voices_path="voices-v1.0.bin",
            )
    return tts

# Initialize FastAPI app
app = FastAPI(
    title="Kokoro TTS API",
    description="Text-to-Speech API using Kokoro ONNX",
    root_path="/api/v1",
)


class TTSRequest(BaseModel):
    text: str
    voice: str = "af_heart"  # Default voice


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Download model files on startup."""
    print("Starting up TTS API server...")
    if not download_model_files():
        raise RuntimeError("Failed to download required model files")
    print("Model files ready. TTS API server started successfully.")
    yield


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
            temp_file_path,
            media_type="audio/wav",
            filename="tts_output.wav"
        )

    except Exception as e:
        logging.exception("TTS generation failed")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5555)
