#!/usr/bin/python3
#
# LaunchBar Action Script
#
# Searches the *text content* of documents and images (images via Spotlight's
# OCR / Live Text index). It only matches text that Spotlight has extracted
# (kMDItemTextContent), so binary file contents are never searched.
#
import os
import sys
import json
import subprocess as sp

MAX_RESULTS = 100
MIN_LENGTH = 2

# Ignore the Library folders entirely: they hold app support files, caches
# and other system data — not documents the user created.
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


def escape(text):
    # Escape backslashes and double quotes for the Spotlight query string.
    return text.replace("\\", "\\\\").replace('"', '\\"')


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
