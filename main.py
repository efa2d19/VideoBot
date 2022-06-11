import asyncio

from aiohttp import ClientSession
from dotenv import load_dotenv

from src.api.reddit import reddit_setup
from src.audio.tts.tts_wrapper import tts

load_dotenv()


async def main():
    async with ClientSession() as client:
        submission_title, comments = await reddit_setup(client)
        await tts(client, submission_title, 'title.mp3')
        for index, comment in enumerate(comments):
            await tts(client, comment.body, f'{index}_body.mp3')


if __name__ == '__main__':
    asyncio.run(main())