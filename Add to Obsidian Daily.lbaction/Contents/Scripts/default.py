#!/usr/bin/env python3
#
# LaunchBar Action Script
#
import os
import shutil
import sys
import subprocess
from urllib.parse import quote

VAULT = "ObsidianVault"
VAULT_PATH = "/Users/huanbo/Library/Mobile Documents/iCloud~md~obsidian/Documents/ObsidianVault"
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


args = sys.argv[1:]

parts = []
for arg in args:
    if os.path.exists(arg):
        parts.append(import_file(arg))
    elif arg.strip():
        parts.append(arg.strip())

if not parts:
    print("Nothing to add")
    sys.exit(0)

text = "\n".join(parts)

url = (
    "obsidian://advanced-uri"
    "?vault=" + quote(VAULT)
    + "&daily=true"
    + "&mode=append"
    + "&data=" + quote("\n" + text + "\n\n---")
)

subprocess.run(["open", url])

print("Added to Obsidian Daily Note")
