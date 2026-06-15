# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import azure.cognitiveservices.speech as speechsdk
import random
import keyring

def mstts(text, lan):

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

    voice = voice_list[0]
    print(voice)



    # Creates an instance of a speech config with specified subscription key and service region.
    # Replace with your own subscription key and service region (e.g., "westus").
    api_key = keyring.get_password("api_keys", "azure_tts")
    service_region = keyring.get_password("api_keys", "azure_region")
    speech_config = speechsdk.SpeechConfig(subscription=api_key, region=service_region)
    #speech_config.speech_synthesis_voice_name = voice

    """performs speech synthesis to a mp3 file"""
    # Creates an instance of a speech config with specified subscription key and service r
    # Sets the synthesis output format.
    # The full list of supported format can be found here:
    # https://docs.microsoft.com/azure/cognitive-services/speech-service/rest-text-to-speech#audio-outputs
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
    # Creates a speech synthesizer using file as audio output.
    # Replace with your own audio file name.
    file_name = "outputaudio.mp3"
    file_config = speechsdk.audio.AudioOutputConfig(filename=file_name)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=file_config)

    ssml_string = open("ssml.xml", "r").read()
    result = speech_synthesizer.speak_ssml_async(ssml_string).get()

    #result = speech_synthesizer.speak_text_async(text).get()
    print(result.reason)
    # Receives a text from console input and synthesizes it to mp3 file.
    #while True:
    #    print("Enter some text that you want to synthesize, Ctrl-Z to exit")
    #    try:
    #        text = input()
    #    except EOFError:
    #        break
    #    result = speech_synthesizer.speak_text_async(text).get()
    #    # Check result
    #    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    #        print("Speech synthesized for text [{}], and the audio was saved to [{}]".format(text, file_name))
    #    elif result.reason == speechsdk.ResultReason.Canceled:
    #        cancellation_details = result.cancellation_details
    #        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
    #        if cancellation_details.reason == speechsdk.CancellationReason.Error:
    #            print("Error details: {}".format(cancellation_details.error_details))