#!/usr/bin/python3

import json
import os
import shutil
import subprocess
import sys


def find_ffmpeg():
    for candidate in (
        "/opt/homebrew/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        shutil.which("ffmpeg"),
    ):
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def error_item(title, subtitle=None):
    item = {
        "title": title,
        "icon": "symbol:exclamationmark.triangle",
    }
    if subtitle:
        item["subtitle"] = subtitle
    return item


ffmpeg = find_ffmpeg()
if not ffmpeg:
    print(json.dumps([
        error_item(
            "FFmpeg is not installed",
            "Install it with: brew install ffmpeg",
        )
    ]))
    sys.exit(0)

inputs = [
    path for path in sys.argv[1:]
    if os.path.isfile(path) and path.lower().endswith(".mts")
]

if not inputs:
    print(json.dumps([
        error_item("No MTS file selected")
    ]))
    sys.exit(0)

items = []

for input_path in inputs:
    output_path = os.path.splitext(input_path)[0] + ".mp4"

    if os.path.exists(output_path):
        items.append({
            "path": output_path,
            "subtitle": "Output already exists; conversion was skipped",
        })
        continue

    command = [
        ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-i", input_path,
        "-map", "0:v:0",
        "-map", "0:a:0?",
        "-map_metadata", "0",
        "-c:v", "libx265",
        "-preset", "medium",
        "-crf", "20",
        "-tag:v", "hvc1",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        "-avoid_negative_ts", "make_zero",
        output_path,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0 and os.path.isfile(output_path):
        items.append({
            "path": output_path,
            "subtitle": "HEVC MP4 created for Photos.app",
        })
    else:
        details = result.stderr.strip().splitlines()
        items.append(error_item(
            "Conversion failed: " + os.path.basename(input_path),
            details[-1] if details else "FFmpeg returned an unknown error",
        ))

print(json.dumps(items))
