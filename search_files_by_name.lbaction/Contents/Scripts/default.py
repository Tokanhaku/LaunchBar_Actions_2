#!/usr/bin/python3
#
# LaunchBar Action Script
#
import os
import sys
import json
import subprocess as sp

MAX_RESULTS = 100

# Ignore the Library folders, /Applications and other locations that hold app
# support files, caches and bundled resources — not documents the user created.
EXCLUDE_DIRS = [
    "/Library",
    "/System/Library",
    os.path.expanduser("~/Library"),
    "/Applications",
]

# ...but keep these, even though they live under an excluded dir. iCloud Drive
# (incl. Obsidian, Desktop & Documents) is stored under ~/Library/Mobile
# Documents and DOES contain the user's own documents.
INCLUDE_DIRS = [
    os.path.expanduser("~/Library/Mobile Documents"),
]

items = []


def _under(path, directory):
    return path == directory or path.startswith(directory + os.sep)


def is_excluded(path):
    # Excluded if under an EXCLUDE_DIRS entry, unless an INCLUDE_DIRS entry
    # (which takes precedence) brings it back in.
    if any(_under(path, d) for d in INCLUDE_DIRS):
        return False
    return any(_under(path, d) for d in EXCLUDE_DIRS)

# Note: The first argument is the script's path
for arg in sys.argv[1:]:
    try:
        output = sp.run(
            ["mdfind", "-name", arg],
            capture_output=True, text=True, check=True,
        ).stdout
    except sp.CalledProcessError as e:
        items.append({
            "title": "Search failed: " + e.stderr.strip(),
            "icon": "font-awesome:fa-exclamation-triangle",
        })
        continue

    files = [f for f in output.split("\n") if f and not is_excluded(f)]

    if not files:
        items.append({
            "title": "No result!",
            "icon": "symbol:exclamationmark.magnifyingglass",
        })
    else:
        for file in files[:MAX_RESULTS]:
            items.append({"path": file})

print(json.dumps(items))