from __future__ import annotations

import argparse
import sys
import time
import vedio_util
from pathlib import Path
from typing import Literal, Optional


try:
    from pynput.mouse import Button, Controller
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "Missing dependency: pynput. Install with:\n  pip install pynput"
    ) from exc

try:
    import yaml  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "Missing dependency: PyYAML. Install with:\n  pip install pyyaml"
    ) from exc


class Action:
    TIMER_EVENT = "timer"
    MOUSE_CLICK_EVENT = "mouse_click"
    
    LEFT_BUTTON = "left"
    RIGHT_BUTTON = "right"
    MIDDLE_BUTTON = "middle"
    
    action_type : str
    event : Optional[str] 
    button : Optional[str]
    x: Optional[int]
    y: Optional[int]
    interval_sec: Optional[float]
    clicks: Optional[int]
    delay_sec: Optional[float]
    
    def __init__(self, action_type: str = "", event: Optional[str] = None, button: Optional[str] = None, 
                 x: Optional[int] = None, y: Optional[int] = None, 
                 interval_sec: Optional[float] = None, clicks: Optional[int] = None, 
                 delay_sec: Optional[float] = None):
        self.action_type = action_type
        self.event = event
        self.button = button
        self.x = x
        self.y = y
        self.interval_sec = interval_sec
        self.clicks = clicks
        self.delay_sec = delay_sec
    
    def set_position(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        
    def get_position(self) -> Optional[tuple[int, int]]:
        if self.x is not None and self.y is not None:
            return (self.x, self.y)
        return None
    


def mouse_click(
    action: Action,
) -> None:
    """
    Simulate mouse clicks.

    If x/y are provided, move to (x, y) first (screen coordinates).
    """
    if action.clicks <= 0:
        raise ValueError("clicks must be > 0")
    if action.interval_sec < 0:
        raise ValueError("interval_sec must be >= 0")

    mouse = Controller()
    if action.x is not None and action.y is not None:
        mouse.position = (int(action.x), int(action.y))

    btn = {"left": Button.left, "right": Button.right, "middle": Button.middle}[action.button]

    for i in range(action.clicks):
        mouse.click(btn, 1)
        if i != action.clicks - 1 and action.interval_sec > 0:
            time.sleep(action.interval_sec)
            
    time.sleep(action.delay_sec)
    print(f"Executed mouse click action: {action.__dict__}")
    


def track_mouse_position(*, interval_sec: float = 0.1, duration_sec: Optional[float] = None) -> None:
    """
    Continuously print mouse cursor position.

    Stop with Ctrl+C, or set duration_sec to stop automatically.
    """
    if interval_sec <= 0:
        raise ValueError("interval_sec must be > 0")
    if duration_sec is not None and duration_sec <= 0:
        raise ValueError("duration_sec must be > 0 when provided")

    mouse = Controller()
    start = time.perf_counter()
    try:
        while True:
            x, y = mouse.position
            print(f"{x},{y}")
            time.sleep(interval_sec)
            if duration_sec is not None and (time.perf_counter() - start) >= duration_sec:
                break
    except KeyboardInterrupt:
        pass


def countdown(seconds: int = 3, message: str = "Starting in") -> None:
    """
    Countdown helper: prints once per second.

    Example output:
      Starting in 3...
      Starting in 2...
      Starting in 1...
    """
    if seconds <= 0:
        return
    for remaining in range(int(seconds), 0, -1):
        print(f"{message} {remaining}...")
        time.sleep(1.0)


def progress_sleep(duration_sec: float, *, width: int = 30, update_hz: float = 2.0, label: str = "Waiting") -> None:
    """
    Sleep with a simple terminal progress bar.

    This does NOT replace time.sleep usages automatically; call it explicitly.
    """
    if duration_sec <= 0:
        return
    if width <= 0:
        raise ValueError("width must be > 0")
    if update_hz <= 0:
        raise ValueError("update_hz must be > 0")

    start = time.perf_counter()
    end = start + float(duration_sec)

    try:
        while True:
            now = time.perf_counter()
            remaining = end - now
            if remaining <= 0:
                break
            elapsed = now - start
            progress = min(1.0, max(0.0, elapsed / float(duration_sec)))
            filled = int(progress * width)
            bar = "#" * filled + "-" * (width - filled)
            sys.stdout.write(f"\r{label}: [{bar}] {progress*100:6.2f}% ({remaining:5.1f}s left)")
            sys.stdout.flush()
            time.sleep(min(update_hz, remaining))
    finally:
        bar = "#" * width
        sys.stdout.write(f"\r{label}: [{bar}] 100.00% (0.0s left)\n")
        sys.stdout.flush()


def _load_config(path: Path) -> tuple[list, list[dict]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    worklist = raw.get("worklist")
    if worklist is None:
        raise ValueError("YAML file must contain a 'worklist' key.")
    
    actions = raw.get("actions")
    if actions is None:
        raise ValueError("YAML file must contain an 'actions' key.")

    return worklist, actions


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Simulate mouse clicks from a YAML config (requires pynput).")
    p.add_argument("--track", type=bool, help="track mouse position")
    p.add_argument(
        "--config",
        type=str,
        default="mouse_clicker.yaml",
        help="Path to YAML config (default: mouse_clicker.yaml)",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    config_path = vedio_util.resolve_path(Path(args.config))
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")

    if args.track:
        print("Tracking mouse position... (Ctrl+C to stop)")
        # interval = float(action.get("interval_sec", action.get("interval", 0.1)))
        # duration = action.get("duration_sec", action.get("duration", None))
        # duration_sec = None if duration in (None, "") else float(duration)
        # print(f"Action #{idx}: tracking mouse position... (Ctrl+C to stop)")
        # track_mouse_position(interval_sec=interval, duration_sec=duration_sec)
        track_mouse_position()
        return 0
    else:
        worklist, actions = _load_config(config_path)
        # parse all actions
        action_dict = {}
        for idx, action in enumerate(actions, start=1):
            event = action.get("event")
            action_boj : Action = None
            if event == Action.TIMER_EVENT:
                action_boj = Action(
                    action_type = action.get("type"),
                    event = event,
                    delay_sec=float(action.get("delay_sec"))
                )
            elif event == Action.MOUSE_CLICK_EVENT:
                action_boj = Action(
                    action_type = action.get("type"),
                    event = event,
                    button = action.get("button"),
                    x = int(action.get("x")) if action.get("x") is not None else None,
                    y = int(action.get("y")) if action.get("y") is not None else None,
                    clicks = int(action.get("clicks", 1)),
                    interval_sec = float(action.get("interval_sec")),
                    delay_sec = float(action.get("delay_sec"))
                )
            
            action_dict[action.get("type")] = action_boj
            # print(f"Parsed Action #{idx}: {action_boj.__dict__}")
            
            
        countdown(3, "Tracking starts in")
            
        # execute actions in worklist order
        for work in worklist:
            action_obj = action_dict.get(work)
            if action_obj is None:
                print(f"Unknown work item in worklist: {work}")
                continue

            if action_obj.event == Action.TIMER_EVENT:
                delay = action_obj.delay_sec
                if delay is not None and delay > 0:
                    print(f"Action type {action_obj.action_type}: starts in {delay} seconds... (Ctrl+C to cancel)")
                    progress_sleep(delay, label=f"Action type {action_obj.action_type} {action_obj.delay_sec}s")
            elif action_obj.event == Action.MOUSE_CLICK_EVENT:
                mouse_click(action_obj)
                     
         
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
