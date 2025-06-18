"""Type stubs for pydub.silence."""

from typing import List

from . import AudioSegment

def detect_silence(
    audio_segment: AudioSegment,
    min_silence_len: int = 1000,
    silence_thresh: float = -16.0,
    seek_step: int = 1,
) -> List[List[int]]: ...
