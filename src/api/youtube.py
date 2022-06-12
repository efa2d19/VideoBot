from pytube import YouTube, Search

from typing import Optional


def youtube_get_file(
        file_title: str,
        min_lenght: int,
        link: str,
        query: str,
        file_extension: str = 'mp4',
) -> None:

    if link:
        YouTube(link).streams.filter(progressive=True, file_extension=file_extension).order_by(
            'resolution').desc().first().download(filename=file_title)
    else:
        youtube_instance: Optional[YouTube] = None
        while True:
            for video in Search(query).results:
                if min_lenght * 2 >= video.length >= min_lenght:
                    youtube_instance = video
                    break
            if youtube_instance:
                break
        youtube_instance.streams.filter(progressive=True, file_extension=file_extension).order_by(
            'resolution').desc().first().download(filename=file_title)
