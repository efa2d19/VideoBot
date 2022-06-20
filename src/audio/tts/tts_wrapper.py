from aiohttp import ClientSession
from aiofiles import open

import base64

from os import getenv
from re import sub

from src.audio.tts.ValidVoices import voice_list


class TikTokTTS:
    uri_base = 'https://api16-normal-useast5.us.tiktokv.com/media/api/text/speech/invoke/'

    def __init__(
            self,
            client: 'ClientSession',
            voice: str = 'en_us_002',  # List of valid voices in ValidVoices.py
    ):
        self.client = client
        env_voice = getenv('tts_voice')
        if env_voice and env_voice in voice_list:
            self.voice = env_voice
        else:
            self.voice = voice

    @staticmethod
    def text_sanitize(
            text: str,
    ) -> str:
        # Removes newlines
        text = sub(r'\n', '', text)
        # Replace hyperlinks with text
        text = sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # Removes all links
        text = sub(r'(https|http|file|ftp):?\/?(\S+|\w+.\w+\/\w+)?', '', text)
        return text

    @staticmethod
    def text_len_sanitize(  # TODO chews last words, fix needed
            text: str,
            max_length: int,
    ) -> list:
        # Split by comma or dot (else you can lose intonations), if there is non, split by groups of 299 chars
        if '.' in text and all([split_text.__len__() < max_length for split_text in text.split('.')]):
            return text.split('.')

        if ',' in text and all([split_text.__len__() < max_length for split_text in text.split(',')]):
            return text.split(',')

        return [text[i:i + max_length] for i in range(0, len(text), max_length)]

    async def get_tts(
            self,
            text_to_tts: str,
    ) -> str:
        async with self.client.post(
                url=self.uri_base,
                params={
                    'text_speaker': self.voice,
                    'req_text': text_to_tts,
                    'speaker_map_type': 0,
                }) as result:
            response = await result.json()
            output_text = [response.get('data').get('v_str')][0]
        return output_text

    @staticmethod
    async def decode_tts(
            output_text: str,
            filename: str,
    ) -> None:
        decoded_text = base64.b64decode(output_text)

        async with open(f'assets/audio/{filename}.mp3', 'wb') as out:
            await out.write(decoded_text)

    async def __call__(
            self,
            req_text: str,
            filename: str | int,
    ) -> None:
        if not req_text:
            raise ValueError(f'Text never came for file - {filename}.mp3')

        req_text = self.text_sanitize(req_text)

        if getenv("PROFANE_FILTER", 'False') == 'True':
            from src.audio.tts.profane_filter import profane_filter

            req_text = profane_filter(req_text)

        output_text = ''

        # use multiple api requests to make the sentence
        if len(req_text) > 299:
            for part in self.text_len_sanitize(req_text, 299):
                if part:
                    output_text += await self.get_tts(part)

            await self.decode_tts(output_text, filename)
            return

        # if under 299 characters do it in one
        output_text = await self.get_tts(req_text)

        await self.decode_tts(output_text, filename)
