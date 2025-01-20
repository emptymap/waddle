import argparse
import os

from .config import DEFAULT_COMP_AUDIO_DURATION
from .processor import process_multi_files, process_single_file


def main():
    """
    Command-line entry point for processing audio files.
    """
    parser = argparse.ArgumentParser(
        description="Align audio files, extract speech, transcribe, and generate SRT files."
    )
    parser.add_argument(
        "-a",
        "--audio",
        help="Path to the single audio file to process. If provided, the script processes this file in single-file mode.",
    )
    parser.add_argument(
        "-d",
        "--directory",
        default="./",
        help="Directory containing audio files (used in multi-file mode, default: './').",
    )
    parser.add_argument(
        "-r",
        "--reference",
        default=None,
        help="Path to the reference audio file (used in multi-file mode).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Path to save the output. For single-file mode, this is the directory to save results. For multi-file mode, it is the synthesized audio file path.",
    )
    parser.add_argument(
        "-c",
        "--comp_duration",
        type=float,
        default=DEFAULT_COMP_AUDIO_DURATION,
        help="Duration in seconds for alignment comparison (default: 10s).",
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

    if args.audio:
        # Single-file mode
        if not os.path.isfile(args.audio):
            raise FileNotFoundError(f"Audio file not found: {args.audio}")
        if not args.output:
            output_dir = os.path.join("./", "out")
            os.makedirs(output_dir, exist_ok=True)

        print(f"[INFO] Processing single audio file: {args.audio}")
        process_single_file(
            aligned_audio_path=args.audio,
            output_dir=args.output,
            speaker_file=os.path.basename(args.audio),
        )
        print(f"[INFO] Processed single audio file saved in: {args.output}")
    else:
        # Multi-file mode
        process_multi_files(
            reference_path=args.reference,
            directory=args.directory,
            output_path=args.output,
            comp_duration=args.comp_duration,
            out_duration=args.out_duration,
            convert=not args.no_convert,
        )


if __name__ == "__main__":
    main()
