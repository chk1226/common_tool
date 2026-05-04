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

This script reads a YAML config and executes a simple automation workflow.

Key features:

- Mouse click actions, with optional direct `x` / `y` coordinates
- Timer actions in a `worklist`
- Image matching inside a screen region before clicking
- Cursor tracking mode (prints `x,y` continuously)
- Countdown helper
- Progress-bar sleep for timed waits

Install optional dependencies:

```powershell
pip install pynput pyyaml opencv-python mss numpy
```

YAML structure:

- `worklist`: the execution order
- `actions`: the action definitions referenced by `worklist`

Supported action types:

- `event: timer`
- `event: mouse_click`

Example config:

```yaml
worklist:
  - click1
  - wait1
  - click_by_image

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
  - type: click_by_image
    event: mouse_click
    button: left
    clicks: 1
    interval_sec: 0.1
    delay_sec: 0.5
    match_image_path: target.png
    region_x: 0
    region_y: 0
    region_width: 1920
    region_height: 1080
```

Run:

```powershell
python mouse_clicker.py --config mouse_clicker.yaml
```

Track the current mouse position:

```powershell
python mouse_clicker.py --track true --config mouse_clicker.yaml
```

Notes:

- If `match_image_path` is provided, the script searches that image inside the given region and uses the matched position as the click target.
- If the image is not found above the threshold, that click action is skipped.
- Timer actions currently use the terminal progress bar helper during the wait.
