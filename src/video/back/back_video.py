from os import getenv

from src.api.youtube import youtube_get_file


def background_video(
) -> None:
    link = getenv('youtube_background_video', False)
    background_video_query = getenv('background_video_query', None)
    if not background_video_query:
        background_video_query = 'Relaxing Minecraft Parkour'
    youtube_get_file('back', link, background_video_query, 'mp4')
