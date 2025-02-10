import os

from pydub import AudioSegment
from tqdm import tqdm

from waddle.config import DEFAULT_CHUNK_DURATION


def chunk_audio(input_path: str, output_dir: str, chunk_length: int = DEFAULT_CHUNK_DURATION):
    """Splits audio into chunks and saves them in the specified directory."""
    audio = AudioSegment.from_file(input_path)
    chunk_length_ms = chunk_length * 1000

    os.makedirs(output_dir, exist_ok=True)
    for i, start in enumerate(
        tqdm(range(0, len(audio), chunk_length_ms), desc="[INFO] Chunking audio")
    ):
        chunk = audio[start : start + chunk_length_ms]
        chunk_path = os.path.join(output_dir, f"chunk_{str(i).zfill(8)}.wav")
        chunk.export(chunk_path, format="wav")


def chunk_concat(chunks_dir: str, output_path: str):
    """Concatenates all audio chunks in the given directory into a single file."""
    chunk_files = [
        os.path.join(chunks_dir, f) for f in sorted(os.listdir(chunks_dir)) if f.endswith(".wav")
    ]
    final_audio = AudioSegment.empty()

    for chunk_file in tqdm(chunk_files, desc="[INFO] Concatenating chunks"):
        final_audio += AudioSegment.from_file(chunk_file)

    final_audio.export(output_path, format="wav")
