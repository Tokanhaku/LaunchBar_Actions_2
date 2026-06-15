#!/usr/bin/env python3
#
# LaunchBar Action Script
#
import sys
import os
import re
import json
import time
import subprocess
import requests
import keyring
from urllib.parse import quote

VAULT = "ObsidianVault"
VAULT_PATH = "/Users/huanbo/Library/Mobile Documents/iCloud~md~obsidian/Documents/ObsidianVault"
BASE_FOLDER = "Notes/Knowledge/Languages"

LANGUAGE_FOLDERS = {
    "英语": "English",
    "德语": "Deutsch",
    "意大利语": "Italiano",
}

MODEL = "gemini-2.5-flash-lite"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

RETRY_STATUS_CODES = {429, 500, 503}
MAX_RETRIES = 3

SYSTEM_PROMPT = """你是一名外语教师，帮助一名中文母语者学习英语、德语和意大利语。

给定一段输入文本（英语、德语或意大利语），请先判断它属于：
- "词"：单个单词
- "词组"：固定搭配、短语、惯用语（多个词但不构成完整句子）
- "句子"：一个完整的句子

然后判断这段文本所属的语言，只能是 "英语"、"德语" 或 "意大利语" 三者之一。

接着根据类型撰写中文 Obsidian 笔记正文（Markdown 格式）：

如果是"词"：
- 词性和基本含义
- 主要用法和常见搭配
- 变格/变位表格（名词的格与复数、动词的时态与人称变位、形容词的变格等，视词性和语言而定）
- 复数形式（如适用）
- 至少 4 个常用例句，每句附中文翻译

如果是"词组"：
- 含义和中文翻译
- 用法说明（在什么场合/语境下使用，固定搭配、词形变化注意事项等）
- 至少 4 个常用例句，每句附中文翻译

如果是"句子"：
- 整句的中文翻译
- 挑出其中超出 A1/A2/B1 水平的重点/难点单词和词组，逐个讲解含义和用法（必要时给出 1 个补充例句）。A1/A2/B1 范围内的常见基础词汇（如 gestern、Film、sehen 等日常高频词）不需要讲解。如果整句都是基础词汇，可以说明这是一句基础句子，不再逐词讲解。

另外给出：
- headword：笔记标题。"词"用词典形式（德语名词带冠词，动词给不定式）；"词组"用该短语本身；"句子"用该句子（如果很长可适当截短，保留关键部分）。
- word_for_filename：适合用作文件名的简短文本，不含 / \\ : * ? " < > | 等特殊符号。"词"和"词组"用其本身；"句子"用能概括句子大意的几个词。

请使用简洁清晰的 Markdown（标题、表格、列表），风格类似语法笔记。不要用代码块包裹整篇内容，不要输出多余说明。

最终以 JSON 格式输出，包含字段：type, language, headword, word_for_filename, content。只输出 JSON 本身。"""


def sanitize_filename(name):
    name = re.sub(r'[\\/:*?"<>|]', "-", name)
    name = name.strip()
    return name[:80] if len(name) > 80 else name


text = sys.argv[1].strip()

if not text:
    print("没有收到内容")
    sys.exit(0)

api_key = keyring.get_password("api_keys", "gemini")

payload = {
    "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
    "contents": [{"parts": [{"text": text}]}],
    "generationConfig": {
        "responseMimeType": "application/json",
        "responseSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["词", "词组", "句子"]},
                "language": {"type": "string", "enum": ["英语", "德语", "意大利语"]},
                "headword": {"type": "string"},
                "word_for_filename": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["type", "language", "headword", "word_for_filename", "content"],
        },
    },
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

    response_text = data["candidates"][0]["content"]["parts"][0]["text"]
    result = json.loads(response_text)
except Exception as e:
    print("Error: " + str(e))
    sys.exit(0)

entry_type = result["type"]
language = result["language"]
headword = result["headword"]
filename_word = sanitize_filename(result["word_for_filename"])
content = result["content"]

folder = f"{BASE_FOLDER}/{LANGUAGE_FOLDERS[language]}"
filename = filename_word

content = f"> {text}\n\n{content}"

os.makedirs(os.path.join(VAULT_PATH, folder), exist_ok=True)

filepath = f"{folder}/{filename}.md"

url = (
    "obsidian://advanced-uri"
    "?vault=" + quote(VAULT)
    + "&filepath=" + quote(filepath)
    + "&data=" + quote(content)
    + "&mode=overwrite"
)

subprocess.run(["open", url])

print(f"已创建笔记（{entry_type}/{language}）：{headword}")
