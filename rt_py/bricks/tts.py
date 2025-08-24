import os
import platform
import onnxruntime as ort
import urllib.request
from kokoro_onnx import Kokoro

FOLDER = "models"
def download_model_files():
    """Download model files if they don't exist."""
    model_urls = {
        "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
        "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
    }

    for filename, url in model_urls.items():
        fpath = os.path.join(FOLDER, filename)
        if not os.path.exists(fpath):
            print(f"Downloading {filename}...")
            try:
                urllib.request.urlretrieve(url, fpath)
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
            session = ort.InferenceSession(os.path.join(FOLDER, "kokoro-v1.0.onnx"), providers=providers)
            tts = Kokoro.from_session(session, voices_path=os.path.join(FOLDER, "voices-v1.0.bin"))
        else:
            tts = Kokoro(
                model_path=os.path.join(FOLDER, "kokoro-v1.0.onnx"),
                voices_path=os.path.join(FOLDER, "voices-v1.0.bin"),
            )
    return tts

def on_startup():
    if not download_model_files():
        raise RuntimeError("Failed to download required model files")
    get_tts_engine()
