# Reat Time Voice Assistant

This project contains the code backing the "Build Your own Real Time Voice Assistant" PyConFR25 Workshop.

## Caveat

In order to execute this code you need a few components

uv: used to manage the dependencies
ffmpeg (used mainly for transcoding audio formats)
whisper.cpp (used for the STT - because it offers good support for both Mac and LInux and native GPU acceleration)
ollama or a similar tool to execute AI models and expose them locally with a OpenAI API
    also: OpenRouter or the OpenAI API

A GPU will improve the performances greatly.
This code has been tested on a Mac (M4).

## For the impatients

Create a .env file with a structure like this

```sh
OPENAI_API_KEY=sk-or-v1-aOpenRoutersecretkeyhere
WHISPER_CPP_DIR="/Users/nilleb/dev/nillebco/whisper-ane/whisper.cpp"
```

```sh
uv sync
uv run rt_py.cli
```

## Slides

The slides presented are in the doc/slides folder. you can run `npm i && npm run start` to get the Workshop experience. Otherwise just open the md file in that folder. The architexture diagram is in the .excalidraw file.

FIXME: copy the latest slides.

## Repository structure

The repository contains a rt_py folder containing the code that we will try to implement during the workshop.

### bricks

The bricks folder contains the elementary bricks that we will be working on during the workshop

- stt folder: several alternatives to implement the Speech-to-Text.
- vad: Voice Activity Detection (with silero - better - or webrtc)
- audio: utility functions to save the recordings to a file avoiding the noise.
- listen: start the recording thread, launch the frame processor
- frame_processor: simple logic to accumulate voice frames, detect speech start and speech end
- tts: text-to-speech implemented with Kokoro.
- llm: query a llm (locally or remotely) using the openai API (a de facto standard nowadays)

### cli

The `cli` folder contains test CLI (command line interface) tools to verify what we are doing.

- listen: listens to your voice and dumps a recording. Displays the current DB.
- vad: detect voice frame by frame (no recording)
- record_voice: voice activity detection sample: it creates a recording for every voice session.
- transcribe: convert the detected speech to text
- say: convert what you type to speech
- ask: textual assistant. Type your questions you will get the configured AI to answer them.
- __main__: the rt voice assistant

Every one of these samples can be run with a command like `uv run rt_py.cli.SAMPLE` (exception made for the last for which you type just `uv run rt_py.cli`).

The `api` file contains a sample FastAPI API exposing a few endpoints (inlcuding a websocket).

### web application

The rt-voice-assistant folder contains a web application (in React) showing how the VAD works in the browser. It will call the 

## Requirements

FIXME

### on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

### on Arch Linux
sudo pacman -S ffmpeg

### on MacOS using Homebrew (https://brew.sh/)
brew install ffmpeg ollama

### on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg

### on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg
