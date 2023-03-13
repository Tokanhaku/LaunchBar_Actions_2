#!/usr/bin/env python3
#
# LaunchBar Action Script
#
import sys
import json
import requests
import keyring
def deepl_translate(text, target):
    # Set the URL for the API endpoint
    url = 'https://api-free.deepl.com/v2/translate'

    # Set the parameters for the request
    params = {
        'auth_key': keyring.get_password("api_keys", "deepl"),
        'text': text,
        'target_lang': target
    }

    # Send the request
    response = requests.post(url, data=params)
    return json.loads(response.text)


items = []
languages = ["ZH"]
# Note: The first argument is the script's path
for arg in sys.argv[1:]:
    for language in languages:
        item = {}
        try:
            content = deepl_translate(arg, language)['translations'][0]
            item["title"] = content['text']
            item["subtitle"] = content["detected_source_language"]\
                               + ": " + arg
            item["icon"] = "zhong_Template.png"
        except:
            item = {}
            item["title"] = "Error!"
            item["icon"] = "font-awesome:fa-exclamation-triangle"
        items.append(item)
print(json.dumps(items))