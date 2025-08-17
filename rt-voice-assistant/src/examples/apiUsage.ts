import { TTSApiClient, ttsApiClient } from '../services/ttsApi';

// Example 1: Transcribe an audio file from input
export const transcribeFileExample = async (fileInput: HTMLInputElement) => {
  const file = fileInput.files?.[0];
  if (!file) {
    throw new Error('No file selected');
  }

  try {
    const result = await ttsApiClient.transcribeAudio(file, 'base');
    console.log('Transcription result:', result.text);
    return result;
  } catch (error) {
    console.error('Transcription failed:', error);
    throw error;
  }
};

// Example 2: Transcribe audio from a blob (e.g., from MediaRecorder)
export const transcribeBlobExample = async (audioBlob: Blob) => {
  try {
    const result = await ttsApiClient.transcribeAudioBlob(
      audioBlob,
      'recording.webm',
      'base'
    );
    console.log('Transcription result:', result.text);
    return result;
  } catch (error) {
    console.error('Transcription failed:', error);
    throw error;
  }
};

// Example 3: Transcribe base64 audio data
export const transcribeBase64Example = async (base64Data: string) => {
  try {
    const result = await ttsApiClient.transcribeBase64Audio(
      base64Data,
      'audio/webm',
      'recording.webm',
      'base'
    );
    console.log('Transcription result:', result.text);
    return result;
  } catch (error) {
    console.error('Transcription failed:', error);
    throw error;
  }
};

// Example 4: Create a custom client with different base URL
export const createCustomClient = () => {
  const customClient = new TTSApiClient('https://your-custom-tts-server.com');
  return customClient;
};

// Example 5: Handle file input change event
export const handleFileInputChange = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  
  if (file) {
    try {
      const result = await ttsApiClient.transcribeAudio(file);
      console.log('File transcribed successfully:', result.text);
      return result;
    } catch (error) {
      console.error('Failed to transcribe file:', error);
      throw error;
    }
  }
};
