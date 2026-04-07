#!/usr/bin/env python3
"""Convert common video inputs to MP4 or MOV with ffmpeg.

Examples:
  python3 video_converter.py demo.webm
  python3 video_converter.py clip.webm --to mov
  python3 video_converter.py a.webm b.mkv --out-dir converted
  python3 video_converter.py recordings --recursive --to mp4
"""

from __future__ import annotations

import argparse
import glob
import shutil
import subprocess
import sys
from pathlib import Path


COMMON_VIDEO_EXTENSIONS = {
    ".avi",
    ".flv",
    ".gif",
    ".m2ts",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".mts",
    ".ogv",
    ".ts",
    ".webm",
    ".wmv",
}

SUPPORTED_OUTPUT_FORMATS = {"mp4", "mov"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert one or more video files to MP4 or MOV with ffmpeg."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input files, directories, or glob patterns.",
    )
    parser.add_argument(
        "--to",
        choices=sorted(SUPPORTED_OUTPUT_FORMATS),
        default="mp4",
        help="Output container format. Default: mp4",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Explicit output file path. Only valid for a single input file.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="Output directory for batch conversions.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan directory inputs for common video formats.",
    )
    parser.add_argument(
        "--video-codec",
        default="libx264",
        help="ffmpeg video codec. Default: libx264",
    )
    parser.add_argument(
        "--audio-codec",
        default="aac",
        help="ffmpeg audio codec. Use 'copy' to keep audio as-is. Default: aac",
    )
    parser.add_argument(
        "--audio-bitrate",
        default="192k",
        help="Audio bitrate when re-encoding audio. Default: 192k",
    )
    parser.add_argument(
        "--preset",
        default="medium",
        help="ffmpeg preset for video encoding. Default: medium",
    )
    parser.add_argument(
        "--crf",
        type=int,
        default=23,
        help="CRF value for video encoding. Lower means better quality. Default: 23",
    )
    parser.add_argument(
        "--fps",
        type=float,
        help="Optional output FPS override.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print ffmpeg commands without running them.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show the full ffmpeg command for each conversion.",
    )
    return parser


def ensure_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "ffmpeg was not found in PATH. Install ffmpeg first; no pip package is required."
        )
    return ffmpeg


def expand_inputs(raw_inputs: list[str], recursive: bool) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()

    for raw in raw_inputs:
        matches = [Path(p) for p in glob.glob(raw)] if any(ch in raw for ch in "*?[]") else [Path(raw)]
        if not matches:
            raise FileNotFoundError(f"No input matched: {raw}")

        for match in matches:
            if match.is_dir():
                iterator = match.rglob("*") if recursive else match.glob("*")
                for child in iterator:
                    if child.is_file() and child.suffix.lower() in COMMON_VIDEO_EXTENSIONS:
                        resolved = child.resolve()
                        if resolved not in seen:
                            seen.add(resolved)
                            paths.append(resolved)
            elif match.is_file():
                resolved = match.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    paths.append(resolved)
            else:
                raise FileNotFoundError(f"Input does not exist: {match}")

    if not paths:
        raise FileNotFoundError("No input video files were found.")
    return paths


def resolve_output_path(
    input_path: Path,
    args: argparse.Namespace,
    batch_mode: bool,
) -> Path:
    output_suffix = f".{args.to}"

    if args.output is not None:
        if batch_mode:
            raise ValueError("--output can only be used with a single input file.")
        output_path = args.output.expanduser()
        if output_path.suffix.lower() not in {".mp4", ".mov"}:
            output_path = output_path.with_suffix(output_suffix)
    else:
        parent = args.out_dir.expanduser() if args.out_dir else input_path.parent
        output_path = parent / f"{input_path.stem}{output_suffix}"

    if output_path.resolve() == input_path.resolve():
        output_path = output_path.with_name(f"{input_path.stem}_converted{output_suffix}")

    return output_path


def build_ffmpeg_command(
    ffmpeg: str,
    input_path: Path,
    output_path: Path,
    args: argparse.Namespace,
) -> list[str]:
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if args.overwrite else "-n",
        "-i",
        str(input_path),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        args.video_codec,
        "-preset",
        args.preset,
        "-crf",
        str(args.crf),
        "-pix_fmt",
        "yuv420p",
    ]

    if args.fps is not None:
        command.extend(["-r", str(args.fps)])

    if args.audio_codec.lower() == "copy":
        command.extend(["-c:a", "copy"])
    else:
        command.extend(["-c:a", args.audio_codec, "-b:a", args.audio_bitrate])

    if args.to == "mp4":
        command.extend(["-movflags", "+faststart"])

    command.append(str(output_path))
    return command


def convert_one(
    ffmpeg: str,
    input_path: Path,
    output_path: Path,
    args: argparse.Namespace,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = build_ffmpeg_command(ffmpeg, input_path, output_path, args)

    if args.verbose or args.dry_run:
        print(" ".join(command))

    if args.dry_run:
        return

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffmpeg failed for {input_path}") from exc


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        ffmpeg = ensure_ffmpeg()
        inputs = expand_inputs(args.inputs, args.recursive)
        batch_mode = len(inputs) > 1

        for input_path in inputs:
            output_path = resolve_output_path(input_path, args, batch_mode)
            convert_one(ffmpeg, input_path, output_path, args)
            if not args.dry_run:
                print(f"Converted: {input_path} -> {output_path}")
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
