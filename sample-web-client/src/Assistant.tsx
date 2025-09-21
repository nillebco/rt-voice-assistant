import { useMicVAD, utils } from "@ricky0123/vad-react";
import { useTranscription } from "./hooks/useTranscription";
import { useState } from "react";

interface TranscriptionItem {
  id: string;
  text: string;
  timestamp: Date;
}

const Assistant = () => {
  const [transcriptionHistory, setTranscriptionHistory] = useState<TranscriptionItem[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<string>('en');
  
  const {
    transcribeAudio,
    isTranscribing,
    error,
    clearError
  } = useTranscription({
    model: 'base',
    language: selectedLanguage,
    onTranscriptionStart: () => console.log('Starting transcription...'),
    onTranscriptionComplete: (result) => {
      console.log('Transcription complete:', result);
      // Add new transcription to history
      const newTranscription: TranscriptionItem = {
        id: Date.now().toString(),
        text: result.text,
        timestamp: new Date()
      };
      setTranscriptionHistory(prev => [...prev, newTranscription]);
    },
    onTranscriptionError: (error) => console.error('Transcription error:', error)
  });

  const vad = useMicVAD({
    onSpeechEnd: async (audio: Float32Array) => {
      console.log("User stopped talking, audio length:", audio.length);
      
      try {
        const wav = utils.encodeWAV(audio);
        const wavBlob = new Blob([wav], { type: 'audio/wav' })
        await transcribeAudio(wavBlob);
      } catch (err) {
        console.error('Failed to transcribe audio:', err);
      }
    },
  });

  const clearHistory = () => {
    setTranscriptionHistory([]);
  };

  const removeTranscription = (id: string) => {
    setTranscriptionHistory(prev => prev.filter(item => item.id !== id));
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString();
  };

  return (
    <div className="voice-assistant">
      <div className="status">
        {vad.userSpeaking && <div className="speaking">🎤 User is speaking...</div>}
        {isTranscribing && <div className="transcribing">🔄 Transcribing...</div>}
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
