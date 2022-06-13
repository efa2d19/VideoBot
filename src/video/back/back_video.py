from os import getenv

from src.api.youtube import youtube_get_file


async def background_video(
        lenght: int,
) -> str:
    link = getenv('youtube_background_video', False)
    background_video_query = getenv('background_video_query', None)
    if not background_video_query:
        background_video_query = 'Relaxing Minecraft Parkour short'
    await youtube_get_file('back', link, background_video_query, lenght, 'mp4')
    return 'assets/video/back.mp4'
