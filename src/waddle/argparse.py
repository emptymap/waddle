import argparse

from waddle.config import DEFAULT_COMP_AUDIO_DURATION, DEFAULT_LANGUAGE
from waddle.utils import phrase_time_to_seconds


def create_waddle_parser():
    parser = argparse.ArgumentParser(exit_on_error=False)

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    single_parser = subparsers.add_parser(
        "single",
        description="Process a single audio file: normalize, detect speech, and transcribe.",
    )
    single_parser.add_argument(
        "audio",
        help="Path to the single audio file to process.",
    )
    single_parser.add_argument(
        "-o",
        "--output",
        default="./out",
        help="Directory to save the output (default: './out').",
    )
    single_parser.add_argument(
        "-ss",
        type=phrase_time_to_seconds,
        default=0.0,
        help="Start time in seconds for the audio segment (default: None).",
    )
    single_parser.add_argument(
        "-t",
        "--time",
        type=phrase_time_to_seconds,
        default=None,
        help="Duration in seconds for the output audio (default: None).",
    )
    single_parser.add_argument(
        "-wo",
        "--whisper-options",
        default=f"-l {DEFAULT_LANGUAGE}",
        help=(
            "Options to pass to Whisper transcription (default: '-l {DEFAULT_LANGUAGE}').\n"
            "You can change the default language by modifying src/config.py."
        ),
    )

    preprocess_parser = subparsers.add_parser(
        "preprocess",
        description="Preprocess audio files.",
    )
    preprocess_parser.add_argument(
        "-d",
        "--directory",
        default="./",
        help="Directory containing audio files (used in multi-file mode, default: './').",
    )
    preprocess_parser.add_argument(
        "-r",
        "--reference",
        default=None,
        help="Path to the reference audio file (used in multi-file mode).",
    )
    preprocess_parser.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Path to save the output. For single-file mode, this is the directory to save results. "
            "For multi-file mode, it is the synthesized audio file path."
        ),
    )
    preprocess_parser.add_argument(
        "-c",
        "--comp-duration",
        type=float,
        default=DEFAULT_COMP_AUDIO_DURATION,
        help="Duration in seconds for alignment comparison (default: 10s).",
    )
    preprocess_parser.add_argument(
        "-ss",
        type=phrase_time_to_seconds,
        default=0.0,
        help="Start time in seconds for the audio segment (default: None).",
    )
    preprocess_parser.add_argument(
        "-t",
        "--time",
        type=phrase_time_to_seconds,
        default=None,
        help="Duration in seconds for the output audio (default: None).",
    )
    preprocess_parser.add_argument(
        "-nc",
        "--no-convert",
        action="store_true",
        help="Skip converting audio files to WAV format.",
    )

    postprocess_parser = subparsers.add_parser(
        "postprocess",
        description="Postprocess audio files: merge and finalize outputs.",
    )
    postprocess_parser.add_argument(
        "-d",
        "--directory",
        required=True,
        help="Directory containing audio files to be postprocessed.",
    )
    postprocess_parser.add_argument(
        "-o",
        "--output",
        default="./out",
        help="Directory to save the postprocessed audio files (default: './out').",
    )
    postprocess_parser.add_argument(
        "-wo",
        "--whisper-options",
        default=f"-l {DEFAULT_LANGUAGE}",
        help=(
            "Options to pass to Whisper transcription (default: '-l {DEFAULT_LANGUAGE}').\n"
            "You can change the default language by modifying src/config.py."
        ),
    )

    return parser
