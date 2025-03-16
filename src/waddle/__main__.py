import shutil

from waddle.argparse import create_waddle_parser
from waddle.metadata import generate_metadata
from waddle.processor import postprocess_multi_files, preprocess_multi_files, process_single_file
from waddle.utils import to_path


def main():
    """
    Command-line entry point for processing audio files.
    """
    parser = create_waddle_parser()
    args = parser.parse_args()

    match args.subcommand:
        case "single":
            do_single(args)
        case "preprocess":
            do_preprocess(args)
        case "postprocess":
            do_postprocess(args)
        case "metadata":
            do_metadata(args)
        case _:
            raise ValueError(f"Command not implemented: {args.subcommand}")


def do_single(args):
    audio_path = to_path(args.audio)
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {args.audio}")
    output_dir = to_path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy the audio file to the output directory
    audio_file_name = audio_path.name
    tmp_audio_path = output_dir / audio_file_name
    print(f"[INFO] Copying audio file to: {tmp_audio_path}")
    shutil.copy(args.audio, tmp_audio_path)

    print(f"[INFO] Processing single audio file: {tmp_audio_path}")
    process_single_file(
        aligned_audio=tmp_audio_path,
        output_dir=output_dir,
        speaker_audio=audio_path,
        ss=args.ss,
        out_duration=args.time,
        no_noise_remove=args.no_noise_remove,
        whisper_options=args.whisper_options,
    )
    print(f"[INFO] Processed single audio file saved in: {output_dir}")


def do_preprocess(args):
    reference_path_or_none = to_path(args.reference) if args.reference else None
    if reference_path_or_none is not None and not reference_path_or_none.is_file():
        raise FileNotFoundError(f"Reference file not found: {args.reference}")
    source_dir_path = to_path(args.directory)
    if not source_dir_path.is_dir():
        raise FileNotFoundError(f"Audio source directory not found: {args.directory}")
    output_dir_path = to_path(args.output or "./out")

    preprocess_multi_files(
        reference=reference_path_or_none,
        source_dir=source_dir_path,
        output_dir=output_dir_path,
        comp_duration=args.comp_duration,
        ss=args.ss,
        out_duration=args.time,
        no_noise_remove=args.no_noise_remove,
        convert=not args.no_convert,
        transcribe=args.transcribe,
        whisper_options=args.whisper_options,
    )


def do_postprocess(args):
    source_dir_path = to_path(args.directory)
    if not source_dir_path.is_dir():
        raise FileNotFoundError(f"Audio source directory not found: {args.directory}")
    output_dir_path = to_path(args.output or "./out")

    print(f"[INFO] Postprocessing audio files from: {source_dir_path}")
    postprocess_multi_files(
        source_dir=source_dir_path,
        output_dir=output_dir_path,
        ss=args.ss,
        out_duration=args.time,
        whisper_options=args.whisper_options,
    )
    print(f"[INFO] Postprocessing complete. Output saved in: {output_dir_path}")


def do_metadata(args):
    generate_metadata(args.source, args.input, args.output)


if __name__ == "__main__":
    main()
