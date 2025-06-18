import shutil
from pathlib import Path

from waddle.argparse import create_waddle_parser
from waddle.metadata import generate_metadata
from waddle.processor import postprocess_multi_files, preprocess_multi_files, process_single_file
from waddle.tools.install_all_tools import install_all_tools
from waddle.utils import to_path


def main():
    parser = create_waddle_parser()
    args = parser.parse_args()

    handlers = {
        "install": do_install,
        "init": do_init,
        "single": do_single,
        "preprocess": do_preprocess,
        "postprocess": do_postprocess,
        "metadata": do_metadata,
    }
    if args.subcommand in handlers:
        handlers[args.subcommand](args)
    else:
        raise ValueError(f"Command not implemented: {args.subcommand}")


def do_single(args):
    audio_path = to_path(args.audio)
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {args.audio}")

    output_dir = to_path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    tmp_audio_path = output_dir / audio_path.name
    shutil.copy(args.audio, tmp_audio_path)

    process_single_file(
        aligned_audio=tmp_audio_path,
        output_dir=output_dir,
        speaker_audio=audio_path,
        ss=args.ss,
        out_duration=args.time,
        no_noise_remove=args.no_noise_remove,
        whisper_options=args.whisper_options,
    )


def do_preprocess(args):
    reference = to_path(args.reference) if args.reference else None
    if reference and not reference.is_file():
        raise FileNotFoundError(f"Reference file not found: {args.reference}")

    source_dir = to_path(args.directory)
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {args.directory}")

    output_dir = to_path(args.output)

    preprocess_multi_files(
        reference=reference,
        source_dir=source_dir,
        output_dir=output_dir,
        comp_duration=args.comp_duration,
        ss=args.ss,
        out_duration=args.time,
        no_noise_remove=args.no_noise_remove,
        convert=not args.no_convert,
        transcribe=args.transcribe,
        whisper_options=args.whisper_options,
    )


def do_postprocess(args):
    source_dir = to_path(args.directory)
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {args.directory}")

    output_dir = to_path(args.output)

    postprocess_multi_files(
        source_dir=source_dir,
        output_dir=output_dir,
        ss=args.ss,
        out_duration=args.time,
        whisper_options=args.whisper_options,
    )


def do_metadata(args):
    source = args.source

    if source == "3_post/*.srt":
        srt_files = list(Path("3_post").glob("*.srt"))
        if not srt_files:
            raise FileNotFoundError("No SRT files found in 3_post/ directory")
        source = str(srt_files[0])

    generate_metadata(source, args.input, args.output)


def do_init(args):
    base_path = Path(args.project_name) if args.project_name.strip() else Path.cwd()
    base_path.mkdir(parents=True, exist_ok=True)

    for folder in ["0_raw", "1_pre", "2_edited", "3_post", "4_meta"]:
        (base_path / folder).mkdir(exist_ok=True)


def do_install(args):
    del args  # Unused parameter
    install_all_tools()


if __name__ == "__main__":
    main()
