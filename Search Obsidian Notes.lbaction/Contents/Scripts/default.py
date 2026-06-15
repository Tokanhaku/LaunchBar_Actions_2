#!/usr/bin/env python3
#
# LaunchBar Action Script
#
import sys
import os
import json
import subprocess
from urllib.parse import quote

VAULT = "ObsidianVault"
VAULT_PATH = "/Users/huanbo/Library/Mobile Documents/iCloud~md~obsidian/Documents/ObsidianVault"
MAX_RESULTS = 30

query = " ".join(sys.argv[1:]).strip()

items = []
seen = set()


def add_item(rel_path):
    if rel_path in seen:
        return
    seen.add(rel_path)
    note_path = rel_path[:-3]  # strip ".md"
    url = "obsidian://open?vault=" + quote(VAULT) + "&file=" + quote(note_path)
    items.append({
        "title": os.path.basename(note_path),
        "subtitle": rel_path,
        "url": url,
        "icon": "obsidian_icon.png",
    })


if query:
    # 1. filename matches first
    for root, dirs, files in os.walk(VAULT_PATH):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if f.lower().endswith(".md") and query.lower() in f.lower():
                rel = os.path.relpath(os.path.join(root, f), VAULT_PATH)
                add_item(rel)

    # 2. content matches
    if len(items) < MAX_RESULTS:
        result = subprocess.run(
            ["grep", "-rliIF", "--include=*.md", query, VAULT_PATH],
            capture_output=True, text=True,
        )
        for line in result.stdout.splitlines():
            rel = os.path.relpath(line, VAULT_PATH)
            add_item(rel)
            if len(items) >= MAX_RESULTS:
                break

if not items:
    items.append({
        "title": "No result!",
        "icon": "grin-beam-sweat-Template",
    })

print(json.dumps(items[:MAX_RESULTS]))
