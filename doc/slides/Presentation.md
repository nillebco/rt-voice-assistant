---
cssclasses: pycon
---
## Build <span class="highlight">*your own*</span> Real Time Voice Assistant

---

## Where are we going today - and why?
> LLMs are a new kind of computer, and you program them in English
>         Andrej Karpathy

LLMs are good at what software isn't and viceversa. Think of them as a set of stored procedures activated by the sentences you type.

*What if the LLMs were just a new Human Machine Interface?*

---
## Assumptions
- you brought your own computer!
	- maybe it has a GPU 🤞🏻, maybe not 😅
- we have a network connection to download a few files 🌍🕸️

---
## Architecture
 ![[LocalFirst Real Time Voice Assistant.excalidraw]]

---
## Prerequisites
- uv, npm, ollama, terraform, ffmpeg
- models:
	- tts: kokoro + voices
	- stt: whisper
	- llm: gemma3

---

## Client side
- React
- VAD: voice activity detection (useful to avoid transferring hundreds of megabytes over the network)
- API Client (sends the audio with the question, receives the audio with the question)

---
## Server side
The API will be composed of three parts

- STT: Speech to text (transforms the voice into text)
- LLM: large language model, reason over the request
- TTS: Text to speech (transforms the text into voice)

---
### Infrastructure
We want to host this on Linux - a Hetzner server (CAX41)
So we are going to use `terraform` to provision this
Otherwise, we can try this on your PC 🤞

---
## Client
- React + typescript
- additional package `@ricky0123/vad-react`.

The idea is that our assistant is a web page with a single button "Start".
When this button is pressed, we begin listening for any voice.
When a voice is heard, we record a wav file. And when the voice stops, we send that to a server, for processing.

---
## Client - step by step - shell
```sh
npm create vite@latest rt-voice-assistant -- --template react-ts
cd rt-voice-assistant
npm install
npm i @ricky0123/vad-react --legacy-peer-deps
npm run dev
```

---

## Client - App.tsx
```tsx
// something
```

---
## Client - services/api.ts
```ts
// something
```

---
## Server - shell
```sh
uv init
# stt
uv add 
# tts
uv add kokoro-onnx soundfile onnx-runtime
# llm
uv add httpx
# api
uv add fastapi pydantic
```
---

## Server - stt.py

```python
# this
```

---
## Server - tts.py
```python
# this
```

---
## Server - llm.py
```python
# this
```
---
## Server - api.py
```python
# this
```

---
## Infrastructure - terraform/main.tf

```terraform
variable "project_id" {
	type = string
}
```

---
## Infrastructure - Dockerfile

```Dockerfile
FROM ubuntu:24-04
# this
```

---
## References
[this code](https://github.com/nillebco/rt-voice-assistant.git)
