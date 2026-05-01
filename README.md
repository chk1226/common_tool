# common tool

This folder contains small Python utilities.

## Requirements

- Python 3.x
- `ffmpeg` (not a pip package; install it separately and ensure it is on your PATH)

## `vedio_util.py` (Video Utilities)

File: `vedio_util.py`

Key features:

- **Trim video** by start/end time (supports `H:M:S` string format)
- **Combine two MP4 files** (optionally trim A/B before concatenation)
- **GPU compression (NVIDIA)** using `hevc_nvenc` (requires an ffmpeg build with NVENC support)

Common examples:

- Trim a single video (keep `--trim_start` to `--trim_end`):

```powershell
python vedio_util.py -i input.mp4 -o out.mp4 --trim_start 0:10:00 --trim_end 0:20:00
```

- Combine two videos (optionally trim A/B first; output name is customizable):

```powershell
python vedio_util.py --in_a a.mp4 --in_b b.mp4 -o combined.mp4 --a_start 0:00:00 --a_end 0:00:00 --b_start 0:10:00 --b_end 0:00:00
```

- Combine and then compress on GPU (if you have NVIDIA + NVENC-enabled ffmpeg):

```powershell
python vedio_util.py --in_a a.mp4 --in_b b.mp4 -o combined.mp4 --b_start 0:10:00 --b_end 0:00:00 --compress_gpu true
```

Notes:
- `trim_end` / `a_end` / `b_end` currently map to ffmpeg `-to` end time (on the input timeline).
- `0:0:0` means "no end time specified".
