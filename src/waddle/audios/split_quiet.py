import shutil
from pathlib import Path

from pydub import AudioSegment
from pydub.silence import detect_silence


def split_audio_by_longest_silence(
    audio_path: Path,
    min_ms=5000,
    max_ms=20000,
    silence_thresh=-40,
    min_silence_len=100,
) -> Path:
    """
    Split audio file by finding the longest quiet parts within specified segment duration ranges

    Parameters:
    - audio_path: Path to audio file
    - min_ms: Minimum segment duration in milliseconds
    - max_ms: Maximum segment duration in milliseconds
    - silence_thresh: Silence detection threshold (dBFS)
    - min_silence_len: Minimum silence length to detect (milliseconds)
    """
    splited_dir_path = audio_path.parent / "splited"
    if splited_dir_path.exists():
        shutil.rmtree(splited_dir_path)
    splited_dir_path.mkdir(parents=True, exist_ok=True)
    audio = AudioSegment.from_file(str(audio_path))

    silent_segments = detect_silence(
        audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh
    )

    # Pre-calculate silence centers and durations for efficiency
    silence_data = []
    for start, end in silent_segments:
        center = (start + end) // 2
        duration = end - start
        silence_data.append((center, duration, start, end))
    silence_data.sort(key=lambda x: x[0])

    # Find optimal split points
    split_points = [0]  # Always start from beginning
    current_pos = 0
    silence_index = 0  # Track position in sorted silence list

    while current_pos < len(audio):
        # Calculate the search range for next split point
        earliest_split = current_pos + min_ms
        latest_split = current_pos + max_ms

        if earliest_split >= len(audio):
            break

        latest_split = min(latest_split, len(audio))

        # Find silence segments within the valid range more efficiently
        candidate_silences = []
        temp_index = silence_index

        # Skip silences before our range
        while temp_index < len(silence_data) and silence_data[temp_index][0] < earliest_split:
            temp_index += 1

        # Collect silences within range
        while temp_index < len(silence_data) and silence_data[temp_index][0] <= latest_split:
            center, duration, start, end = silence_data[temp_index]
            candidate_silences.append((center, duration))
            temp_index += 1

        if candidate_silences:
            # Find the silence with longest duration
            best_silence = max(candidate_silences, key=lambda x: x[1])
            best_split = best_silence[0]  # Use the center position
            split_points.append(best_split)
            current_pos = best_split

            # Update silence_index for next iteration
            while silence_index < len(silence_data) and silence_data[silence_index][0] < best_split:
                silence_index += 1
        else:
            # No suitable silence found, split at maximum allowed position
            split_points.append(latest_split)
            current_pos = latest_split

    # Add final point if not already at the end
    if split_points[-1] < len(audio):
        split_points.append(len(audio))

    # Remove duplicates and sort
    split_points = sorted(list(set(split_points)))
    for i in range(len(split_points) - 1):
        start_time = split_points[i]
        end_time = split_points[i + 1]

        chunk = audio[start_time:end_time]
        output_filename = f"silence_chunk_{i + 1:06d}.wav"
        output_path = splited_dir_path / output_filename
        chunk.export(str(output_path), format="wav")

    return splited_dir_path


def analyze_silence_distribution(audio_file_path: Path, silence_thresh=-40, min_silence_len=100):
    """
    Analyze silence distribution in audio file for debugging purposes

    Parameters:
    - audio_file_path: Path to audio file
    - silence_thresh: Silence detection threshold (dBFS)
    - min_silence_len: Minimum silence length to detect (milliseconds)
    """
    audio = AudioSegment.from_file(str(audio_file_path))
    silent_segments = detect_silence(
        audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh
    )

    print(f"\nSilence analysis for {audio_file_path.name}:")
    print(f"Total audio duration: {len(audio) / 1000:.1f} seconds")
    print(f"Found {len(silent_segments)} silence segments:")

    for i, (start, end) in enumerate(silent_segments[:10]):  # Show first 10
        duration = (end - start) / 1000
        position = start / 1000
        print(f"  {i + 1}: {position:.1f}s - {(end / 1000):.1f}s (duration: {duration:.1f}s)")

    if len(silent_segments) > 10:
        print(f"  ... and {len(silent_segments) - 10} more")


if __name__ == "__main__":
    input_file = Path("tests/ep0/ep12-shun.wav")

    analyze_silence_distribution(input_file)

    split_audio_by_longest_silence(
        audio_path=input_file,
        min_ms=2000,
        max_ms=10000,
        silence_thresh=-40,
        min_silence_len=100,
    )

    shutil.rmtree(input_file.parent / "splited", ignore_errors=True)

    print("\nSplitting completed!")
