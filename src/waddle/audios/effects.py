from pydub import AudioSegment, effects


def normalize_audio(input_path, output_path):
    """
    Normalize audio using pydub.
    """
    audio = AudioSegment.from_file(input_path)
    normalized_audio = effects.normalize(audio)
    normalized_audio.export(output_path, format="wav")


def silence_removal(input_path, output_path):
    """
    Remove silence from audio using pydub.
    """
    audio = AudioSegment.from_file(input_path)
    trimmed_audio = effects.strip_silence(
        audio, silence_len=1400, padding=1000, silence_thresh=-60
    )
    trimmed_audio.export(output_path, format="wav")
