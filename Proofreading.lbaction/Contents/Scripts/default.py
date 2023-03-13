#!/usr/bin/env python3
#
# LaunchBar Action Script
#
import sys
import json
import openai
import subprocess
import keyring

def detect_language(text):
    command = ["swift", "./detLan.swift", text]
    output = subprocess.check_output(command)
    language = output.decode('utf-8')
    return language

def write_to_clipboard(output):
    process = subprocess.Popen(
        'pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(output.encode('utf-8'))

# items = []

# Note: The first argument is the script's path
for arg in sys.argv[1:]:
    lan = detect_language(arg)
    if lan.startswith('zh'):
        msg = [
        {"role": "system", "content": "你是我的写作助手，检查接收到的文字的拼写、语法错误，对其进行润色，向我提供修改后的文字。"},
        {"role": "user", "content": "修改和润色下面的文字，直接输出修改后的结果，不需要额外的声明:\n" + arg}
        ]
    elif lan.startswith('en'):
        msg = [
        {"role": "system", "content": "I want you act as a proofreader. I will provide you texts and I would like you to review them for any spelling, grammar, or punctuation errors. Once you have finished reviewing the text, provide me with the improved text, and do not include extra declarations or comments."},
        {"role": "user", "content": arg},
        ]
    elif lan.startswith('de'):
        msg = [
        {"role": "system", "content": "Ich möchte Sie als Korrekturleser einsetzen. Ich werde Ihnen Texte zur Verfügung stellen, die Sie auf Rechtschreib-, Grammatik- und Zeichensetzungsfehler überprüfen sollen. Sobald Sie die Überprüfung des Textes abgeschlossen haben, übermitteln Sie mir den verbesserten Text, ohne zusätzliche Erklärungen oder Kommentare einzufügen."},
        {"role": "user", "content": arg},
        ]
    else:
        continue

    openai.api_key = keyring.get_password("api_keys", "gpt")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=msg,)

    string = response["choices"][0]["message"]["content"]
    write_to_clipboard(string)
    command = ["osascript", "-e", "tell application \"LaunchBar\"\n display in notification center \"" + string + "\" with title \"Proofreading Result Copied\" \n end tell"]
    subprocess.check_output(command)

#    item = {}
#    item['title'] = string
#    items.append(item)

# print(json.dumps(items))
