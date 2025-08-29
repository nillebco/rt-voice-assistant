## Build <span class="highlight">*your own*</span> Real Time Voice Assistant

---

## Acknowledgements

- [Marine Guyot](https://codingresearcher.com/) - for testing this logic on Linux/GPU

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

## Flow

We record -> The user speaks -> We detect voice -> We extract the text -> We pass it to a LLM -> We synthetize the LLM response to voice -> We play that sound.

---

## Disclaimer about the technologies

> Why didn't you pick instead `ModelXYZ` as `<technology>` ?

I have picked "good enough", #opensource if possible, technologies
available in August 2025. Other technologies certainly exist and you might prefer them. Just fork my repository and try them! :)

---

## Deep dive: Voice Activity Detection (VAD)

- Silero
- Webrtc (older)

---

## Deep dive: Speech to text (STT)

Recognize the voice in a sound stream

- Whisper (WhisperX, WhisperCPP) ✅
- Voxtral

---

### Deep dive: Large Language Models (LLM)

Several models are available and every month we have a new one
The performances are known thanks to benchmarks
You can run a small model on practically any device (with reduced performaces)
For this workshop we are going to use essentially
Qwen ✅ and/or Gemma, Mixtral

---

## Deep dive: Text to speech (TTS)

Synthetize a text into sound - maybe including emotions

- KokoroTTS ✅
- KittenTTS

---

## References

- [this code](https://github.com/nillebco/rt-voice-assistant.git)

Please ⭐️ star it if you liked this presentation!
