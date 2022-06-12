from os import getenv

from src.api.youtube import youtube_get_file


def background_video(
        file_title: str,
        min_lenght: int,
) -> None:
    link = getenv('youtube_background_video', False)
    background_video_query = getenv('background_video_query', None)
    if not background_video_query:
        background_video_query = 'Relaxing Minecraft Parkour'
    youtube_get_file(file_title, min_lenght, link, background_video_query, 'mp4')
