#!/usr/bin/python3
#
# LaunchBar Action Script
#
# Searches the *text content* of documents and images (images via Spotlight's
# OCR / Live Text index). It only matches text that Spotlight has extracted
# (kMDItemTextContent), so binary file contents are never searched.
#
import sys
import json
import subprocess as sp

MAX_RESULTS = 50
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
            "title": "Type at least %d characters…" % MIN_LENGTH,
            "icon": "file-magnifying-glass-light_Template",
        })
        continue

    # kMDItemTextContent -> Spotlight's extracted text index (never binary).
    # Restrict to documents (public.content) and images (public.image);
    # images match on OCR / Live Text that Spotlight has indexed.
    query = (
        'kMDItemTextContent == "*{term}*"cd && '
        '(kMDItemContentTypeTree == "public.content" || '
        'kMDItemContentTypeTree == "public.image")'
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
