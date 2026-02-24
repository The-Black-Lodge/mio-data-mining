#!/usr/bin/env python3
"""
Watch a MIO save file continuously and report when new keys appear or existing
keys gain the Acquired flag. Output format: [timestamp] DISPLAY_NAME Acquired
"""
import argparse
import re
import sys
import time
from datetime import datetime
from pathlib import Path

KEY_PATTERN = re.compile(r'pairs\.(\d+)\.key = String\("([^"]*)"\)')
FLAGS_PATTERN = re.compile(r'pairs\.(\d+)\.value\.flags = Flags\(([^)]+)\)')
POLL_INTERVAL = 0.5


def parse_pairs(content: str) -> dict[str, bool]:
    """
    Parse the Saved_entries pairs section and return a dict of key -> has_acquired.
    Skips empty keys.
    """
    keys: dict[int, str] = {}
    flags: dict[int, bool] = {}

    for m in KEY_PATTERN.finditer(content):
        idx, key = int(m.group(1)), m.group(2)
        keys[idx] = key

    for m in FLAGS_PATTERN.finditer(content):
        idx, flags_str = int(m.group(1)), m.group(2)
        flags[idx] = '"Acquired"' in flags_str

    result: dict[str, bool] = {}
    for idx in keys:
        if idx not in flags:
            continue
        key = keys[idx]
        if key == "":
            continue
        result[key] = flags[idx]
    return result


def display_name(key: str) -> str:
    """Convert key to display form: colon -> space."""
    return key.replace(":", " ")


def watch(save_path: Path) -> None:
    if not save_path.exists():
        print(f"Error: file not found: {save_path}", file=sys.stderr)
        sys.exit(1)

    prev: dict[str, bool] | None = None
    last_mtime: float | None = None

    print(f"Watching {save_path} — press Ctrl+C to stop", file=sys.stderr)

    try:
        while True:
            try:
                mtime = save_path.stat().st_mtime
                if mtime != last_mtime:
                    content = save_path.read_text(encoding="utf-8", errors="ignore")
                    current = parse_pairs(content)
                    last_mtime = mtime

                    if prev is not None:
                        for key, has_acquired in current.items():
                            if not has_acquired:
                                continue
                            prev_acquired = prev.get(key, False)
                            if not prev_acquired:
                                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                print(f"[{ts}] {display_name(key)} Acquired")

                    prev = current

            except (PermissionError, OSError):
                pass

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Watch a MIO save file for new acquisitions (new keys or Acquired flag)."
    )
    parser.add_argument(
        "save_file",
        type=Path,
        help="Path to the .save file (e.g. slot_0.save)",
    )
    args = parser.parse_args()
    watch(args.save_file)


if __name__ == "__main__":
    main()
