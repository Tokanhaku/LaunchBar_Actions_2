#!/usr/bin/python3
#
# LaunchBar Action Script
#
# Searches the *contents* of PDF files (via Spotlight's full-text index)
# and restricts results to .pdf files only.
#
import sys
import json
import subprocess as sp

MAX_RESULTS = 50

# With live feedback the script runs on every keystroke. Skip very short
# queries so we don't fire an expensive full-text search for 1 character.
MIN_LENGTH = 2

items = []


def escape(text):
    # Escape backslashes and double quotes for the Spotlight query string.
    return text.replace("\\", "\\\\").replace('"', '\\"')


# Note: The first argument is the script's path
for arg in sys.argv[1:]:
    term = arg.strip()
    if not term:
        continue

    if len(term) < MIN_LENGTH:
        items.append({
            "title": "Keep typing to search PDF contents…",
            "icon": "file-magnifying-glass-light_Template",
        })
        continue

    # kMDItemContentType == com.adobe.pdf  -> only PDF files
    # kMDItemTextContent  == "*term*"cd    -> full-text match, case/diacritic insensitive
    query = (
        'kMDItemContentType == "com.adobe.pdf" && '
        'kMDItemTextContent == "*{term}*"cd'
    ).format(term=escape(term))

    try:
        output = sp.run(
            ["mdfind", query],
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
