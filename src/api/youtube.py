from pytube import YouTube, Search

from random import choice


def youtube_get_file(
        file_title: str,
        link: str,
        query: str,
        file_extension: str = 'mp4',
        file_folder: str = 'video',
) -> None:
    if link:
        YouTube(link).streams.filter(progressive=True, file_extension=file_extension).order_by(
            'resolution').desc().first().download(output_path=f'assets/{file_folder}/',
                                                  filename=f'{file_title}.{file_extension}')
    else:
        youtube_instance = choice(Search(query).results)

        youtube_instance.streams.filter(progressive=True, file_extension=file_extension).order_by(
            'resolution').desc().first().download(output_path=f'assets/{file_folder}/',
                                                  filename=f'{file_title}.{file_extension}')
