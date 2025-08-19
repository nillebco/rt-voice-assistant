import whisper


def transcribe(input_wav_path: str, model: str = None, language: str = None):
    model = whisper.load_model(model or "tiny")
    result = model.transcribe(input_wav_path)
    return result["text"]
