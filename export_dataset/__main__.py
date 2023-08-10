import argparse
import csv
import logging
import shutil
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from .trim import trim_silence
from .vad import SileroVoiceActivityDetector

_DIR = Path(__file__).parent
_LOGGER = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    parser.add_argument(
        "--audio-glob", default="*.webm", help="Glob pattern for audio files"
    )
    #
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--samples-per-chunk", type=int, default=480)
    parser.add_argument("--keep-chunks-before", type=int, default=5)
    parser.add_argument("--keep-chunks-after", type=int, default=5)
    #
    parser.add_argument(
        "--skip-existing-wav",
        action="store_true",
        help="Don't overwrite existing WAV files",
    )
    #
    args = parser.parse_args()
    logging.basicConfig()

    if not shutil.which("ffmpeg"):
        _LOGGER.fatal("ffmpeg must be installed")
        return 1

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    wav_dir = output_dir / "wav"

    export_audio = ExportAudio()
    with open(
        output_dir / "metadata.csv", "w", encoding="utf-8"
    ) as metadata_file, ThreadPoolExecutor() as executor:
        writer = csv.writer(metadata_file, delimiter="|")
        writer_lock = threading.Lock()
        for audio_path in input_dir.rglob(args.audio_glob):
            executor.submit(
                export_audio,
                audio_path,
                input_dir,
                wav_dir,
                writer,
                writer_lock,
                args,
            )


class ExportAudio:
    def __init__(self):
        self.thread_data = threading.local()

    def __call__(
        self,
        audio_path: Path,
        input_dir: Path,
        wav_dir: Path,
        writer,
        writer_lock: threading.Lock,
        args: argparse.Namespace,
    ):
        try:
            text_path = audio_path.with_suffix(".txt")
            if not text_path.exists():
                _LOGGER.warning("Missing text file: %s", text_path)
                return

            if not hasattr(self.thread_data, "detector"):
                self.thread_data.detector = make_silence_detector()

            text = text_path.read_text(encoding="utf-8").strip()
            wav_path = wav_dir / audio_path.relative_to(input_dir).with_suffix(".wav")
            wav_id = wav_path.relative_to(wav_dir)

            if (not args.skip_existing_wav) or (
                (not wav_path.exists()) or (wav_path.stat().st_size == 0)
            ):
                if args.threshold <= 0:
                    offset_sec = 0.0
                    duration_sec = None
                else:
                    # Trim silence first.
                    #
                    # The VAD model works on 16khz, so we determine the portion of audio
                    # to keep and then just load that with librosa.
                    vad_sample_rate = 16000
                    audio_16khz_bytes = subprocess.check_output(
                        [
                            "ffmpeg",
                            "-i",
                            str(audio_path),
                            "-f",
                            "s16le",
                            "-acodec",
                            "pcm_s16le",
                            "-ac",
                            "1",
                            "-ar",
                            str(vad_sample_rate),
                            "pipe:",
                        ],
                        stderr=subprocess.DEVNULL,
                    )

                    # Normalize
                    audio_16khz = np.frombuffer(
                        audio_16khz_bytes, dtype=np.int16
                    ).astype(np.float32)
                    audio_16khz /= np.abs(np.max(audio_16khz))

                    offset_sec, duration_sec = trim_silence(
                        audio_16khz,
                        self.thread_data.detector,
                        threshold=args.threshold,
                        samples_per_chunk=args.samples_per_chunk,
                        sample_rate=vad_sample_rate,
                        keep_chunks_before=args.keep_chunks_before,
                        keep_chunks_after=args.keep_chunks_after,
                    )

                # Write as WAV
                command = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(audio_path),
                    "-f",
                    "wav",
                    "-acodec",
                    "pcm_s16le",
                    "-ss",
                    str(offset_sec),
                ]
                if duration_sec is not None:
                    command.extend(["-t", str(duration_sec)])

                command.append(str(wav_path))

                wav_path.parent.mkdir(parents=True, exist_ok=True)
                subprocess.check_call(command, stderr=subprocess.DEVNULL)

            with writer_lock:
                # id|text
                writer.writerow((wav_id, text))

            print(wav_path)
        except Exception:
            _LOGGER.exception("export_audio")


def make_silence_detector() -> SileroVoiceActivityDetector:
    silence_model = _DIR / "models" / "silero_vad.onnx"
    return SileroVoiceActivityDetector(silence_model)


if __name__ == "__main__":
    main()
