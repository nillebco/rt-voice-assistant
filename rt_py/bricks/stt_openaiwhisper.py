import whisper

def transcribe(model: str, language: str, input_wav_path: str):
    model = whisper.load_model(model)
    result = model.transcribe(input_wav_path)
    return result["text"]
