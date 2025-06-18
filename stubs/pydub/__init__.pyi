"""Type stubs for pydub."""

import array
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

class AudioSegment:
    def __init__(
        self,
        data: bytes,
        frame_rate: int,
        sample_width: int,
        channels: int,
    ) -> None: ...
    @classmethod
    def from_file(
        cls,
        file: Union[str, Path, BinaryIO],
        format: Optional[str] = None,
        codec: Optional[str] = None,
        parameters: Optional[Any] = None,
        start_second: Optional[float] = None,
        duration: Optional[float] = None,
        **kwargs: Any,
    ) -> "AudioSegment": ...
    @classmethod
    def silent(cls, duration: int, frame_rate: int = 11025) -> "AudioSegment": ...
    def export(
        self,
        out_f: Optional[Union[str, Path, BinaryIO]] = None,
        format: str = "mp3",
        codec: Optional[str] = None,
        bitrate: Optional[str] = None,
        parameters: Optional[Any] = None,
        tags: Optional[Any] = None,
        id3v2_version: str = "4",
        cover: Optional[Any] = None,
    ) -> Union[BinaryIO, Any, Path]: ...
    def overlay(
        self,
        seg: "AudioSegment",
        position: int = 0,
        loop: bool = False,
        times: Optional[int] = None,
        gain_during_overlay: Optional[float] = None,
    ) -> "AudioSegment": ...
    def get_array_of_samples(
        self, array_type_override: Optional[Any] = None
    ) -> array.array[int]: ...
    def __getitem__(self, item: Union[slice, int]) -> "AudioSegment": ...
    def __len__(self) -> int: ...
    @property
    def channels(self) -> int: ...
    @property
    def frame_rate(self) -> int: ...
    @property
    def sample_width(self) -> int: ...
    @property
    def max_possible_amplitude(self) -> float: ...
    @property
    def rms(self) -> int: ...
    @property
    def dBFS(self) -> float: ...
    @property
    def duration_seconds(self) -> float: ...
