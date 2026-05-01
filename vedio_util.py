
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional
from typing import Literal, Optional

FFMPEG_PATH = "ffmpeg" 
PROJECT_DIR = Path(__file__).resolve().parent

def time_str_to_seconds(time_str: str) -> float:
    """Convert a time string (e.g., "1:23:45.67") to total seconds."""
    parts = time_str.split(":")
    if len(parts) > 3:
        raise ValueError(f"Invalid time format: {time_str}")
    seconds = 0.0
    for i, part in enumerate(reversed(parts)):
        seconds += float(part) * (60 ** i)
    return seconds

def make_tmp_dir(dir : Path) -> Path:
    tmp_dir = dir / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir

def require_ffmpeg() -> None:
    try:
        subprocess.run(
            [FFMPEG_PATH, "-version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "ffmpeg not found on PATH. Install ffmpeg and ensure `ffmpeg` is available."
        ) from exc

def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (PROJECT_DIR / p)


def escape_concat_path(path: Path) -> str:
    # concat demuxer format: file '...'
    # Escape single quotes (') for ffmpeg's concat file syntax.
    return str(path).replace("'", r"'\''")


def combine_two_mp4(
    input_a: str | Path,
    input_b: str | Path,
    output_path: str | Path,
    *,
    fast_copy: bool = True,
) -> Path:
    """
    Combine two MP4 files into a single MP4.

    fast_copy=True uses stream copy (no re-encode) and requires compatible streams
    (same codec params, resolution, fps, etc). If it fails, it falls back to re-encode.
    """
    in_a = resolve_path(input_a)
    in_b = resolve_path(input_b)
    out = resolve_path(output_path)

    tmp_base = make_tmp_dir(PROJECT_DIR)
    # tmp_dir = Path(tempfile.mkdtemp(prefix="screenrec_", dir=str(tmp_base)))
    # tmp_video = tmp_dir / "combined.mp4"


    if not in_a.exists():
        raise FileNotFoundError(f"Input not found: {in_a}")
    if not in_b.exists():
        raise FileNotFoundError(f"Input not found: {in_b}")

    with tempfile.TemporaryDirectory(prefix="ffmpeg_concat_", dir=str(tmp_base)) as td:
        list_path = Path(td) / "inputs.txt"
        list_path.write_text(
            "ffconcat version 1.0\n"
            f"file '{escape_concat_path(in_a.resolve())}'\n"
            f"file '{escape_concat_path(in_b.resolve())}'\n",
            encoding="utf-8",
        )

        def run(cmd: list[str]) -> None:
            subprocess.run(cmd, check=True)

        if fast_copy:
            try:
                run(
                    [
                        FFMPEG_PATH,
                        "-y",
                        "-f",
                        "concat",
                        "-safe",
                        "0",
                        "-i",
                        str(list_path),
                        "-c",
                        "copy",
                        str(out),
                    ]
                )
                return out
            except subprocess.CalledProcessError:
                # Fall back to re-encode for mismatched streams.
                pass

        # Re-encode fallback (widest compatibility).
        run(
            [
                FFMPEG_PATH,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                str(out),
            ]
        )
        return out



def combine_two_mp4_with_offsets(
    input_a: str | Path,
    input_b: str | Path,
    output_path: str | Path,
    *,
    start_a_seconds: str | float,
    end_a_seconds: str | float,
    start_b_seconds: str | float,
    end_b_seconds: str | float,
    fast_copy: bool = True,
    trim_mode: Literal["copy", "reencode"] = "copy",
) -> Path:
    """
    Combine two MP4s after optionally trimming either input from a given offset (seconds).
    """

    in_a = resolve_path(input_a)
    in_b = resolve_path(input_b)
    out = resolve_path(output_path)

    start_a_seconds = time_str_to_seconds(start_a_seconds) if type(start_a_seconds) == str else start_a_seconds
    end_a_seconds = time_str_to_seconds(end_a_seconds) if type(end_a_seconds) == str else end_a_seconds
    start_b_seconds = time_str_to_seconds(start_b_seconds) if type(start_b_seconds) == str else start_b_seconds
    end_b_seconds = time_str_to_seconds(end_b_seconds) if type(end_b_seconds) == str else end_b_seconds

    if start_a_seconds < 0 or start_b_seconds < 0 or end_a_seconds < 0 or end_b_seconds < 0:
        raise ValueError("start_a_seconds/start_b_seconds/end_a_seconds/end_b_seconds must be >= 0")

    with tempfile.TemporaryDirectory(prefix="ffmpeg_trim_", dir=str(make_tmp_dir(PROJECT_DIR))) as td:
        td_path = Path(td)
        a_path = trim_mp4_from_seconds(in_a, start_a_seconds, end_a_seconds, td_path / "a_trim.mp4")
        b_path = trim_mp4_from_seconds(in_b, start_b_seconds, end_b_seconds, td_path / "b_trim.mp4")
        out = out.with_name("Combined_" + out.name)
        return combine_two_mp4(a_path, b_path, out, fast_copy=fast_copy)


def compress_video_gpu(input_path: str | Path, output_path: str | Path) -> Path:

    src = resolve_path(input_path)
    # print(f"Input video: {src}")
    dst = resolve_path(output_path)
    # print(f"Output video: {dst}")

    if not src.exists():
        raise FileNotFoundError(f"Input video not found: {src}")


    # with tempfile.TemporaryDirectory(prefix="ffmpeg_concat_", dir=str(make_tmp_dir(PROJECT_DIR))) as td:


    # Build ffmpeg command for compression
    cmd = [FFMPEG_PATH, "-i", str(src)]
    
    # Example for NVIDIA GPU acceleration (requires appropriate ffmpeg build)
    cmd += ["-c:v", "hevc_nvenc"]
    cmd += ["-rc", "vbr", "-qp", "28", "-preset", "p4", "-c:a", "mp3", "-b:a", "128k", str(dst)]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffmpeg failed to compress video: {exc}") from exc

    return dst


def trim_mp4_from_seconds(
    input_path: str | Path,
    start_seconds: str | float,
    end_seconds: str | float, 
    output_path: str | Path,
    *,
    mode: Literal["copy", "reencode"] = "copy",
) -> Path:
    """
    Trim an MP4 starting from `start_seconds` and write a new MP4.
    - `end_seconds`: the end time for the trim. Negative values are relative to the "end of file". That is negative values are earlier in the file, 0 is at EOF.
    - mode="copy": fast, but seek accuracy depends on keyframes (may not be frame-accurate).
    - mode="reencode": slower, but frame-accurate and more robust for later concat.
    """

    src = resolve_path(input_path)
    dst = resolve_path(output_path)


    base = [
        FFMPEG_PATH,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-avoid_negative_ts",
        "make_zero",
        "-fflags",
        "+genpts",
    ]

    if type(start_seconds) == str:
        start_seconds = time_str_to_seconds(start_seconds)
    if type(end_seconds) == str:
        end_seconds = time_str_to_seconds(end_seconds)
        
    if start_seconds < 0:
        raise ValueError("start_seconds must be >= 0 ")
    if end_seconds < 0:
        raise ValueError("end_seconds must be >= 0 ")
    if start_seconds == 0 and end_seconds == 0:
        return src
    if not src.exists():
        raise FileNotFoundError(f"Input not found: {src}")

    if start_seconds > 0:
        base += ["-ss", str(start_seconds)]
    if end_seconds > 0:
        base += ["-to", str(end_seconds)]

    dst = dst.with_name("Trimmed_" + dst.name)

    if mode == "copy":
        cmd = base + ["-c", "copy", str(dst)]
    else:
        cmd = base + [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(dst),
        ]

    subprocess.run(cmd, check=True)
    print(f"Trimmed complete! Trimmed video saved to: {dst}")
    return dst



def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Combine two MP4 files into one MP4 (ffmpeg required).")
    p.add_argument("--compress_gpu", type=bool, help="compress vedio")
    p.add_argument("-i", "--input", type=str, help="input file path")
    p.add_argument("-o", "--output", type=str, default="combined.mp4", help="Output file path")
    p.add_argument("--trim_start", type=str, default="0:0:0", help="Trim starting at N seconds (default: 0)")
    p.add_argument("--trim_end", type=str, default="0:0:0", help="Trim ending from N seconds (default: 0)")
    p.add_argument("--in_a", type=str, help="First MP4 path")
    p.add_argument("--in_b", type=str, help="Second MP4 path")
    p.add_argument("--a_start", type=str, default="0:0:0", help="Trim input_a starting at N seconds (default: 0)")
    p.add_argument("--b_start", type=str, default="0:0:0", help="Trim input_b starting at N seconds (default: 0)")
    p.add_argument("--a_end", type=str, default="0:0:0", help="Trim input_a ending at N seconds (default: 0)")
    p.add_argument("--b_end", type=str, default="0:0:0", help="Trim input_b ending at N seconds (default: 0)")

    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    require_ffmpeg()

    #not complete, just a placeholder for now
    output_file = None
    args = _parse_args(sys.argv[1:] if argv is None else argv)


    if args.in_a and args.in_b:
        output_file = combine_two_mp4_with_offsets(
            input_a=args.in_a,
            input_b=args.in_b,
            output_path=args.output,
            start_a_seconds=args.a_start,
            end_a_seconds=args.a_end,
            start_b_seconds=args.b_start,
            end_b_seconds=args.b_end,
        )
    else:
        output_file = trim_mp4_from_seconds(
            input_path=args.input,
            start_seconds=args.trim_start,
            end_seconds=args.trim_end,
            output_path=args.output,
            mode="copy",
        )
    
    if args.compress_gpu:
        if output_file is None:
            output_file = resolve_path(args.output)
        output_file = compress_video_gpu(output_file, "Compressed_" + output_file.name)
        print(f"Compressed video saved to: {output_file}")

    if output_file is None:
        print("No trimming or compression applied.")
    else:
        print(f"Saved: {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())