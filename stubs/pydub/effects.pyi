"""Type stubs for pydub.effects."""

from . import AudioSegment

def compress_dynamic_range(
    seg: AudioSegment,
    threshold: float = -20.0,
    ratio: float = 4.0,
    attack: float = 5.0,
    release: float = 50.0,
) -> AudioSegment: ...
