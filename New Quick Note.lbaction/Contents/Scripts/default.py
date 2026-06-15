#!/usr/bin/env python3
#
# LaunchBar Action Script
#
import os
import shutil
import sys
import subprocess
import datetime
from urllib.parse import quote

VAULT = "ObsidianVault"
VAULT_PATH = "/Users/huanbo/Library/Mobile Documents/iCloud~md~obsidian/Documents/ObsidianVault"
FOLDER = "Notes/Inbox"
ATTACHMENTS_DIR = "Attachments"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp", ".heic"}


def unique_destination(folder, filename):
    name, ext = os.path.splitext(filename)
    dest = os.path.join(folder, filename)
    counter = 1
    while os.path.exists(dest):
        dest = os.path.join(folder, f"{name} ({counter}){ext}")
        counter += 1
    return dest


def import_file(path):
    folder = os.path.join(VAULT_PATH, ATTACHMENTS_DIR)
    os.makedirs(folder, exist_ok=True)
    dest = unique_destination(folder, os.path.basename(path))
    shutil.copy2(path, dest)
    name = os.path.basename(dest)
    ext = os.path.splitext(name)[1].lower()
    if ext in IMAGE_EXTS:
        return f"![[{name}]]"
    return f"[[{name}]]"


def clipboard_image_to_file():
    """Extract an image currently on the clipboard (e.g. selected from
    LaunchBar's Clipboard History) and save it as a temp PNG file."""
    tmp_path = "/tmp/launchbar_clipboard_image.png"
    script = (
        'set pngData to the clipboard as «class PNGf»\n'
        f'set theFile to open for access POSIX file "{tmp_path}" with write permission\n'
        'set eof of theFile to 0\n'
        'write pngData to theFile\n'
        'close access theFile\n'
    )
    result = subprocess.run(["osascript", "-e", script], capture_output=True)
    if result.returncode != 0 or not os.path.exists(tmp_path):
        return None
    return tmp_path


args = sys.argv[1:]

parts = []
for arg in args:
    if os.path.exists(arg):
        parts.append(import_file(arg))
    elif arg == "Image":
        tmp_path = clipboard_image_to_file()
        if tmp_path:
            parts.append(import_file(tmp_path))
            os.remove(tmp_path)
    elif arg.strip():
        parts.append(arg.strip())

content = "\n".join(parts)

timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S")
filepath = f"{FOLDER}/{timestamp} Quick Note.md"

url = (
    "obsidian://advanced-uri"
    "?vault=" + quote(VAULT)
    + "&filepath=" + quote(filepath)
    + "&mode=new"
)
if content:
    url += "&data=" + quote(content)

subprocess.run(["open", url])
