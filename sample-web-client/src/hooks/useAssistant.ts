import { useState, useCallback } from 'react';
import { assistantApiClient, type AudioCompletionResponse } from '../services/assistantApi';

export interface UseAssistantOptions {
  sttModel?: string;
  llmModel?: string;
  language?: string;
  voice?: string;
  onAudioCompletionStart?: () => void;
  onAudioCompletionComplete?: (result: AudioCompletionResponse) => void;
  onAudioCompletionError?: (error: Error) => void;
}

export const useAssistant = (options: UseAssistantOptions = {}) => {
  const [isProcessingAudioCompletion, setIsProcessingAudioCompletion] = useState(false);
  const [audioResponse, setAudioResponse] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);

  const processAudioCompletion = useCallback(async (audioBlob: Blob) => {
    if (isProcessingAudioCompletion) return;

    setIsProcessingAudioCompletion(true);
    setError(null);
    options.onAudioCompletionStart?.();

    try {
      const result = await assistantApiClient.audioCompletions(
        audioBlob,
        options.sttModel || 'base',
        options.llmModel || 'openai/gpt-4o',
        options.language || 'en',
        options.voice || 'af_heart'
      );

      setAudioResponse(result.audioBlob);
      options.onAudioCompletionComplete?.(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Audio completion failed';
      setError(errorMessage);
      options.onAudioCompletionError?.(err instanceof Error ? err : new Error(errorMessage));
      throw err;
    } finally {
      setIsProcessingAudioCompletion(false);
    }
  }, [isProcessingAudioCompletion, options]);

  const clearAudioResponse = useCallback(() => {
    setAudioResponse(null);
    setError(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearHistory = useCallback(async () => {
    await assistantApiClient.clearHistory();
  }, []);

  return {
    processAudioCompletion,
    isProcessingAudioCompletion,
    audioResponse,
    error,
    clearAudioResponse,
    clearError,
    clearHistory,
  };
};
