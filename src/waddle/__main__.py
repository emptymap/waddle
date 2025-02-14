import os
import shutil

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
    if not os.path.isfile(args.audio):
        raise FileNotFoundError(f"Audio file not found: {args.audio}")
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    # Copy the audio file to the output directory
    audio_file_name = os.path.basename(args.audio)
    output_audio_path = os.path.join(output_dir, audio_file_name)
    print(f"[INFO] Copying audio file to: {output_audio_path}")
    shutil.copy(args.audio, output_audio_path)

    print(f"[INFO] Processing single audio file: {output_audio_path}")
    process_single_file(
        aligned_audio_path=output_audio_path,
        output_dir=output_dir,
        speaker_file=os.path.basename(args.audio),
        out_duration=args.time,
    )
    print(f"[INFO] Processed single audio file saved in: {output_dir}")


def do_preprocess(args):
    preprocess_multi_files(
        reference_path=args.reference,
        audio_source_directory=args.directory,
        output_dir=args.output or "./out",
        comp_duration=args.comp_duration,
        out_duration=args.time,
        convert=not args.no_convert,
    )


if __name__ == "__main__":
    main()
