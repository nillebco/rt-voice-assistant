import os
import logging
import json
import subprocess
import uuid

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def safe_decode(data: bytes) -> str:
    try:
        return data.decode("utf-8", errors="replace")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


def safe_get_text(stream: bytes) -> str:
    try:
        text = safe_decode(stream) if stream else ""
    except Exception as decode_e:
        logger.error(f"Error decoding process output: {decode_e}")
        text = str(stream) if stream else ""
    return text


def read_transcription(json_file_path: str) -> str:
    try:
        with open(json_file_path, "r", encoding="utf-8") as out_file:
            file_content = out_file.read()
            logger.info(f"JSON file content length: {len(file_content)}")
            transcription_data = json.loads(file_content)
            transcription = transcription_data["transcription"][0]["text"]
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error reading JSON file: {e}")
        # Try to read as bytes and decode with error handling
        with open(json_file_path, "rb") as out_file:
            file_content = out_file.read()
            logger.info(f"JSON file bytes length: {len(file_content)}")
            # Try to decode with error handling
            try:
                decoded_content = file_content.decode("utf-8", errors="replace")
                transcription_data = json.loads(decoded_content)
                transcription = transcription_data["transcription"][0]["text"]
                logger.warning("Successfully decoded JSON with replacement characters")
            except Exception as decode_e:
                logger.error(f"Failed to decode JSON even with replacement: {decode_e}")
                raise
    return transcription


def execute_whisper(cmd: list[str]):
    try:
        process_handle = subprocess.run(
            cmd, check=True, capture_output=True, text=False
        )
    except subprocess.CalledProcessError as e:
        error_message = "Whisper CLI failed"
        if e.cmd:
            if e.cmd[0] == "ffmpeg":
                error_message = f"ffmpeg conversion failed: {e.stderr if e.stderr else 'Unknown error'}"
                logger.error(
                    f"FFmpeg conversion failed: {e.stderr if e.stderr else 'Unknown error'}"
                )
            elif e.cmd[0] == cmd[0]:
                error_message = (
                    f"Whisper CLI failed: {e.stderr if e.stderr else 'Unknown error'}"
                )
                logger.error(
                    f"Whisper CLI failed: {e.stderr if e.stderr else 'Unknown error'}"
                )
        raise ValueError(error_message)
    except Exception as e:
        logger.exception("Unexpected error during transcription")
        raise ValueError(f"An unexpected error occurred: {str(e)}")
    return process_handle


def transcribe(
    model: str, language: str, input_wav_path: str, whisper_cpp_dir: str = None
):
    WHISPER_CPP_DIR = whisper_cpp_dir or os.getenv("WHISPER_CPP_DIR", "./whisper.cpp")

    WHISPER_MODEL_FMT = f"{WHISPER_CPP_DIR}/models/ggml-" "{model}.{language}.bin"
    WHISPER_BINARY = os.getenv(
        "WHISPER_BINARY", f"{WHISPER_CPP_DIR}/build/bin/whisper-cli"
    )
    DEFAULT_MODEL = "small"  # Default model to use when whisper-1 is specified

    output_prefix = f"out-{uuid.uuid4()}"

    actual_model = DEFAULT_MODEL if model == "whisper-1" else model
    model_path = WHISPER_MODEL_FMT.format(model=actual_model, language=language)
    model_path = WHISPER_MODEL_FMT.format(model=actual_model, language=language)
    if not os.path.exists(model_path):
        raise ValueError(
            f"Model '{model}' for language '{language}' does not exist. Please check the model name and language."
        )

    cmd = [
        WHISPER_BINARY,
        "-m",
        model_path,
        "-f",
        input_wav_path,
        "-ojf",
        "-of",
        output_prefix,
        "-l",
        language,
    ]

    logger.info(" ".join(cmd))

    try:
        process_handle = execute_whisper(cmd)
        process_handle.check_returncode()
    except Exception as e:
        logger.error(f"Error executing whisper: {e}")
    else:
        stdout_text = safe_get_text(process_handle.stdout)
        stderr_text = safe_get_text(process_handle.stderr)

        logger.info(f"Whisper stdout: {stdout_text}")
        logger.info(f"Whisper stderr: {stderr_text}")

    # Read the JSON file with explicit encoding
    json_file_path = f"{output_prefix}.json"
    logger.info(f"Reading JSON file: {json_file_path}")
    try:
        transcription = read_transcription(json_file_path)
    except Exception as e:
        logger.error(f"Error reading transcription: {e}")
    else:
        logger.info(f"Transcription: {transcription}")
        return transcription.strip()
    finally:
        if os.path.exists(f"{output_prefix}.txt"):
            os.remove(f"{output_prefix}.txt")
        if os.path.exists(f"{output_prefix}.json"):
            os.remove(f"{output_prefix}.json")

