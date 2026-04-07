# video_converter

Simple command-line video conversion with `ffmpeg`.

This repo provides a single Python script, [`video_converter.py`](./video_converter.py), for converting common input video formats to `mp4` or `mov`.

It is intended to be lightweight:
- Python standard library only
- no `pip install` required
- uses system `ffmpeg`

## Requirements

- Python 3.10 or newer
- `ffmpeg` available in `PATH`

Check them with:

```bash
python3 --version
ffmpeg -version
```

## Install ffmpeg

Ubuntu / Debian:

```bash
sudo apt update
sudo apt install ffmpeg
```

macOS with Homebrew:

```bash
brew install ffmpeg
```

## Repo Layout

```bash
video_converter/
├── assets/
│   ├── .gitignore
│   ├── <video_files>
├── README.md
└── video_converter.py
```

The `assets/` folder can be used for sample inputs and converted outputs.

## Usage

Run the script directly:

```bash
python3 video_converter.py INPUT
```

Or:

```bash
./video_converter.py INPUT
```

Default behavior:
- output format is `mp4`
- output file is written next to the input
- video codec is `libx264`
- audio codec is `aac`
- odd video dimensions are padded to even dimensions by default for encoder compatibility

## Examples

Convert a single WebM to MP4:

```bash
python3 video_converter.py demo.webm
```

Convert a single file to MOV:

```bash
python3 video_converter.py demo.webm --to mov
```

Convert multiple files into a target directory:

```bash
python3 video_converter.py a.webm b.mkv c.mov --out-dir converted
```

Convert every supported video inside a directory:

```bash
python3 video_converter.py recordings --recursive --out-dir converted
```

Write to a specific output file:

```bash
python3 video_converter.py input.webm --output final_clip.mp4
```

Preview the generated `ffmpeg` command without running it:

```bash
python3 video_converter.py input.webm --dry-run --verbose
```

Overwrite existing output files:

```bash
python3 video_converter.py input.webm --overwrite
```

Change encoding settings:

```bash
python3 video_converter.py input.webm --crf 18 --preset slow --audio-bitrate 256k
```

Keep the original audio stream when possible:

```bash
python3 video_converter.py input.webm --audio-codec copy
```

## Supported Input Formats

The script scans these common extensions:

```text
.avi .flv .gif .m2ts .m4v .mkv .mov .mp4 .mpeg .mpg .mts .ogv .ts .webm .wmv
```

Supported output formats:

```text
mp4
mov
```

## CLI Options

```bash
python3 video_converter.py --help
```

Main options:
- `--to {mp4,mov}`: choose output container
- `--output`: explicit output path for a single input
- `--out-dir`: output directory for batch conversion
- `--recursive`: recursively scan directory inputs
- `--video-codec`: ffmpeg video codec, default `libx264`
- `--audio-codec`: ffmpeg audio codec, default `aac`
- `--audio-bitrate`: audio bitrate when re-encoding, default `192k`
- `--preset`: ffmpeg preset, default `medium`
- `--crf`: video quality, default `23`
- `--fps`: force output FPS
- `--even-dimensions {pad,scale,none}`: how to handle odd frame sizes, default `pad`
- `--overwrite`: overwrite existing files
- `--dry-run`: print commands only
- `--verbose`: print full ffmpeg command

## Notes

- No third-party Python modules are used.
- If `ffmpeg` is missing, the script exits with a clear error.
- If the output path would overwrite the input path, the script writes `<name>_converted.<ext>` instead.
- The converter writes to a temporary file first, then renames it on success so failed runs do not leave a broken output behind.
- For MP4 output, `+faststart` is enabled so files are more stream-friendly.

## Contact

- **Author**: Wei-Hsuan Cheng [(johnathancheng0125@gmail.com)](mailto:johnathancheng0125@gmail.com)
- **Homepage**: [wei-hsuan-cheng](https://wei-hsuan-cheng.github.io)
- **GitHub**: [wei-hsuan-cheng](https://github.com/wei-hsuan-cheng)
