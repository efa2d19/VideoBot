import base64
from os import getenv

from src.audio.tts.ValidVoices import voice_list

from aiohttp import ClientSession
from aiofiles import open


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
    def text_len_sanitize(
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
            filename: str,  # TODO remove after debug
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

        if not output_text:  # TODO wrote blank file once, fixes, resend request doesn't help(
            print(f'no response - file {filename}.mp3')
            print('---------')
            print(text_to_tts)
            print('---------')
            # output_text = await self.get_tts(
            #     text_to_tts,
            #     filename,
            # )

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

        if getenv("PROFANE_FILTER", 'False') == 'True':
            from src.audio.tts.profane_filter import profane_filter

            req_text = profane_filter(req_text)

        output_text = ''

        # use multiple api requests to make the sentence
        if len(req_text) > 299:
            for part in self.text_len_sanitize(req_text, 299):
                output_text += await self.get_tts(part, filename)

            await self.decode_tts(output_text, filename)
            return

        # if under 299 characters do it in one
        output_text = await self.get_tts(req_text, filename)

        await self.decode_tts(output_text, filename)
