from os import getenv

from src.api.youtube import youtube_get_file


def background_audio(
        file_title: str,
        min_lenght: int,
) -> None:
    audio = getenv('enable_background_audio', 'True') == 'True'
    if audio:
        link = getenv('youtube_background_audio', False)
        background_video_query = getenv('background_audio_query', None)
        if not background_video_query:
            background_video_query = 'lofi hip hop short'
        youtube_get_file(file_title, min_lenght, link, background_video_query, 'mp4')
