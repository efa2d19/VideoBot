from youtubesearchpython.__future__ import CustomSearch, VideoDurationFilter
from pytube import YouTube, Search

from random import choice


async def youtube_get_file(
        file_title: str,
        link: str,
        query: str,
        length: int,
        file_extension: str = 'mp4',
        file_folder: str = 'video',
) -> None:
    if link:
        YouTube(link).streams.filter(progressive=True).order_by(
            'resolution').desc().first().download(output_path=f'assets/{file_folder}/',
                                                  filename=f'{file_title}.{file_extension}')
    else:
        yt_instance = CustomSearch(query, VideoDurationFilter.short, limit=20)
        yt_results = await yt_instance.next()

        yt_result = choice([video.get('link') for video in yt_results.get('result') if
                            video.get('duration') and int(video.get('duration').split(':')[0]) * 60 + int(
                                video.get('duration').split(':')[1]) >= length])

        YouTube(yt_result).streams.filter(progressive=True).order_by(
            'resolution').desc().first().download(output_path=f'assets/{file_folder}/',
                                                  filename=f'{file_title}.{file_extension}')
