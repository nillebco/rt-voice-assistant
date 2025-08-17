# step by step

## web app

we could use https://github.com/ricky0123/vad/tree/master/test-site as a starting canvas

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
import { useMicVAD, utils } from "@ricky0123/vad-react"
import { ttsApiClient, type TranscriptionResponse } from '../services/ttsApi';

const VoiceActivityDetection = () => {
    const vad = useMicVAD({
        onSpeechEnd: (audio: audio: Float32Array) => {
            const wav = utils.encodeWAV(audio);
            const wavBlob = new Blob([wav], { type: 'audio/wav' })
            const result = await ttsApiClient.transcribeAudioBlob(
                wavBlob,
                'recording.webm',
                options.model || 'base'
            );
            // result.text contains the transcription
        },
    })
    return <div>{vad.userSpeaking && "User is speaking"}</div>
}
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

```sh
uv run kokoro_onnx_api.py
# now you can visit https://stt.localhost/docs
```
