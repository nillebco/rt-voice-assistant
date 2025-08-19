import numpy as np
import webrtcvad

SAMPLERATE = 16000  # 44_100 or 48_000 are common, pywebrtcvad uses 8000, 16000, 32000 or 48000 Hz, silero uses 8000 or 16000

def _is_speech_webrtc(chunk_bytes: list[bytes], sampling_rate: int = SAMPLERATE):
    try:
        is_speech = vad_webrtc.is_speech(chunk_bytes, sampling_rate)
        return is_speech
    except Exception as e:
        print(f"WebRTC VAD processing error: {e}")
        return False


def process_vad_webrtc(chunk: np.ndarray, sampling_rate: int = SAMPLERATE):
    """
    Process the audio chunk using WebRTC VAD.
    Ensures WebRTC VAD requirements:
    - 16-bit mono PCM audio
    - Supported sample rates: 8000, 16000, 32000, or 48000 Hz
    - Frame duration: 10, 20, or 30 ms
    """
    global vad_webrtc

    # Initialize VAD once
    if vad_webrtc is None:
        vad_webrtc = webrtcvad.Vad()
        vad_webrtc.set_mode(1)  # Aggressiveness level 0-3

    # Ensure we have mono audio (take first channel if stereo)
    if chunk.ndim > 1 and chunk.shape[1] > 1:
        chunk = chunk[:, 0]

    # Ensure 16-bit PCM format
    if chunk.dtype != np.int16:
        chunk = chunk.astype(np.int16)
    
    # Calculate frame duration in milliseconds
    frame_duration_ms = (len(chunk) / sampling_rate) * 1000
    
    # WebRTC VAD only accepts 10, 20, or 30 ms frames
    # If our frame doesn't match, we need to adjust
    if frame_duration_ms not in [10, 20, 30]:
        # Find the closest supported frame duration
        target_durations = [10, 20, 30]
        closest_duration = min(target_durations, key=lambda x: abs(x - frame_duration_ms))
        
        # Calculate how many samples we need for the target duration
        target_samples = int((closest_duration / 1000) * sampling_rate)
        
        # Pad or truncate to match target duration
        if len(chunk) < target_samples:
            # Pad with zeros if too short
            padded_chunk = np.zeros(target_samples, dtype=np.int16)
            padded_chunk[:len(chunk)] = chunk
            chunk = padded_chunk
        else:
            # Truncate if too long
            chunk = chunk[:target_samples]
        
        frame_duration_ms = closest_duration
    
    # Convert to bytes for WebRTC VAD
    chunk_bytes = chunk.tobytes()
    
    return _is_speech_webrtc(chunk_bytes)
