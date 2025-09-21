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
    model: string = 'base',
    language: string = 'en'
  ): Promise<TranscriptionResponse> {
    const formData = new FormData();
    formData.append('file', audioFile);

    const url = `${this.baseUrl}/api/v1/audio/transcriptions?model=${model}&language=${language}`;

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
    model: string = 'base',
    language: string = 'en'
  ): Promise<TranscriptionResponse> {
    // Create a File object from the blob with a proper filename
    const audioFile = new File([audioBlob], filename, { type: audioBlob.type });
    return this.transcribeAudio(audioFile, model, language);
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
    model: string = 'base',
    language: string = 'en'
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
    
    return this.transcribeAudioBlob(audioBlob, filename, model, language);
  }
}

// Export a default instance
export const ttsApiClient = new TTSApiClient();

// For development: Force recreation of the instance when module reloads
if (import.meta.hot) {
  import.meta.hot.accept();
}
