from os import getenv

from src.api.youtube import youtube_get_file


async def background_video(
        lenght: int | float,
) -> None:
    link = getenv('YT_BACK_VIDEO')
    background_video_query = getenv('BACK_VIDEO_QUERY')
    if not background_video_query:
        background_video_query = 'minecraft parkour gameplay'
    await youtube_get_file('back', link, background_video_query, lenght, 'mp4')
