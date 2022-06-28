from youtubesearchpython.__future__ import CustomSearch, VideoDurationFilter
from pytube import YouTube

from random import choice


async def search_yt(
        query: str,
        length: int | float,
) -> str:
    # TODO maybe move to something else (deprecated)
    yt_instance = CustomSearch(query, VideoDurationFilter.short, limit=20)

    yt_results = await yt_instance.next()

    yt_length_check = [video.get('link') for video in yt_results.get('result') if
                       video.get('duration') and int(video.get('duration').split(':')[0]) * 60 + int(
                           video.get('duration').split(':')[1]) >= length / 2]

    yt_result = choice(yt_length_check if yt_length_check else [None])
    return yt_result


def download_yt(
        link: str,
        file_title: str,
        file_folder: str = 'video',
        file_extension: str = 'mp4',
) -> None:
    if file_folder == 'video':
        YouTube(link).streams.filter().order_by('resolution').desc().first().download(
            output_path=f'assets/{file_folder}/', filename=f'{file_title}.{file_extension}')
        return
    if file_folder == 'audio':
        YouTube(link).streams.filter(type='audio').order_by('abr').desc().first().download(
            output_path=f'assets/{file_folder}/', filename=f'{file_title}.{file_extension}')
        return
    raise ValueError(f'Incorrect file_folder: {file_folder}')


async def youtube_get_file(
        file_title: str,
        link: str,
        query: str,
        length: int | float,
        file_extension: str = 'mp4',
        file_folder: str = 'video',
) -> None:
    if link:
        download_yt(link, file_title, file_folder, file_extension)
    else:
        yt_result = await search_yt(query, length)

        if not yt_result:
            raise ValueError(f'Can\'t find video:\ntitle - {query}\nlength - {int(length)}')

        download_yt(yt_result, file_title, file_folder, file_extension)
