from pathlib import Path
from typing import cast

import numpy as np
from pydub import AudioSegment
from tqdm import tqdm

from waddle.audios.call_tools import transcribe
from waddle.config import (
    DEFAULT_BUFFER_DURATION,
    DEFAULT_CHUNK_DURATION,
    DEFAULT_LANGUAGE,
    DEFAULT_TARGET_DB,
    DEFAULT_THRESHOLD_DB,
)
from waddle.processing.combine import SpeechTimeline
from waddle.utils import (
    format_audio_filename,
    format_time,
    parse_audio_filename,
    prepare_dir,
    time_to_seconds,
)


class SegmentsProcessor:
    """
    A class to detect, merge, normalize, export, and transcribe speech segments from an audio file.
    """

    def __init__(
        self,
        segs_dir_path: Path,
        timeline: SpeechTimeline,
    ):
        """
        Initialize the SegmentsProcessor with the path to the segments folder and the speech timeline.
        """
        self.segs_dir_path = segs_dir_path
        self.timeline = timeline

    # Public getters
    def get_segs_dir_path(self) -> Path:
        return self.segs_dir_path

    def get_timeline(self) -> SpeechTimeline:
        return self.timeline

    def get_both(self) -> tuple[Path, SpeechTimeline]:
        return (self.segs_dir_path, self.timeline)

    # ------------------------------
    # Factory Methods (Class Methods)
    # ------------------------------
    @classmethod
    def from_audio(
        cls,
        audio_path: Path,
        threshold_db: float = DEFAULT_THRESHOLD_DB,
        chunk_size_ms: int = int(DEFAULT_CHUNK_DURATION * 1000),
        buffer_size_ms: int = int(DEFAULT_BUFFER_DURATION * 1000),
        target_dBFS: float = DEFAULT_TARGET_DB,
    ) -> "SegmentsProcessor":
        """
        Create segments from an audio file.

        Args:
            audio_path (Path): Path to the audio file.
            threshold_db (float, optional): Threshold in dB for detecting speech. Defaults to -30.
            chunk_size_ms (int, optional): Size of audio chunks in milliseconds. Defaults to 1000.
            buffer_size_ms (int, optional): Buffer size in milliseconds. Defaults to 500.
            target_dBFS (float, optional): Target dBFS level for normalization. Defaults to -20.

        Returns:
            SegmentsProcessor: SegmentsProcessor instance.
        """
        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        audio = AudioSegment.from_file(str(audio_path))

        # Step 1: Detect raw speech timeline.
        raw_timeline = cls._detect_raw_timeline(audio, threshold_db, chunk_size_ms, buffer_size_ms)

        # Step 2: Merge timeline.
        timeline = cls._merge_raw_timeline(raw_timeline)

        if not timeline:
            print("[Warning] No speech segments detected.")
            segs_folder = audio_path.parent / f"{audio_path.stem}_segs"
            prepare_dir(segs_folder)
            return cls(segs_folder, timeline)

        # Step 3: Calculate gain adjustment for normalization.
        gain_adjustment = cls._calculate_gain_adjustment(audio, timeline, target_dBFS)

        # Step 4: Export normalized segments.
        segs_dir_path = audio_path.parent / f"{audio_path.stem}_segs"
        cls._export_normalized_segments(audio, timeline, gain_adjustment, segs_dir_path)

        # Clean up original audio file.
        audio_path.unlink()

        print(f"[INFO] Global normalization applied with gain adjustment: {gain_adjustment} dB")
        return cls(segs_dir_path, timeline)

    @classmethod
    def process(
        cls,
        audio_path: Path,
        threshold_db: float = DEFAULT_THRESHOLD_DB,
        chunk_size_ms: int = int(DEFAULT_CHUNK_DURATION * 1000),
        buffer_size_ms: int = int(DEFAULT_BUFFER_DURATION * 1000),
        target_dBFS: float = DEFAULT_TARGET_DB,
        is_transcribe: bool = False,
        transcription_output_path_or_none: Path | None = None,
        whisper_options: str = f"-l {DEFAULT_LANGUAGE}",
    ) -> "SegmentsProcessor":
        """
        Process an audio file, it will detect, normalize, export segments, and transcribe if needed.

        Args:
            audio_path (Path): Path to the audio file.
            threshold_db (float, optional): Threshold in dB for detecting speech. Defaults to -30.
            chunk_size_ms (int, optional): Size of audio chunks in milliseconds. Defaults to 1000.
            buffer_size_ms (int, optional): Buffer size in milliseconds. Defaults to 500.
            target_dBFS (float, optional): Target dBFS level for normalization. Defaults to -20.

            is_transcribe (bool, optional): Whether to transcribe the detected segments.
            transcription_output_path_or_none (Path | None, optional): Path to transcription file.
            whisper_options (str, optional): Options for whisper transcribe. Defaults to "-l ja".

        Returns:
            SegmentsProcessor: SegmentsProcessor instance.
        """
        processor = cls.from_audio(
            audio_path,
            threshold_db=threshold_db,
            chunk_size_ms=chunk_size_ms,
            buffer_size_ms=buffer_size_ms,
            target_dBFS=target_dBFS,
        )

        if is_transcribe and processor.timeline:
            transcription_output_path = (
                transcription_output_path_or_none or audio_path.parent / f"{audio_path.stem}.srt"
            )
            processor.transcribe_segments(transcription_output_path, whisper_options)
        else:
            print("[Warning] No speech segments detected; skipping transcription.")

        return processor

    # ------------------------------
    # Public Instance Methods
    # ------------------------------
    def transcribe_segments(
        self,
        transcription_output_path: Path,
        whisper_options: str = f"-l {DEFAULT_LANGUAGE}",
    ) -> None:
        """
        Transcribe the detected segments and create a combined SRT file.
        """
        seg_file_paths = sorted(
            self.segs_dir_path.glob("*.wav"), key=lambda x: int(x.stem.split("_")[1])
        )
        transcription_entries = []

        for segs_file_path in tqdm(
            seg_file_paths,
            desc=f"[INFO] Transcribing {len(seg_file_paths)} segments",
            total=len(seg_file_paths),
            dynamic_ncols=True,
            bar_format="{l_bar}{bar:50}{r_bar}",
        ):
            start, _ = parse_audio_filename(str(segs_file_path))
            start_seconds = float(start) / 1000

            # Transcribe segment.
            srt_output_path = segs_file_path.with_suffix(".srt")
            transcribe(segs_file_path, srt_output_path, options=whisper_options)

            # Adjust transcription timestamps.
            transcription_entries.extend(
                self._adjust_srt_timestamps(srt_output_path, start_seconds)
            )
            srt_output_path.unlink()

        # Create a single SRT file from all segments.
        with open(str(transcription_output_path), "w", encoding="utf-8") as srt_out:
            for idx, (start_time, end_time, text) in enumerate(transcription_entries, start=1):
                srt_out.write(f"{idx}\n")
                srt_out.write(f"{start_time} --> {end_time}\n")
                srt_out.write(f"{text}\n\n")

    # ------------------------------
    # Private Helper Methods (Class Methods)
    # ------------------------------
    @classmethod
    def _detect_raw_timeline(
        cls, audio: AudioSegment, threshold_db: float, chunk_size_ms: int, buffer_size_ms: int
    ) -> SpeechTimeline:
        """
        Detect raw speech timeline by iterating over audio chunks.
        Returns a list of (start_ms, end_ms) tuples.
        """
        duration = len(audio)
        timeline = []
        current_timeline = None

        for i in tqdm(
            range(0, duration, chunk_size_ms),
            desc="[INFO] Detecting speech timeline",
        ):
            chunk = cast(AudioSegment, audio[i : i + chunk_size_ms])
            if chunk.dBFS > threshold_db:
                start_ms = max(0, i - buffer_size_ms)
                end_ms = min(duration, i + chunk_size_ms + buffer_size_ms)
                if current_timeline is None:
                    current_timeline = [start_ms, end_ms]
                else:
                    current_timeline[1] = end_ms
            else:
                if current_timeline is not None:
                    timeline.append((current_timeline[0], current_timeline[1]))
                    current_timeline = None

        if current_timeline is not None:
            timeline.append((current_timeline[0], current_timeline[1]))

        return timeline

    @classmethod
    def _merge_raw_timeline(cls, raw_timeline: SpeechTimeline) -> SpeechTimeline:
        """
        Merge overlapping or adjacent segments.
        """
        timeline = []
        for seg in raw_timeline:
            if not timeline or seg[0] > timeline[-1][1]:
                timeline.append(seg)
            else:
                timeline[-1] = (timeline[-1][0], max(timeline[-1][1], seg[1]))
        return timeline

    @classmethod
    def _calculate_gain_adjustment(
        cls, audio: AudioSegment, timeline: SpeechTimeline, target_dBFS: float
    ):
        """
        Calculate gain adjustment based on the 95th percentile of segment dBFS levels.
        """
        max_dBFS_list = []
        for seg in timeline:
            seg_audio = cast(AudioSegment, audio[seg[0] : seg[1]])
            max_dBFS_list.append(seg_audio.dBFS)

        if not max_dBFS_list:
            raise ValueError("[Warning] No speech segments detected.")

        percentile_95 = float(np.percentile(max_dBFS_list, 95))
        return target_dBFS - percentile_95

    @classmethod
    def _export_normalized_segments(
        cls, audio, timeline: SpeechTimeline, gain_adjustment: float, output_folder: Path
    ) -> None:
        """
        Apply gain adjustment to each segment and export as WAV files.
        """
        prepare_dir(output_folder)
        for seg in timeline:
            seg_audio = audio[seg[0] : seg[1]]
            normalized_audio = seg_audio.apply_gain(gain_adjustment)
            seg_audio_path = output_folder / format_audio_filename("seg", seg[0], seg[1])
            normalized_audio.export(seg_audio_path, format="wav")

    # ------------------------------
    # Private Helper Methods (Instance Methods)
    # ------------------------------
    def _adjust_srt_timestamps(
        self, transcribe_file_path: Path, start_offset: float
    ) -> SpeechTimeline:
        """
        Adjust SRT timestamps by adding the segment's start offset.
        """
        transcribe_file_path = Path(transcribe_file_path)
        if not transcribe_file_path.is_file():
            print(f"[Warning] SRT file not found for segment: {transcribe_file_path}")
            return []

        with open(str(transcribe_file_path), "r", encoding="utf-8") as srt_file:
            blocks = srt_file.read().strip().split("\n\n")

        segment_entries = []
        for block in blocks:
            lines = block.split("\n")
            if len(lines) < 3:
                continue

            _, timestamps, *text_lines = lines
            s_timestamp, e_timestamp = timestamps.split(" --> ")
            text = " ".join(text_lines)

            adjusted_start = format_time(start_offset + time_to_seconds(s_timestamp))
            adjusted_end = format_time(start_offset + time_to_seconds(e_timestamp))

            segment_entries.append((adjusted_start, adjusted_end, text))
        return segment_entries
