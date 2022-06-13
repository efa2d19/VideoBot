from os import getenv

from src.api.youtube import youtube_get_file


async def background_audio(
        lenght: int,
) -> str:
    link = getenv('youtube_background_audio', False)
    background_video_query = getenv('background_audio_query', None)
    if not background_video_query:
        background_video_query = 'lofi hip hop short'
    await youtube_get_file('back', link, background_video_query, lenght, 'mp3', 'audio')
    return 'assets/audio/back.mp3'
