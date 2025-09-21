import { useState, useCallback } from 'react';
import { ttsApiClient, type TranscriptionResponse } from '../services/ttsApi';

export interface UseTranscriptionOptions {
  model?: string;
  language?: string;
  onTranscriptionStart?: () => void;
  onTranscriptionComplete?: (result: TranscriptionResponse) => void;
  onTranscriptionError?: (error: Error) => void;
}

export const useTranscription = (options: UseTranscriptionOptions = {}) => {
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcription, setTranscription] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const transcribeAudio = useCallback(async (audioBlob: Blob) => {
    if (isTranscribing) return;

    setIsTranscribing(true);
    setError(null);
    options.onTranscriptionStart?.();

    try {
      const result = await ttsApiClient.transcribeAudioBlob(
        audioBlob,
        'recording.webm',
        options.model || 'base',
        options.language || 'en'
      );

      setTranscription(result.text);
      options.onTranscriptionComplete?.(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Transcription failed';
      setError(errorMessage);
      options.onTranscriptionError?.(err instanceof Error ? err : new Error(errorMessage));
      throw err;
    } finally {
      setIsTranscribing(false);
    }
  }, [isTranscribing, options]);

  const clearTranscription = useCallback(() => {
    setTranscription('');
    setError(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    transcribeAudio,
    isTranscribing,
    transcription,
    error,
    clearTranscription,
    clearError,
  };
};
