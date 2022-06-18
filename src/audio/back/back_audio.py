from os import getenv

from src.api.youtube import youtube_get_file


async def background_audio(
        lenght: int | float,
) -> str:
    link = getenv('youtube_background_audio')
    background_video_query = getenv('background_audio_query')
    if not background_video_query:
        background_video_query = 'lofi type beat'
    await youtube_get_file('back', link, background_video_query, lenght, 'mp3', 'audio')
    return 'assets/audio/back.mp3'
