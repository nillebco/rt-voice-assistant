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

## Pre-requirements

You must have access to an LLM accessible through a OpenAI like API.
You must download a few files before proceeding.

You have installed the necessary audio libraries at the OS level.
eg.

- redhat-like distributions: portaudio portaudio-devel ffmpeg ffmpeg-devel
- ubuntu-like distributions: libportaudio2, portaudio19-dev, libportaudiocpp0, libasound2, libasound2-plugins, alsa-utils ffmpeg
- macos: ffmpeg ollama

In the following sections we provide sample setup scripts for a few target architectures/distributions.

### on Ubuntu or Debian -- using Docker and llama_cpp

(The llama.cpp server image is available also for a few other GPUs - check https://github.com/ggml-org/llama.cpp/blob/b6262/docs/docker.md)

```sh
./cli download llama_cpp
# or mixtral-8x7b-instruct.Q4_K_M.gguf or any other model you will have downloaded
./cli llama_cpp-up qwen2-1_5b-instruct.Q4_K_M.gguf
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
```

### on Ubuntu or Debian -- using Docker and ollama

```sh
./cli download ollama
./cli ollama-up
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-local" \
  -d '{
    "model": "qwen2.5:14b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Write a haiku about Debian Linux."}
    ],
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

### on MacOS using Homebrew (https://brew.sh/) and ollama

```sh
# LLM setup
brew install ffmpeg ollama
./cli download ollama
ollama serve
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-local" \
  -d '{
    "model": "qwen2.5:14b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Write a haiku about Debian Linux."}
    ],
    "max_tokens": 100,
    "temperature": 0.7
  }'

# STT - compile whisper.cpp with native acceleration
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

## run on linux

Make sure you completed the pre-requirements.

```sh
uv sync
uv run -m rt_voice_assistant.cli.transcribe audios/jfk.wav
uv run -m rt_voice_assistant.cli.say "hello world"
# for the next step you shall have a OpenAI compatible API running on https://localhost:11434 (ollama) or a OpenRouter API key. Check the configuration and pre-requirements sections.
uv run -m rt_voice_assistant.cli
```

## provisioning on hetzner

The scripts have been tested on a Hetzner server - only partially because such servers don't have a audio device. 😅

If you'd like to use the tf scripts to provision one:

- create a file terraform/tailscale.vars following the sample
- create a file terraform/hetzner.vars following the sample
- add a line `ssh_key_file=~/.ssh/id_rsa` to your .env (assuming you have such a file already - otherwise try `./cli gen-ssh-key`)

```sh
./cli tf apply
hostname=$(./cli tf output --json servers_ipv4 | grep '{' | jq -r '.gpu')
./cli scpto -h $hostname terraform/configuration/devops devops
./cli ssh -h $hostname
chmod 755 devops
./devops download
./devops transcribe audios/jfk.wav
./devops llm-up
./devops llm-down
./devops say "hello world"
```

## Future evolutions

- Detect the spoken language
- Reduce the pauses in the input
- Finish the web API use case
