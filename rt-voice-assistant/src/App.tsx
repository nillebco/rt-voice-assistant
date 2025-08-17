import "./App.css";
import { useMicVAD } from "@ricky0123/vad-react";
import { useTranscription } from "./hooks/useTranscription";
import { useState } from "react";

interface TranscriptionItem {
  id: string;
  text: string;
  timestamp: Date;
}

/**
 * Converts Float32Array audio data to WAV format
 * @param audio - Float32Array containing raw audio samples
 * @param sampleRate - Sample rate in Hz (default: 16000)
 * @returns Blob containing WAV audio data
 */
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

const VoiceActivityDetection = () => {
  const [transcriptionHistory, setTranscriptionHistory] = useState<TranscriptionItem[]>([]);
  
  const {
    transcribeAudio,
    isTranscribing,
    error,
    clearError
  } = useTranscription({
    model: 'base',
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
    onSpeechEnd: async (audio) => {
      console.log("User stopped talking, audio length:", audio.length);
      
      try {
        // Convert Float32Array to WAV format and transcribe
        const wavBlob = convertFloat32ArrayToWAV(audio);
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
          <h3>Transcription History</h3>
          {transcriptionHistory.length > 0 && (
            <button onClick={clearHistory} className="clear-all-btn">
              Clear All
            </button>
          )}
        </div>
        
        {transcriptionHistory.length === 0 ? (
          <div className="empty-state">
            <p>No transcriptions yet. Start speaking to see results here!</p>
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
        <button onClick={vad.listening ? vad.pause : vad.start}>
          {vad.listening ? 'Stop Recording' : 'Start Recording'}
        </button>
      </div>
    </div>
  );
};

function App() {
  return (
    <>
      <VoiceActivityDetection />
    </>
  );
}

export default App;
