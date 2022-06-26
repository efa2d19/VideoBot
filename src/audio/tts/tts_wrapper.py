from aiohttp import ClientSession
from aiofiles import open

import base64

from os import getenv
from re import sub

from attr import attrs, attrib
from attr.validators import instance_of

from src.audio.tts.ValidVoices import voice_list
from src.common import str_to_bool


def voice_validator(instance, attribute, value):
    if not value or value not in voice_list:
        raise ValueError('Not valid voice:', value)


@attrs
class TikTokTTS:
    client: 'ClientSession' = attrib()
    # List of valid voices in ValidVoices.py
    voice: str = attrib(validator=voice_validator, default=getenv('TTS_VOICE', 'en_us_002'))
    profane_filter: bool = attrib(validator=instance_of(bool),
                                  default=str_to_bool(getenv('PROFANE_FILTER')) if getenv('PROFANE_FILTER') else False)
    uri_base: str = 'https://api16-normal-useast5.us.tiktokv.com/media/api/text/speech/invoke/'

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

        if str_to_bool(getenv('PROFANE_FILTER', 'False')):
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
