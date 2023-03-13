# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import azure.cognitiveservices.speech as speechsdk
import random
import keyring

def mstts(text, lan):
    # Creates an instance of a speech config with specified subscription key and service region.
    # Replace with your own subscription key and service region (e.g., "westus").
    api_key = keyring.get_password("api_keys", "azure_tts")
    service_region = keyring.get_password("api_keys", "azure_region")
    speech_config = speechsdk.SpeechConfig(subscription=api_key, region=service_region)
    
    # Set the voice name, refer to https://aka.ms/speech/voices/neural for full list.
    voice_list_zh = ["zh-CN-XiaochenNeural", "zh-CN-XiaohanNeural", "zh-CN-XiaomengNeural", "zh-CN-XiaomoNeural", "zh-CN-XiaoqiuNeural", "zh-CN-XiaoshuangNeural", "zh-CN-XiaoxiaoNeural", "zh-CN-XiaoxuanNeural", "zh-CN-XiaoyanNeural", "zh-CN-XiaoyiNeural", "zh-CN-XiaoyouNeural", "zh-CN-XiaozhenNeural", "zh-CN-YunfengNeural", "zh-CN-YunhaoNeural", "zh-CN-YunjianNeural", "zh-CN-YunxiaNeural", "zh-CN-YunxiNeural", "zh-CN-YunyangNeural", "zh-CN-YunyeNeural", "zh-CN-YunzeNeural"]
    voice_list_de = ["de-DE-AmalaNeural", "de-DE-BerndNeural", "de-DE-ChristophNeural", "de-DE-ConradNeural", "de-DE-ElkeNeural", "de-DE-GiselaNeural", "de-DE-KasperNeural", "de-DE-KatjaNeural", "de-DE-KillianNeural", "de-DE-KlarissaNeural", "de-DE-KlausNeural", "de-DE-LouisaNeural", "de-DE-MajaNeural", "de-DE-RalfNeural", "de-DE-TanjaNeural"]
    voice_list_en = ["en-GB-AbbiNeural",  "en-GB-AlfieNeural",  "en-GB-BellaNeural",  "en-GB-ElliotNeural",  "en-GB-EthanNeural",  "en-GB-HollieNeural",  "en-GB-LibbyNeural",  "en-GB-MaisieNeural",  "en-GB-NoahNeural",  "en-GB-OliverNeural",  "en-GB-OliviaNeural",  "en-GB-RyanNeural",  "en-GB-SoniaNeural",  "en-GB-ThomasNeural"] 
    print("language: " + lan)
    if lan.startswith('zh'):
        voice_list = voice_list_zh
    elif lan.startswith('en'):
        voice_list = voice_list_en
    elif lan.startswith('de'):
        voice_list = voice_list_de
    else:
        voice_list = voice_list_en
    print(voice_list)

    voice = random.choice(voice_list)
    print(voice)

    speech_config.speech_synthesis_voice_name = voice
    
    # Creates a speech synthesizer using the default speaker as audio output.
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    
    # Synthesizes the received text to speech.
    # The synthesized speech is expected to be heard on the speaker with this line executed.
    result = speech_synthesizer.speak_text_async(text).get()
    
    # Checks result.
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized to speaker for text [{}]".format(text))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
        print("Did you update the subscription info?")
    return voice
    # </code>

