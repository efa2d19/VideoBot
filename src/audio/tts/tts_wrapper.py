from aiohttp import ClientSession
import base64
from os import getenv

from src.audio.tts.profane_filter import profane_filter
from src.audio.tts.ValidVoices import voice_list


async def tts(  # TODO test it, failed once, wrote blank file
        client: 'ClientSession',
        req_text: str,
        filename: str | int,
        voice: str = 'en_us_002',  # List of valid voices in ValidVoices.py
):
    env_voice = getenv('tts_voice')
    if env_voice and env_voice in voice_list:
        voice = env_voice

    uri_base = 'https://api16-normal-useast5.us.tiktokv.com/media/api/text/speech/invoke/'
    req_text = profane_filter(req_text)
    output_text = ''

    def text_len_sanitize(
            text: str,
            max_length: int,
    ) -> list:
        if '.' in text and all([split_text.__len__() < max_length for split_text in text.split('.')]):
            return text.split(',')

        if ',' in text and all([split_text.__len__() < max_length for split_text in text.split(',')]):
            return text.split(',')

        return [text[i:i + max_length] for i in range(0, len(text), max_length)]

    # use multiple api requests to make the sentence
    if len(req_text) > 299:
        # Split by comma or dot (else you can lose intonations), if there is non, split by groups of 299 chars
        for part in text_len_sanitize(req_text, 299):
            async with client.post(
                    url=uri_base,
                    params={
                        'text_speaker': voice,
                        'req_text': part,
                        'speaker_map_type': 0,
                    }) as result:
                response = await result.json()
                output_text += [response.get('data').get('v_str')][0]
        decoded_text = base64.b64decode(output_text)
        with open(f'assets/audio/{filename}.mp3', 'wb') as out:
            out.write(decoded_text)
        return

    # if under 299 characters do it in one
    async with client.post(
            url=uri_base,
            params={
                'text_speaker': voice,
                'req_text': req_text,
                'speaker_map_type': 0,
            }) as result:
        response = await result.json()
        output_text = [response.get('data').get('v_str')][0]
    decoded_text = base64.b64decode(output_text)
    with open(f'assets/audio/{filename}.mp3', 'wb') as out:
        out.write(decoded_text)
