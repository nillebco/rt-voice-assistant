from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from typing import Callable, Optional, List
import numpy as np


# ---- Types ------------------------------------------------------------------

ProbFn = Callable[[np.ndarray], float]  # returns P(speech) for a single frame

OnFrameProcessed = Callable[[float, np.ndarray], None]
OnVADMisfire = Callable[[], None]
OnSpeechStart = Callable[[], None]
OnSpeechRealStart = Callable[[], None]
OnSpeechEnd = Callable[[np.ndarray], None]


# ---- Options ----------------------------------------------------------------


@dataclass
class FrameProcessorOptions:
    frame_samples: int = 512  # 30 ms @ 16 kHz (Silero v5); legacy often 512
    positive_speech_threshold: float = 0.6
    negative_speech_threshold: float = 0.35
    redemption_frames: int = 8  # grace frames allowed while "in speech"
    pre_speech_pad_frames: int = 4  # frames to prepend when a speech start is detected
    min_speech_frames: int = 5  # frames needed to confirm "real" speech
    submit_user_speech_on_pause: bool = True


@dataclass
class Callbacks:
    on_frame_processed: Optional[OnFrameProcessed] = None
    on_vad_misfire: Optional[OnVADMisfire] = None
    on_speech_start: Optional[OnSpeechStart] = None
    on_speech_real_start: Optional[OnSpeechRealStart] = None
    on_speech_end: Optional[OnSpeechEnd] = None


# ---- Processor ---------------------------------------------------------------


class FrameProcessor:
    """
    Stitch per-frame speech probabilities into contiguous speech segments.

    State machine:
      - idle: keep a ring buffer for pre-speech padding
      - speaking: accumulate frames; tolerate up to `redemption_frames` of low prob
      - finalize:
          - if total < min_speech_frames -> misfire
          - else -> emit on_speech_end(audio)

    All frames are assumed to be Float32 mono @ 16 kHz with `frame_samples` length.
    """

    def __init__(self, prob_fn: ProbFn, options: FrameProcessorOptions, cb: Callbacks):
        self._prob_fn = prob_fn
        self.opt = options
        self.cb = cb

        # Ring buffer for pre-speech audio
        self._pre_ring: deque[np.ndarray] = deque(maxlen=self.opt.pre_speech_pad_frames)

        # Active segment buffer
        self._active_frames: List[np.ndarray] = []
        self._in_speech: bool = False
        self._speech_frame_count: int = 0
        self._real_start_fired: bool = False
        self._low_prob_streak: int = 0
        self._paused: bool = False

    # --- Public API -----------------------------------------------------------

    def pause(self):
        """Optionally flush current segment if configured, then enter paused state."""
        if self._paused:
            return
        if self.opt.submit_user_speech_on_pause and self._in_speech:
            self._finalize_segment()
        self._paused = True

    def resume(self):
        """Resume processing frames."""
        self._paused = False

    def reset(self):
        """Hard reset of all buffers and state."""
        self._pre_ring.clear()
        self._active_frames.clear()
        self._in_speech = False
        self._speech_frame_count = 0
        self._real_start_fired = False
        self._low_prob_streak = 0
        self._paused = False

    def process(self, frame: np.ndarray):
        """
        Consume a single frame (Float32, shape (frame_samples,)).
        Calls callbacks synchronously.
        """
        if self._paused:
            return

        # Probability for this frame
        p_speech = self._prob_fn(frame)

        if self.cb.on_frame_processed:
            self.cb.on_frame_processed(p_speech, frame)

        if not self._in_speech:
            # Idle: collect ring buffer and look for activation
            self._pre_ring.append(frame)

            if p_speech >= self.opt.positive_speech_threshold:
                # Enter speaking
                self._enter_speaking()
        else:
            # Already speaking: append and manage deactivation
            self._active_frames.append(frame)
            self._speech_frame_count += 1

            # Fire "real start" once, after min_speech_frames
            if (not self._real_start_fired) and (
                self._speech_frame_count >= self.opt.min_speech_frames
            ):
                self._real_start_fired = True
                if self.cb.on_speech_real_start:
                    self.cb.on_speech_real_start()

            # Deactivation logic with redemption frames
            if p_speech < self.opt.negative_speech_threshold:
                self._low_prob_streak += 1
                if self._low_prob_streak > self.opt.redemption_frames:
                    self._finalize_segment()
            else:
                self._low_prob_streak = 0

    # --- Internals ------------------------------------------------------------

    def _enter_speaking(self):
        # Build initial buffer with pre-speech padding
        self._active_frames = list(self._pre_ring)  # copy current ring
        self._pre_ring.clear()
        self._in_speech = True
        self._speech_frame_count = len(self._active_frames)
        self._real_start_fired = False
        self._low_prob_streak = 0

        if self.cb.on_speech_start:
            self.cb.on_speech_start()

        # Note: do NOT call on_speech_real_start here; we wait for min_speech_frames

    def _finalize_segment(self):
        total_frames = self._speech_frame_count
        audio = (
            np.concatenate(self._active_frames, dtype=np.float32)
            if self._active_frames
            else np.zeros((0,), dtype=np.float32)
        )

        # Reset state before callbacks to avoid reentrancy pitfalls
        self._active_frames = []
        self._in_speech = False
        self._speech_frame_count = 0
        self._real_start_fired = False
        self._low_prob_streak = 0

        if total_frames < self.opt.min_speech_frames:
            if self.cb.on_vad_misfire:
                self.cb.on_vad_misfire()
            return

        if self.cb.on_speech_end:
            self.cb.on_speech_end(audio)
