# Reat Time Voice Assistant

This repository contains the code backing the "Build Your own Real Time Voice Assistant" PyConFR25 Workshop.

During this workshop we will implement a python software to interact with a LLM using the voice, in real time. We will try a local first solution, if the hardware of the participants allows. With a possible fallback on external APIs hosted by OpenRouter.

Access the [Slides](https://raw.githack.com/nillebco/rt-voice-assistant/main/doc/slides/index.html).

Clone the repository easily:

```sh
git clone https://github.com/nillebco/rt-voice-assistant
```

## Caveat

In order to execute this code you need a few components

- uv: used to manage the dependencies
- ffmpeg (used mainly for transcoding audio formats)
- whisper.cpp (used for the STT - because it offers good support for both Mac and LInux and native GPU acceleration)
- ollama or llama.cpp - to run AI models and expose them locally with a OpenAI API
    otherwise: OpenRouter or the OpenAI API
- optional: npm, terraform

A GPU will improve the performances greatly.
This code has been tested on a Mac (M4).

Every time the voice assistant detects a sentence end, it will not process any further audio till when the AI answer will be ready.

## For the impatients

Create a .env file with a structure like this

```sh
OPENAI_API_KEY=sk-or-v1-aOpenRoutersecretkeyhere
# if you don't have this yet, check the section about whisper-cpp in the follow.
WHISPER_CPP_DIR="/Users/nilleb/whisper.cpp"
```

```sh
uv sync
uv run -m rt_voice_assistant.cli
```

## Slides

The slides presented are in the doc/slides folder. Also: You can view them on [RawGitHack](https://raw.githack.com/nillebco/rt-voice-assistant/main/doc/slides/index.html).

## Repository structure

The repository contains a rt_voice_assistant folder containing the code that we will try to implement during the workshop.

### bricks

The bricks folder contains the elementary bricks that we will be working on during the workshop

- `stt` folder: several alternatives to implement the Speech-to-Text.
- `vad`: Voice Activity Detection (with silero - better - or webrtc)
- `audio`: utility functions to save the recordings to a file avoiding the noise.
- `listen`: start the recording thread, launch the frame processor
- `frame_processor`: simple logic to accumulate voice frames, detect speech start and speech end
- `tts`: text-to-speech implemented with Kokoro.
- `llm`: query a llm (locally or remotely) using the openai API (a de facto standard nowadays)

### cli

The `cli` folder contains test CLI (command line interface) tools to verify what we are doing.

- `listen`: listens to your voice and dumps a recording. Displays the current DB.
- `vad`: detect voice frame by frame (no recording)
- `record_voice`: voice activity detection sample: it creates a recording for every voice session.
- `transcribe`: convert the detected speech to text
- `say`: convert what you type to speech
- `ask`: textual assistant. Type your questions you will get the configured AI to answer them.
- `__main__`: the rt voice assistant

Every one of these samples can be run with a command like `uv run rt_voice_assistant.cli.SAMPLE` (exception made for the last for which you type just `uv run rt_voice_assistant.cli`).

The `api` file contains a sample FastAPI API exposing a few endpoints (inlcuding a websocket). Launch it with `uv run -m rt_voice_assistant.api --port 12347`.

### web application

The `sample-web-client` folder contains a web application (in React) showing how the VAD works in the browser. It will call the API to transform the voice recording into another voice recording.

## Requirements

### on Ubuntu or Debian -- using Docker

(The server image is available also for a few other GPUs - check https://github.com/ggml-org/llama.cpp/blob/b6262/docs/docker.md)

```sh
curl -L -o models/mixtral-8x7b-instruct.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF/resolve/main/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf
curl -L -o models/qwen2-1_5b-instruct.Q4_K_M.gguf \
  https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF/resolve/main/qwen2-1_5b-instruct-q4_k_m.gguf
docker run -v ./models:/models -p 11434:8000 ghcr.io/ggml-org/llama.cpp:server -m /models/mixtral-8x7b-instruct.Q4_K_M.gguf --port 8000 --host 0.0.0.0 -n 512 --ctx-size 8192 --api-key sk-local
docker run -v ./models:/models -p 11434:8000 ghcr.io/ggml-org/llama.cpp:server -m /models/qwen2-1_5b-instruct.Q4_K_M.gguf --port 8000 --host 0.0.0.0 -n 512 --ctx-size 8192 --api-key sk-local
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-local" \
  -d '{
    "model": "qwen2-1_5b-instruct.Q4_K_M.gguf",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Write a haiku about Debian Linux."}
    ],
    "max_tokens": 100,
    "temperature": 0.7
  }'

# STT - whisper.cpp
docker pull ghcr.io/ggml-org/whisper.cpp:main

# TTS - kokoroTTS
curl -L "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx" -o models/kokoro-v1.0.onnx
curl -L "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin" -o models/voices-v1.0.bin
```

### on MacOS using Homebrew (https://brew.sh/)

```sh
brew install ffmpeg ollama
ollama serve

# STT - whisper.cpp
cd $HOME
git clone https://github.com/ggml-org/whisper.cpp
pushd whisper.cpp
cmake -B build -DWHISPER_COREML=1
cmake --build build -j --config Release
uv init .
uv add ane_transformers openai-whisper coremltools torch
uv run ./models/generate-coreml-model.sh base.en
uv run ./models/generate-coreml-model.sh small.en
uv run ./models/generate-coreml-model.sh medium.en
./models/download-ggml-model.sh base.en
./models/download-ggml-model.sh small.en
./models/download-ggml-model.sh medium.en
./build/bin/whisper-cli -m models/ggml-base.en.bin -f samples/jfk.wav
./build/bin/whisper-cli -m models/ggml-small.en.bin -f samples/jfk.wav
./build/bin/whisper-cli -m models/ggml-medium.en.bin -f samples/jfk.wav

# TTS - kokoroTTS
curl -L "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx" -o models/kokoro-v1.0.onnx
curl -L "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin" -o models/voices-v1.0.bin
```

## Configuration

Your .env file will be used to store the configuration

### Use a local ollama instance

No need for a secret key - just add these lines to your .env file

```sh
OPENAI_BASE_URL=http://localhost:11434/v1
MODEL=qwen3:30b
```

### Use a local llama.cpp instance

No need for a secret key - just add these lines to your .env file

```sh
OPENAI_BASE_URL=http://localhost:11434/v1
# match your local model file name
MODEL=qwen2-1_5b-instruct.Q4_K_M.gguf
```

## Future evolutions

- Detect the spoken language
- Reduce the pauses in the input
