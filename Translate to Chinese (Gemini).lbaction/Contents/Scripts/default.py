#!/usr/bin/env python3
#
# LaunchBar Action Script
#
import sys
import json
import time
import requests
import keyring

SYSTEM_PROMPT = "I want you to act as a Chinese translator. I will speak to you in any language and you will detect the language and translate it into Chinese. Use modern, natural, everyday Chinese (现代汉语口语化表达), not archaic or overly literary phrasing. Keep the meaning the same. I want you to only reply the translation and nothing else, do not write explanations."

MODEL = "gemini-2.5-flash-lite"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

RETRY_STATUS_CODES = {429, 500, 503}
MAX_RETRIES = 3

items = []

# Note: The first argument is the script's path
for arg in sys.argv[1:]:
    api_key = keyring.get_password("api_keys", "gemini")
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": arg}]}],
        "generationConfig": {"thinkingConfig": {"thinkingBudget": 0}},
    }

    try:
        for attempt in range(MAX_RETRIES):
            response = requests.post(URL, params={"key": api_key}, json=payload)
            data = response.json()
            if response.status_code == 200:
                break
            if response.status_code not in RETRY_STATUS_CODES or attempt == MAX_RETRIES - 1:
                raise Exception(data.get("error", {}).get("message", response.text))
            time.sleep(1.5 * (attempt + 1))

        string = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        item = {"title": string}
    except Exception as e:
        item = {
            "title": "Error: " + str(e),
            "icon": "font-awesome:fa-exclamation-triangle",
        }

    items.append(item)

print(json.dumps(items))
