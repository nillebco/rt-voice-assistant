# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "numpy",
#     "sounddevice",
#     "soundfile",
# ]
# ///

from datetime import datetime

from ..bricks.listen import ListenOptions, listen
from ..bricks.sample_callbacks import RMSMeter, multiple_callbacks, sample_process_frame

if __name__ == "__main__":
    options = ListenOptions(
        samplerate=16000,
        channels=1,
        frames_per_callback=1024,
        filename=f"capture_{datetime.now().strftime('%Y%m%d-%H%M%S')}.wav",
        dtype="int16",
        process_frame=multiple_callbacks([RMSMeter(), sample_process_frame]),
    )
    listen(options)
