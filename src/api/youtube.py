from youtubesearchpython.__future__ import CustomSearch, VideoDurationFilter
from pytube import YouTube

from random import choice


async def search_yt(
        query: str,
        length: int | float,
) -> str:
    yt_instance = CustomSearch(query, VideoDurationFilter.short, limit=20)  # TODO move to something else

    yt_results = await yt_instance.next()

    yt_length_check = [video.get('link') for video in yt_results.get('result') if
                       video.get('duration') and int(video.get('duration').split(':')[0]) * 60 + int(
                           video.get('duration').split(':')[1]) >= length / 2]

    yt_result = choice(yt_length_check if yt_length_check else [None])
    return yt_result


async def youtube_get_file(
        file_title: str,
        link: str,
        query: str,
        length: int | float,
        file_extension: str = 'mp4',
        file_folder: str = 'video',
) -> None:
    if link:
        YouTube(link).streams.filter(progressive=True).order_by('resolution').desc().first().download(
            output_path=f'assets/{file_folder}/', filename=f'{file_title}.{file_extension}')
    else:
        yt_result = await search_yt(query, length)

        if not yt_result:
            raise ValueError(f'Can\'t find video:\ntitle - {query}\nlength - {int(length)}')

        YouTube(yt_result).streams.filter(progressive=True).order_by('resolution').desc().first().download(
            output_path=f'assets/{file_folder}/', filename=f'{file_title}.{file_extension}')
