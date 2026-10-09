#!/usr/bin/env python3
"""ffsummary — one-line media file summaries, batch-friendly.

Wraps ffprobe and prints the stuff you actually want at a glance:
duration, resolution, codecs, frame rate, bitrate, size.

    ffsummary.py video.mp4
    ffsummary.py *.mkv

Requires ffprobe on PATH. No other dependencies.
"""
import json
import subprocess
import sys
from pathlib import Path

VID_KEYS = ("codec_name", "width", "height", "avg_frame_rate")


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return None


def fps(rate):
    if not rate or rate == "0/0":
        return 0.0
    num, _, den = rate.partition("/")
    try:
        return round(int(num) / max(int(den), 1), 3)
    except (ValueError, ZeroDivisionError):
        return 0.0


def fmt_duration(sec):
    sec = int(float(sec or 0))
    h, sec = divmod(sec, 3600)
    m, s = divmod(sec, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def fmt_size(n):
    n = float(n or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024


def summarize(path):
    data = probe(path)
    if not data:
        return f"{path}  UNREADABLE"
    fmt = data.get("format", {})
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
    parts = [str(path), fmt_duration(fmt.get("duration"))]
    if video:
        parts.append(f"{video.get('width', '?')}x{video.get('height', '?')}")
        parts.append(f"{video.get('codec_name', '?')} {fps(video.get('avg_frame_rate'))}fps")
    if audio:
        ch = audio.get("channels", "?")
        parts.append(f"{audio.get('codec_name', '?')} {audio.get('sample_rate', '?')}Hz/{ch}ch")
    br = int(fmt.get("bit_rate") or 0)
    if br:
        parts.append(f"{br / 1e6:.2f} Mb/s")
    parts.append(fmt_size(fmt.get("size")))
    return "  ".join(parts)


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    rc = 0
    for arg in argv[1:]:
        if not Path(arg).is_file():
            print(f"{arg}  NOT A FILE")
            rc = 1
            continue
        print(summarize(arg))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
