#!/usr/bin/env python3
import subprocess
import shlex

VAULT = "/Users/huanbo/Library/Mobile Documents/iCloud~md~obsidian/Documents/ObsidianVault"
CLAUDE = "/Users/huanbo/.local/bin/claude"

shell_cmd = f"cd {shlex.quote(VAULT)} && {shlex.quote(CLAUDE)}"

applescript = f'''tell application "Terminal"
    activate
    do script "{shell_cmd}"
end tell'''

subprocess.run(["osascript", "-e", applescript])
