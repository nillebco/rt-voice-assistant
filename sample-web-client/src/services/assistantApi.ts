export interface AudioCompletionResponse {
  audioBlob: Blob;
  filename: string;
}

export class AssistantApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'https://tts.localhost') {
    this.baseUrl = baseUrl;
  }

  /**
   * Get audio completions (transcription + LLM response + TTS audio)
   * @param audioFile - The audio file to process
   * @param sttModel - The STT model to use (default: 'base')
   * @param llmModel - The LLM model to use (default: 'openai/gpt-4o')
   * @param language - The language for STT and TTS (default: 'en')
   * @param voice - The voice for TTS (default: 'af_heart')
   * @returns Promise with audio blob response
   */
  async audioCompletions(
    audioFile: File | Blob,
    sttModel: string = 'base',
    llmProvider: string = 'openrouter',
    llmModel: string = 'openai/gpt-4o',
    language: string = 'en',
    voice: string = 'af_heart'
  ): Promise<AudioCompletionResponse> {
    const formData = new FormData();
    formData.append('file', audioFile);

    const url = `${this.baseUrl}/api/v1/audio/completions?stt_model=${sttModel}&llm_provider=${llmProvider}&llm_model=${llmModel}&language=${language}&voice=${voice}`;

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

      // Get the filename from the Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'completions_output.wav';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      const audioBlob = await response.blob();
      return {
        audioBlob,
        filename
      };
    } catch (error) {
      console.error('Error getting audio completions:', error);
      throw error;
    }
  }
}
  
// Export a default instance
export const assistantApiClient = new AssistantApiClient();

// For development: Force recreation of the instance when module reloads
if (import.meta.hot) {
  import.meta.hot.accept();
}
