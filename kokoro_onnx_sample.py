import os
import platform
import urllib.request

import onnxruntime as ort
import soundfile as sf
from kokoro_onnx import Kokoro


def download_model_files():
    """Download model files if they don't exist."""
    model_urls = {
        "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
        "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
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


def linux():
    return Kokoro(
        model_path="kokoro-v1.0.onnx",
        voices_path="voices-v1.0.bin",
    )


def mac():
    providers = ["CoreMLExecutionProvider", "CPUExecutionProvider"]
    session = ort.InferenceSession("kokoro-v1.0.onnx", providers=providers)
    return Kokoro.from_session(session, voices_path="voices-v1.0.bin")


if __name__ == "__main__":
    # Download model files if they don't exist
    if not download_model_files():
        print("Failed to download required model files. Exiting.")
        exit(1)
    
    if platform.system() == "Darwin":
        tts = mac()
    else:
        tts = linux()

    samples, sample_rate = tts.create(
        "Hello from Kokoro ONNX on macOS.", voice="af_heart"
    )

    sf.write("audio.wav", samples, sample_rate)
    print("Created audio.wav")
