import argparse

from .config import DEFAULT_COMP_AUDIO_DURATION
from .process import process_audio_files


def main():
    """
    Command-line entry point for processing audio files.
    """
    parser = argparse.ArgumentParser(
        description="Align audio files, extract speech, transcribe, and generate SRT files."
    )
    parser.add_argument(
        "-d",
        "--directory",
        default="./",
        help="Directory containing audio files (default: './')",
    )
    parser.add_argument(
        "-r", "--reference", default=None, help="Path to the reference audio file."
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Path to save the synthesized audio (default: 'combined_audio.wav')",
    )
    parser.add_argument(
        "-c",
        "--comp_duration",
        type=float,
        default=DEFAULT_COMP_AUDIO_DURATION,
        help="Duration in seconds for alignment comparison (default: 10s)",
    )
    parser.add_argument(
        "-od",
        "--out_duration",
        type=int,
        default=None,
        help="Duration in seconds for the output audio (default: None).",
    )
    parser.add_argument(
        "-nc",
        "--no-convert",
        action="store_true",
        help="Skip converting audio files to WAV format.",
    )
    args = parser.parse_args()

    process_audio_files(
        reference_path=args.reference,
        directory=args.directory,
        output_path=args.output,
        comp_duration=args.comp_duration,
        out_duration=args.out_duration,
        convert=not args.no_convert,
    )


if __name__ == "__main__":
    main()
