import whisperx

def transcribe(model: str, language: str, input_wav_path: str):
    device = "cuda"
    batch_size = 4 # reduce if low on GPU mem
    compute_type = "int8" # change to "int8" if low on GPU mem (may reduce accuracy)

    model = whisperx.load_model(model, device, compute_type=compute_type, download_root=".")

    audio = whisperx.load_audio(input_wav_path)
    result = model.transcribe(audio, batch_size=batch_size)
    return(result["segments"]) # before alignment
