from os import getenv

from src.api.youtube import Youtube


async def background_audio(
        lenght: int | float,
) -> None:
    link = getenv('YT_BACK_AUDIO')
    background_video_query = getenv('BACK_AUDIO_QUERY')
    if not background_video_query:
        background_video_query = 'lofi type beat'
    await Youtube('back', link, background_video_query, lenght, 'mp3', 'audio').download()
