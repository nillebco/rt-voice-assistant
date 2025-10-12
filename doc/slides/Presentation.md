## Build <span class="highlight">*your own*</span> Real Time Voice Assistant

---

## Acknowledgements

- [Marine Guyot](https://codingresearcher.com/) - aka <span class="highlight">Coding Researcher</span> - for testing this logic on Linux/GPU 🙏🏼

---

## Where are we going today - and why?

<div class="side-by-side">
  <div class="text-content">
    <blockquote>
      <p>LLMs are a new kind of computer, and you program them in English</p>
      <cite>— Andrej Karpathy</cite>
    </blockquote>
  </div>
  <img src="https://downloads.intercomcdn.com/i/o/dgkjq2bp/1658109889/e9f3194e5f56fc89c198af42cc0c/AD_4nXfsjvyTirgyHkaKM7BjhFu6DukY2ioF4IkXufsh106dK1utoB8vOQqOOs93TR0AGU0vQeMNwYgm53Am_qzM0dhwld9BKSgU1wzhuLcZtD84o2LZC-z4JtH1evEWx2S6b4qTufiY?expires=1757311200&signature=04a48e756d28dd43717893999314c53c8911ce0ed48acf5301a09356ca84166d&req=dSYiHsh%2BlIlXUPMW1HO4zQnlSUxWjxRXbmXRHpNYmWNzJ%2FmKpQWcsvgJdbYI%0Ax7BUgS739TaZXugOtFs%3D%0A" alt="it's cool to speak with somebody who knows everything"/>
</div>

Note:
LLMs are good at what software isn't and viceversa. Think of them as a set of stored procedures activated by the sentences you type.

<span class="highlight">*What if the LLMs were just a new Human Machine Interface?*</span>


---

## Assumptions

- you brought your own computer!
  - maybe it has a <span class="highlight">GPU</span> 🤞🏻, maybe not 😅
- we have a network connection to <span class="highlight">download</span> a few files 🌍🕸️

---

## Architecture

<img src=architecture.png alt="the important components for today">

---

## Flow

We record -> The user speaks -> We detect voice -> We extract the text -> We pass it to a LLM -> We synthetize the LLM response to voice -> We play that sound.

---

## Prerequisites

- uv, ffmpeg
- [optional] terraform (Hetzner infra), npm, ollama (Mac) or docker (Linux)
- models:
  - tts: kokoro + voices
  - stt: whisper
  - llm: qwen3

---

## Disclaimer about the technologies

> Why didn't you pick instead `ModelXYZ` as `<technology>` ?

I have picked "good enough", <span class="highlight">#opensource</span> if possible, technologies available in August 2025.
Other technologies certainly exist and you might prefer them.
Just fork my repository and try them! :)

---

## Show me the code!

https://github.com/<span class="highlight">nillebco</span>/rt-voice-assistant

<img src="repo-qrcode.png" alt="the qr code for the gt repository">

---

## CLI or Web?

It's a real question, it's time to raise your hand!

---

## CLI

All in one - in the same file we have all components described above

---

## Web - Client side

- <span class="highlight">React</span>
- <span class="highlight">VAD</span>: voice activity detection (useful to avoid transferring hundreds of megabytes over the network)
- API Client (sends the audio with the question, receives the audio with the response)

---

## Web - Server side

The API will be composed of three parts

- <span class="highlight">STT</span>: Speech to text (transforms the voice into text)
- <span class="highlight">LLM</span>: large language model, reason over the request
- <span class="highlight">TTS</span>: Text to speech (transforms the text into voice)

---

## Web - Infrastructure

We want to host this on Linux - a Hetzner server (CX52 or CPX51).

So we are going to use <span class="highlight">`terraform`</span> to provision this!

Otherwise, we can try this on your PC 🤞

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

- token per seconds, rankings
- alignment
- Qwen ✅, Gemma, Mixtral

Note:

- Several models are available and every month we have a new one
- The performances are known thanks to benchmarks
- You can run a <span class="highlight">small model</span> on practically <span class="highlight">any device</span> (with reduced performaces)
- For this workshop we are going to use essentially Qwen ✅, Gemma, Mixtral, ...

---

## Deep dive: Text to speech (TTS)

Synthetize a text into sound - maybe including emotions

- KokoroTTS ✅
- KittenTTS

---

## References

- [this code](https://github.com/nillebco/rt-voice-assistant.git)

Please ⭐️ star it if you liked this presentation!
