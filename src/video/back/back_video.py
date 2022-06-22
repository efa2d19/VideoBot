from os import getenv

from src.api.youtube import youtube_get_file


async def background_video(
        lenght: int | float,
) -> None:
    link = getenv('youtube_background_video')
    background_video_query = getenv('background_video_query')
    if not background_video_query:
        background_video_query = 'minecraft parkour gameplay'
    await youtube_get_file('back', link, background_video_query, lenght, 'mp4')
