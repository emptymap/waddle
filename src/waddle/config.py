from dataclasses import dataclass
from typing import Final

# Language settings
DEFAULT_LANGUAGE: Final[str] = "ja"  # Default language for transcription

# Audio duration settings (in seconds)
DEFAULT_OUT_AUDIO_DURATION: Final[float] = 60.0  # Default output duration
DEFAULT_COMP_AUDIO_DURATION: Final[float] = 1200.0  # Default comparison duration (20 minutes)

# Audio processing settings
DEFAULT_SR: Final[int] = 48000  # Default sample rate in Hz
DEFAULT_CHUNK_DURATION: Final[float] = 0.5  # Duration of each processing chunk
DEFAULT_BUFFER_DURATION: Final[float] = 0.25  # Buffer duration around speech segments

# Audio level settings (in dBFS)
DEFAULT_TARGET_DB: Final[float] = -30.0  # Target audio level for normalization
DEFAULT_THRESHOLD_DB: Final[float] = -70.0  # Threshold for speech detection


@dataclass(frozen=True)
class AudioConfig:
    """Audio processing configuration."""

    language: str = DEFAULT_LANGUAGE
    out_duration: float = DEFAULT_OUT_AUDIO_DURATION
    comp_duration: float = DEFAULT_COMP_AUDIO_DURATION
    sample_rate: int = DEFAULT_SR
    chunk_duration: float = DEFAULT_CHUNK_DURATION
    buffer_duration: float = DEFAULT_BUFFER_DURATION
    target_db: float = DEFAULT_TARGET_DB
    threshold_db: float = DEFAULT_THRESHOLD_DB

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.out_duration <= 0:
            raise ValueError("Output duration must be positive")
        if self.comp_duration <= 0:
            raise ValueError("Comparison duration must be positive")
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be positive")
        if self.chunk_duration <= 0:
            raise ValueError("Chunk duration must be positive")
        if self.buffer_duration < 0:
            raise ValueError("Buffer duration cannot be negative")
        if self.target_db > 0:
            raise ValueError("Target dB must be negative or zero")
        if self.threshold_db > self.target_db:
            raise ValueError("Threshold dB must be less than target dB")


# Default configuration instance
DEFAULT_CONFIG: Final[AudioConfig] = AudioConfig()
