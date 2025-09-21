import json
import logging
import os
import shutil
import subprocess
import uuid

logger = logging.getLogger("rt_py.bricks.stt_whisper_cpp")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

DEFAULT_DOCKER_IMAGE = "ghcr.io/ggml-org/whisper.cpp:main"
DEFAULT_MODEL = "small"  # Default model to use when whisper-1 is specified


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


def safe_json_read(json_file_path: str) -> str:
    try:
        data = json.load(open(json_file_path, "r", encoding="utf-8", errors="replace"))
    except (FileNotFoundError, UnicodeDecodeError):
        logger.exception(f"Error reading JSON file: {json_file_path}")
        raise
    return data


def extract_transcription(transcription_data: dict) -> str:
    try:
        transcription = transcription_data["transcription"][0]["text"]
    except (KeyError, IndexError):
        transcription = None
    return transcription


def read_transcription(json_file_path: str) -> str:
    transcription_data = safe_json_read(json_file_path)
    transcription = extract_transcription(transcription_data)
    return transcription


def execute_whisper(cmd: list[str]):
    try:
        logger.info(f"Executing whisper: {cmd}")
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


def whisper_cpp_args(model_path, input_wav_path, output_prefix, language=None):
    cmd = [
        "-m",
        model_path,
        "-f",
        input_wav_path,
        "-ojf",
        "-of",
        output_prefix,
    ]

    if language:
        cmd.extend(["-l", language])

    return cmd


def detect_paths(model: str = None, language: str = None):
    language = language or "en"

    home = os.path.expanduser("~")
    whisper_cpp_dir = os.getenv(
        "WHISPER_CPP_DIR", f"{home}/whisper.cpp"
    )  # as suggested for macOS in our README

    whisper_binary = f"{whisper_cpp_dir}/build/bin/whisper-cli"
    if not os.path.exists(whisper_binary):
        logger.warning(
            f"Whisper binary does not exist: {whisper_binary} -- will be using docker!"
        )
        whisper_binary = None

    available_models_directories = [
        os.getenv("WHISPER_MODELS_DIR", "./models"),
        f"{whisper_cpp_dir}/models",
    ]
    available_models = [model] if model else ["small", "tiny", "medium", "base"]

    valid_models_dir, model_path = None, None
    for models_dir in available_models_directories:
        if os.path.exists(models_dir) and os.path.isdir(models_dir):
            for model in available_models:
                model_paths = [
                    f"{models_dir}/ggml-{model}.{language}.bin",
                    f"{models_dir}/ggml-{model}.bin",
                ]
                for model_path in model_paths:
                    if os.path.exists(model_path):
                        valid_models_dir = models_dir
                        break

    if not valid_models_dir:
        raise ValueError(
            f"No valid models directory found in {available_models_directories}"
        )

    return whisper_binary, model_path


def transcribe(
    input_wav_path: str,
    model: str = None,
    language: str = None,
):
    if not os.path.isdir("outputs"):
        os.mkdir("outputs")

    if not os.path.isdir("audios"):
        os.mkdir("audios")

    output_prefix = f"outputs/out-{uuid.uuid4()}"

    actual_model = DEFAULT_MODEL if model == "whisper-1" or not model else model
    whisper_binary, model_path = detect_paths(actual_model, language)

    cmd = []
    if whisper_binary:
        cmd.append(whisper_binary)
        args = whisper_cpp_args(model_path, input_wav_path, output_prefix, language)
        cmd.extend(args)
    else:
        docker_image = os.getenv("WHISPER_CPP_DOCKER_IMAGE", DEFAULT_DOCKER_IMAGE)
        # copy the audio file to audios folder -- if they are not already there
        audio_filename = os.path.basename(input_wav_path)
        audio_dest_path = os.path.join("audios", audio_filename)

        model_path = f"/models/ggml-{model}.{language}.bin"
        args = whisper_cpp_args(
            model_path, f"/{audio_dest_path}", f"/{output_prefix}", language
        )
        if audio_dest_path != input_wav_path:
            shutil.copy2(input_wav_path, audio_dest_path)
            logger.info(f"Copied audio file to {audio_dest_path}")

        use_elevated_docker = os.getenv("WHISPER_CPP_USE_ELEVATED_DOCKER", "false")
        if use_elevated_docker == "true":
            cmd += ["sudo"]

        cmd += [
            "docker",
            "run",
            "-it",
            "--rm",
            "-v",
            f"{os.getcwd()}/models:/models",
            "-v",
            f"{os.getcwd()}/audios:/audios",
            "-v",
            f"{os.getcwd()}/outputs:/outputs",
            docker_image,
            f'"whisper-cli {" ".join(args)}"',
        ]
        logger.error(f"Docker command: {' '.join(cmd)}")

    try:
        process_handle = execute_whisper(cmd)
        process_handle.check_returncode()
    except Exception:
        logger.exception("Error executing whisper")
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
    except Exception:
        logger.exception("Error reading transcription")
    else:
        logger.info(f"Transcription: {transcription}")
        return transcription.strip()
    finally:
        if os.path.exists(f"{output_prefix}.txt"):
            os.remove(f"{output_prefix}.txt")
        if os.path.exists(f"{output_prefix}.json"):
            os.remove(f"{output_prefix}.json")
