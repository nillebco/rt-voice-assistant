import whisperx


def transcribe(input_wav_path: str, model: str = None, language: str = None):
    device = "cuda"
    batch_size = 4  # reduce if low on GPU mem
    compute_type = "int8"  # change to "int8" if low on GPU mem (may reduce accuracy)

    model = whisperx.load_model(
        model or "tiny", device, compute_type=compute_type, download_root="."
    )

    audio = whisperx.load_audio(input_wav_path)
    result = model.transcribe(audio, batch_size=batch_size)
    return result["segments"]  # before alignment
