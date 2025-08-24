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
 <img src=architecture.png>

---
## Prerequisites

- uv, ffmpeg
- [optional] terraform (Hetzner infra), npm, ollama (Mac) or docker (Linux)
- models:
	- tts: kokoro + voices
	- stt: whisper
	- llm: qwen3

---
## CLI or Web?
It's a real question, raise your hand for....

---
## CLI
All in one - in the same file we have all components described above

---
## Web - Client side
- React
- VAD: voice activity detection (useful to avoid transferring hundreds of megabytes over the network)
- API Client (sends the audio with the question, receives the audio with the response)

---
## Web - Server side
The API will be composed of three parts

- STT: Speech to text (transforms the voice into text)
- LLM: large language model, reason over the request
- TTS: Text to speech (transforms the text into voice)

---
## Infrastructure

We want to host this on Linux - a Hetzner server (CAX41)

So we are going to use `terraform` to provision this

Otherwise, we can try this on your PC 🤞

---
## References
[this code](https://github.com/nillebco/rt-voice-assistant.git)