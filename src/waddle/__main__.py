import shutil
from pathlib import Path

from waddle.argparse import create_waddle_parser
from waddle.processor import preprocess_multi_files, process_single_file


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


def do_single(args):
    audio_path = Path(args.audio)
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {args.audio}")
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy the audio file to the output directory
    audio_file_name = audio_path.name
    output_audio_path = output_dir / audio_file_name
    print(f"[INFO] Copying audio file to: {output_audio_path}")
    shutil.copy(args.audio, output_audio_path)

    print(f"[INFO] Processing single audio file: {output_audio_path}")
    process_single_file(
        aligned_audio_path=str(output_audio_path),
        output_dir=str(output_dir),
        speaker_file=audio_path.name,
        ss=args.ss,
        out_duration=args.time,
    )
    print(f"[INFO] Processed single audio file saved in: {output_dir}")


def do_preprocess(args):
    preprocess_multi_files(
        reference_path=args.reference,
        audio_source_directory=args.directory,
        output_dir=args.output or "./out",
        comp_duration=args.comp_duration,
        ss=args.ss,
        out_duration=args.time,
        convert=not args.no_convert,
    )


if __name__ == "__main__":
    main()
