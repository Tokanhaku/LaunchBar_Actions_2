#!/usr/bin/python3
import sys
import subprocess

subprocess.run(["/opt/homebrew/bin/tag", "--add", "Red"] + sys.argv[1:], check=True)
