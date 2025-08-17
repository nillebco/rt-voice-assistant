# step by step

## web app

```sh
npm create vite@latest rt-voice-assistant -- --template react-ts
cd rt-voice-assistant
npm install
# https://github.com/ricky0123/vad/issues/188
npm i @ricky0123/vad-react --legacy-peer-deps
npm run dev
```

write the code handling the vad
https://docs.vad.ricky0123.com/user-guide/api/#support_2

```typescript
import { useMicVAD } from "@ricky0123/vad-react"

const MyComponent = () => {
const vad = useMicVAD({
    onSpeechEnd: (audio: audio: Float32Array) => {
    console.log("User stopped talking")
    },
})
return <div>{vad.userSpeaking && "User is speaking"}</div>
}
```

convert the audio to a wav

```ts
const convertFloat32ArrayToWAV = (audio: Float32Array, sampleRate: number = 16000): Blob => {
  const numChannels = 1; // Mono audio
  
  // Create WAV header
  const bufferLength = audio.length * 2; // 16-bit samples
  const arrayBuffer = new ArrayBuffer(44 + bufferLength);
  const view = new DataView(arrayBuffer);
  
  // WAV file header
  const writeString = (offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };
  
  writeString(0, 'RIFF');
  view.setUint32(4, 36 + bufferLength, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numChannels * 2, true);
  view.setUint16(32, numChannels * 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, bufferLength, true);
  
  // Convert Float32Array to 16-bit PCM and write to buffer
  let offset = 44;
  for (let i = 0; i < audio.length; i++) {
    const sample = Math.max(-1, Math.min(1, audio[i]));
    const pcmSample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
    view.setInt16(offset, pcmSample, true);
    offset += 2;
  }
  
  return new Blob([arrayBuffer], { type: 'audio/wav' });
};
```

write a client for the transcription API

```ts
export interface TranscriptionResponse {
  text: string;
  // Add other response fields as needed based on your API
}

export class TTSApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'https://tts.localhost') {
    this.baseUrl = baseUrl;
  }

  /**
   * Transcribe audio file to text
   * @param audioFile - The audio file to transcribe
   * @param model - The model to use for transcription (default: 'base')
   * @returns Promise with transcription result
   */
  async transcribeAudio(
    audioFile: File | Blob,
    model: string = 'base'
  ): Promise<TranscriptionResponse> {
    const formData = new FormData();
    formData.append('file', audioFile);

    const url = `${this.baseUrl}/v1/audio/transcriptions?model=${model}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        // Note: Don't set Content-Type header manually for FormData
        // The browser will automatically set it with the correct boundary
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result as TranscriptionResponse;
    } catch (error) {
      console.error('Error transcribing audio:', error);
      throw error;
    }
  }

  /**
   * Transcribe audio from a blob URL or data URL
   * @param audioBlob - Audio blob data
   * @param filename - Filename for the audio (e.g., 'recording.webm')
   * @param model - The model to use for transcription
   * @returns Promise with transcription result
   */
  async transcribeAudioBlob(
    audioBlob: Blob,
    filename: string = 'recording.webm',
    model: string = 'base'
  ): Promise<TranscriptionResponse> {
    // Create a File object from the blob with a proper filename
    const audioFile = new File([audioBlob], filename, { type: audioBlob.type });
    return this.transcribeAudio(audioFile, model);
  }

  /**
   * Transcribe audio from base64 data
   * @param base64Data - Base64 encoded audio data
   * @param mimeType - MIME type of the audio (e.g., 'audio/webm')
   * @param filename - Filename for the audio
   * @param model - The model to use for transcription
   * @returns Promise with transcription result
   */
  async transcribeBase64Audio(
    base64Data: string,
    mimeType: string = 'audio/webm',
    filename: string = 'recording.webm',
    model: string = 'base'
  ): Promise<TranscriptionResponse> {
    // Remove data URL prefix if present
    const base64 = base64Data.replace(/^data:[^;]+;base64,/, '');
    
    // Convert base64 to blob
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    const audioBlob = new Blob([byteArray], { type: mimeType });
    
    return this.transcribeAudioBlob(audioBlob, filename, model);
  }
}

// Export a default instance
export const ttsApiClient = new TTSApiClient();
```

start the transcription API

```sh
# on mac
git clone https://github.com/nillebco/fast-openai-like-transcription-server.git
# on linux -- FIXME
```

start ollama
download a model (ie. gemma3 3b)

start the kokoroTTS server
