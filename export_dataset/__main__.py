import argparse
import csv
from pathlib import Path

import librosa
import soundfile

from .trim import trim_silence
from .vad import SileroVoiceActivityDetector

_DIR = Path(__file__).parent


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    #
    parser.add_argument("--threshold", type=float, default=0.8)
    parser.add_argument("--samples-per-chunk", type=int, default=480)
    parser.add_argument("--keep-chunks-before", type=int, default=2)
    parser.add_argument("--keep-chunks-after", type=int, default=5)
    #
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    wav_dir = output_dir / "wav"

    detector = make_silence_detector()

    with open(output_dir / "metadata.csv", "w", encoding="utf-8") as metadata_file:
        writer = csv.writer(metadata_file, delimiter="|")
        for audio_path in input_dir.rglob("*.webm"):
            text_path = audio_path.with_suffix(".txt")
            if not text_path.exists():
                continue

            text = text_path.read_text(encoding="utf-8").strip()
            wav_path = wav_dir / audio_path.relative_to(input_dir).with_suffix(".wav")
            wav_id = wav_path.relative_to(wav_dir)

            # Trim silence first.
            #
            # The VAD model works on 16khz, so we determine the portion of audio
            # to keep and then just load that with librosa.
            vad_sample_rate = 16000
            audio_16khz, _sr = librosa.load(path=audio_path, sr=vad_sample_rate)

            offset_sec, duration_sec = trim_silence(
                audio_16khz,
                detector,
                threshold=args.threshold,
                samples_per_chunk=args.samples_per_chunk,
                sample_rate=vad_sample_rate,
                keep_chunks_before=args.keep_chunks_before,
                keep_chunks_after=args.keep_chunks_after,
            )

            audio, sample_rate = librosa.load(
                path=audio_path,
                offset=offset_sec,
                duration=duration_sec,
            )

            # Write as WAV
            wav_path.parent.mkdir(parents=True, exist_ok=True)
            soundfile.write(wav_path, audio, sample_rate, format="WAV")

            # id|text
            writer.writerow((wav_id, text))

            print(wav_path)


def make_silence_detector() -> SileroVoiceActivityDetector:
    silence_model = _DIR / "models" / "silero_vad.onnx"
    return SileroVoiceActivityDetector(silence_model)


if __name__ == "__main__":
    main()
