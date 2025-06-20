import argparse
from textwrap import dedent

from waddle.config import DEFAULT_COMP_AUDIO_DURATION, DEFAULT_LANGUAGE
from waddle.utils import phrase_time_to_seconds


def create_waddle_parser():
    """
    Create a command-line argument parser for the Waddle audio processing tool.

    The parser supports four subcommands:
    - single: Process a single audio file
    - preprocess: Preprocess multiple audio files
    - postprocess: Postprocess multiple audio files
    - metadata: Extract and process metadata from an annotated SRT file
    - init: Initialize a new waddle project with folder structure

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(exit_on_error=False)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Create subparsers with descriptions
    single_parser = subparsers.add_parser(
        "single",
        description=(
            "Process a single audio file: "
            "noise removal, normalize, silence removal, and transcription."
        ),
    )
    preprocess_parser = subparsers.add_parser(
        "preprocess",
        description=(
            "Preprocess audio files: align audios, remove noise, normalize, and silence removal."
        ),
    )
    postprocess_parser = subparsers.add_parser(
        "postprocess",
        description="Postprocess audio files: silence removal, merge, and transcription.",
    )

    # ===== PRIMARY INPUT ARGUMENTS =====
    # Add single parser's input argument
    single_parser.add_argument(
        "audio",
        help="Path to the single audio file to process.",
    )

    # Add directory input for multi-file operations
    for p in [preprocess_parser, postprocess_parser]:
        if p == preprocess_parser:
            default_directory = "0_raw"
        elif p == postprocess_parser:
            default_directory = "2_edited"
        else:
            default_directory = "./"

        p.add_argument(
            "-d",
            "--directory",
            default=default_directory,
            help=f"Directory containing audio files (default: '{default_directory}').",
        )

    # ===== COMMON ARGUMENTS FOR ALL PARSERS =====
    parsers = [single_parser, preprocess_parser, postprocess_parser]
    for p in parsers:
        if p == preprocess_parser:
            default_output = "1_pre"
        elif p == postprocess_parser:
            default_output = "3_post"
        else:  # single_parser
            default_output = "./out"

        p.add_argument(
            "-o",
            "--output",
            default=default_output,
            help=f"Directory to save the output (default: '{default_output}').",
        )
        p.add_argument(
            "-ss",
            type=phrase_time_to_seconds,
            default=0.0,
            help="Start time in seconds for the audio segment (default: 0.0).",
        )
        p.add_argument(
            "-t",
            "--time",
            type=phrase_time_to_seconds,
            default=None,
            help="Duration in seconds for the output audio (default: None).",
        )
        p.add_argument(
            "-wo",
            "--whisper-options",
            default=f"-l {DEFAULT_LANGUAGE}",
            help=(
                f"Options to pass to Whisper transcription (default: '-l {DEFAULT_LANGUAGE}').\n"
                "You can change the default language by modifying src/config.py."
            ),
        )

    # ===== OTHER OPTIONS =====
    # Noise removal (for audio preprocessing)
    for p in [single_parser, preprocess_parser]:
        p.add_argument(
            "-nnr",
            "--no-noise-remove",
            action="store_true",
            help="Skip removing noise from the audio.",
        )

    # preprocess options
    preprocess_parser.add_argument(
        "-r",
        "--reference",
        default=None,
        help="Path to the reference audio file (used in multi-file mode).",
    )
    preprocess_parser.add_argument(
        "-c",
        "--comp-duration",
        type=float,
        default=DEFAULT_COMP_AUDIO_DURATION,
        help=(
            "Duration in seconds for alignment comparison "
            f"(default: {DEFAULT_COMP_AUDIO_DURATION}s)."
        ),
    )
    preprocess_parser.add_argument(
        "-nc",
        "--no-convert",
        action="store_true",
        help="Skip converting audio files to WAV format.",
    )
    preprocess_parser.add_argument(
        "-tr",
        "--transcribe",
        action="store_true",
        help="Transcribe the processed audio files.",
    )

    # install
    subparsers.add_parser(
        "install",
        description=(
            "Install all required tools for waddle "
            "(DeepFilterNet, whisper.cpp, FFmpeg, CMake, fmt)."
        ),
    )

    # metadata
    show_notes_parser = subparsers.add_parser(
        "metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent("""\
            Generate metadata from an annotated SRT file.

            - `# Chapter` markers are used to define chapters.
                - Similar to Markdown, `#` indicates the level of the chapter, up to 6 levels.
                - The chapter starts at the next SRT timestamp and ends before next chapter.
            - Any other text is considered show notes.
            - Empty lines are ignored.
                - Use `;` to add newlines in show notes. The `;` will be deleted.
        """),
    )
    show_notes_parser.add_argument(
        "source",
        nargs="?",
        default="3_post/*.srt",
        help="Path to the annotated SRT file (default: looks for SRT files in 3_post/).",
    )
    show_notes_parser.add_argument(
        "-i",
        "--input",
        help="Path to the input audio file. If not specified, it will look for an audio file with"
        " the same name.",
        default=None,
    )
    show_notes_parser.add_argument(
        "-o",
        "--output",
        help="Directory to save the metadata and audio files.",
        default="4_meta",
    )

    # init
    init_parser = subparsers.add_parser(
        "init",
        description="Initialize a new waddle project with folder structure.",
    )
    init_parser.add_argument(
        "project_name",
        nargs="?",
        default="",
        help="Name of the project directory (default: create folders in current directory).",
    )

    return parser
