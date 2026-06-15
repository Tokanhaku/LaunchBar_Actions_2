#!/usr/bin/python3
#
# LaunchBar Action Script
#
import sys
import json
import subprocess as sp

MAX_RESULTS = 50

items = []

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

    files = [f for f in output.split("\n") if f]

    if not files:
        items.append({
            "title": "No result!",
            "icon": "grin-beam-sweat-Template",
        })
    else:
        for file in files[:MAX_RESULTS]:
            items.append({"path": file})

print(json.dumps(items))