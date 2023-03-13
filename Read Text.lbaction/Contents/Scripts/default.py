#!/usr/bin/env python3
#
# LaunchBar Action Script
#
import sys
import json
import mstts
import subprocess

def detect_language(text):
    command = ["swift", "./detLan.swift", text]
    output = subprocess.check_output(command)
    language = output.decode('utf-8')
    return language

def remove_excerpt(text):
    index = text.find("Excerpt From")
    if index != -1:
        return text[:index]
    else:
        return text


items = []

item = {}
item['title'] = str(len(sys.argv) - 1) + ' arguments passed'
items.append(item)

# Note: The first argument is the script's path
voice = ""
for arg in sys.argv[1:]:
    arg = remove_excerpt(arg)
    lan = detect_language(arg)
    voice = mstts.mstts(arg, lan)

command = ["osascript", "-e", "tell application \"LaunchBar\"\n display in notification center \"Read by " + voice + "\" with title \"Reading Finished\" \n end tell"]
subprocess.check_output(command)