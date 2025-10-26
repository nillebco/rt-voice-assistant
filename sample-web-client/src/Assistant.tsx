import { useMicVAD, utils } from "@ricky0123/vad-react";
import { useAssistant } from "./hooks/useAssistant";
import { useState, useRef } from "react";

interface TranscriptionItem {
  id: string;
  text: string;
  timestamp: Date;
  audioUrl?: string; // URL for playing the audio response
}

const Assistant = () => {
  const [transcriptionHistory, setTranscriptionHistory] = useState<TranscriptionItem[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<string>('en');
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const {
    processAudioCompletion,
    isProcessingAudioCompletion,
    error,
    clearError
  } = useAssistant({
    sttModel: 'base',
    language: selectedLanguage,
    voice: 'af_heart',
    llmModel: 'openai/gpt-4o',
    onAudioCompletionStart: () => console.log('Starting audio completion...'),
    onAudioCompletionComplete: (result) => {
      console.log('Audio completion complete:', result);
      // Create audio URL from blob
      const audioUrl = URL.createObjectURL(result.audioBlob);
      
      // Add new transcription to history with audio URL
      const newTranscription: TranscriptionItem = {
        id: Date.now().toString(),
        text: 'Audio response received', // We don't get the transcription text from completions endpoint
        timestamp: new Date(),
        audioUrl: audioUrl
      };
      setTranscriptionHistory(prev => [...prev, newTranscription]);
    },
    onAudioCompletionError: (error) => console.error('Audio completion error:', error)
  });

  const vad = useMicVAD({
    onSpeechEnd: async (audio: Float32Array) => {
      console.log("User stopped talking, audio length:", audio.length);
      
      try {
        const wav = utils.encodeWAV(audio);
        const wavBlob = new Blob([wav], { type: 'audio/wav' })
        await processAudioCompletion(wavBlob);
      } catch (err) {
        console.error('Failed to process audio completion:', err);
      }
    },
  });

  const clearHistory = () => {
    // Clean up audio URLs to prevent memory leaks
    transcriptionHistory.forEach(item => {
      if (item.audioUrl) {
        URL.revokeObjectURL(item.audioUrl);
      }
    });
    setTranscriptionHistory([]);
  };

  const playAudio = (audioUrl: string) => {
    if (audioRef.current) {
      audioRef.current.src = audioUrl;
      audioRef.current.play().catch(err => {
        console.error('Failed to play audio:', err);
      });
    }
  };

  const removeTranscription = (id: string) => {
    setTranscriptionHistory(prev => {
      const itemToRemove = prev.find(item => item.id === id);
      if (itemToRemove?.audioUrl) {
        URL.revokeObjectURL(itemToRemove.audioUrl);
      }
      return prev.filter(item => item.id !== id);
    });
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString();
  };

  return (
    <div className="voice-assistant">
      <audio ref={audioRef} />
      <div className="status">
        {vad.userSpeaking && <div className="speaking">🎤 User is speaking...</div>}
        {isProcessingAudioCompletion && <div className="processing">🔄 Processing audio completion...</div>}
      </div>
      
      {error && (
        <div className="error">
          <span>❌ Error: {error}</span>
          <button onClick={clearError}>Clear</button>
        </div>
      )}
      
      <div className="transcription-history">
        <div className="history-header">
          <h3>Assistant History</h3>
          {transcriptionHistory.length > 0 && (
            <button onClick={clearHistory} className="clear-all-btn">
              Clear All
            </button>
          )}
        </div>
        
        {transcriptionHistory.length === 0 ? (
          <div className="empty-state">
            <p>No interactions yet. Start speaking to see results here!</p>
          </div>
        ) : (
          <div className="transcription-list">
            {transcriptionHistory.map((item) => (
              <div key={item.id} className="transcription-item">
                <div className="transcription-content">
                  <p className="transcription-text">{item.text}</p>
                  <span className="transcription-time">{formatTimestamp(item.timestamp)}</span>
                  {item.audioUrl && (
                    <button 
                      onClick={() => playAudio(item.audioUrl!)}
                      className="play-audio-btn"
                      title="Play audio response"
                    >
                      🔊 Play Response
                    </button>
                  )}
                </div>
                <button 
                  onClick={() => removeTranscription(item.id)}
                  className="remove-btn"
                  title="Remove this transcription"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="controls">
        <div className="language-selector">
          <label htmlFor="language-select">Language:</label>
          <select 
            id="language-select"
            value={selectedLanguage} 
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="language-combobox"
          >
            <option value="en">🇺🇸 English</option>
            <option value="fr">🇫🇷 French</option>
          </select>
        </div>
        <button onClick={vad.listening ? vad.pause : vad.start}>
          {vad.listening ? 'Stop Recording' : 'Start Recording'}
        </button>
      </div>
    </div>
  );
};

export default Assistant;
