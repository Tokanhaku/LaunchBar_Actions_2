#!/usr/bin/env python3
#
# LaunchBar Action Script
#
import subprocess
from urllib.parse import quote

VAULT = "ObsidianVault"

url = "obsidian://advanced-uri?vault=" + quote(VAULT) + "&daily=true"

subprocess.run(["open", url])
