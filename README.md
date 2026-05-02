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

## `mouse_clicker.py` (Mouse Automation)

File: `mouse_clicker.py`

This script reads a YAML config and executes a simple automation workflow:

- Mouse click actions (optional x/y move first)
- Timer delays
- Track cursor position (prints `x,y` continuously)
- Optional 3-second countdown helper (prints once per second)
- Optional progress-bar sleep helper (`progress_sleep`, call explicitly in code)

Install optional dependencies:

```powershell
pip install pynput pyyaml
```

Example config (see `mouse_clicker.example.yaml`):

```yaml
worklist:
  - click1
  - wait1

actions:
  - type: click1
    event: mouse_click
    button: left
    x: 100
    y: 200
    clicks: 2
    interval_sec: 0.1
    delay_sec: 1.0
  - type: wait1
    event: timer
    delay_sec: 5
```

Run:

```powershell
python mouse_clicker.py --config mouse_clicker.yaml
```
