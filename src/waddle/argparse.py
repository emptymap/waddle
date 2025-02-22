import argparse
from dataclasses import dataclass

from waddle.config import DEFAULT_COMP_AUDIO_DURATION, DEFAULT_LANGUAGE
from waddle.utils import phrase_time_to_seconds


@dataclass
class CommonArguments:
    """Common arguments shared between commands."""

    output_help: str
    whisper_help: str = (
        f"Options to pass to Whisper transcription (default: '-l {DEFAULT_LANGUAGE}').\n"
        "You can change the default language by modifying src/config.py."
    )
    time_help: str = "Duration in seconds for the output audio (default: None)."
    start_time_help: str = "Start time in seconds for the audio segment (default: None)."


def add_common_arguments(
    parser: argparse.ArgumentParser,
    args: CommonArguments,
    include_whisper: bool = True,
    include_time: bool = True,
    output_required: bool = False,
) -> None:
    """Add common arguments to a parser."""
    parser.add_argument(
        "-o",
        "--output",
        default="./out" if not output_required else None,
        required=output_required,
        help=args.output_help,
    )

    if include_time:
        parser.add_argument(
            "-ss",
            type=phrase_time_to_seconds,
            default=0.0,
            help=args.start_time_help,
        )
        parser.add_argument(
            "-t",
            "--time",
            type=phrase_time_to_seconds,
            default=None,
            help=args.time_help,
        )

    if include_whisper:
        parser.add_argument(
            "-wo",
            "--whisper-options",
            default=f"-l {DEFAULT_LANGUAGE}",
            help=args.whisper_help,
        )


def create_single_parser(subparsers: argparse._SubParsersAction) -> None:
    """Create parser for single file processing."""
    parser = subparsers.add_parser(
        "single",
        description="Process a single audio file: normalize, detect speech, and transcribe.",
    )
    parser.add_argument(
        "audio",
        help="Path to the single audio file to process.",
    )
    add_common_arguments(
        parser,
        CommonArguments(
            output_help="Directory to save the output (default: './out').",
        ),
    )


def create_preprocess_parser(subparsers: argparse._SubParsersAction) -> None:
    """Create parser for preprocessing."""
    parser = subparsers.add_parser(
        "preprocess",
        description="Preprocess audio files.",
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
        "-c",
        "--comp-duration",
        type=float,
        default=DEFAULT_COMP_AUDIO_DURATION,
        help="Duration in seconds for alignment comparison (default: 10s).",
    )
    parser.add_argument(
        "-nc",
        "--no-convert",
        action="store_true",
        help="Skip converting audio files to WAV format.",
    )
    add_common_arguments(
        parser,
        CommonArguments(
            output_help=(
                "Path to save the output. For single-file mode, this is the directory to save results. "
                "For multi-file mode, it is the synthesized audio file path."
            ),
        ),
        include_whisper=False,
    )


def create_postprocess_parser(subparsers: argparse._SubParsersAction) -> None:
    """Create parser for postprocessing."""
    parser = subparsers.add_parser(
        "postprocess",
        description="Postprocess audio files: merge and finalize outputs.",
    )
    parser.add_argument(
        "-d",
        "--directory",
        required=True,
        help="Directory containing audio files to be postprocessed.",
    )
    add_common_arguments(
        parser,
        CommonArguments(
            output_help="Directory to save the postprocessed audio files (default: './out').",
        ),
        include_time=False,
    )


def validate_time_args(args: argparse.Namespace) -> None:
    """Validate time-related arguments."""
    if hasattr(args, "time") and args.time is not None and args.time <= 0:
        raise argparse.ArgumentTypeError("Duration must be positive")
    if hasattr(args, "ss") and args.ss < 0:
        raise argparse.ArgumentTypeError("Start time cannot be negative")
    if hasattr(args, "comp_duration") and args.comp_duration <= 0:
        raise argparse.ArgumentTypeError("Comparison duration must be positive")


def create_waddle_parser() -> argparse.ArgumentParser:
    """
    Create argument parser for the waddle command-line tool.

    The parser supports three main commands:
    - single: Process a single audio file
    - preprocess: Prepare multiple audio files for processing
    - postprocess: Combine and finalize processed audio files

    Returns:
        ArgumentParser configured with all necessary arguments

    Raises:
        ArgumentTypeError: If argument values are invalid
    """
    parser = argparse.ArgumentParser(exit_on_error=False)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Create parsers for each command
    create_single_parser(subparsers)
    create_preprocess_parser(subparsers)
    create_postprocess_parser(subparsers)

    # Add validation
    original_parse_args = parser.parse_args

    def parse_args_with_validation(*args, **kwargs):
        parsed_args = original_parse_args(*args, **kwargs)
        validate_time_args(parsed_args)
        return parsed_args

    parser.parse_args = parse_args_with_validation  # type: ignore

    return parser
