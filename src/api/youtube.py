from youtubesearchpython.__future__ import CustomSearch, VideoDurationFilter
from pytube import YouTube

from random import choice
from attr import attrs

from src.common import Console


@attrs(auto_attribs=True)
class Youtube(Console):
    file_title: str
    link: str
    query: str
    length: int | float
    file_extension: str = 'mp4'
    file_folder: str = 'video'

    async def search_yt(
            self,
    ) -> None:
        # TODO maybe move to something else (deprecated)
        yt_instance = CustomSearch(self.query, VideoDurationFilter.short, limit=20)

        yt_results = await yt_instance.next()

        yt_normalized_list = [
            video.get('link') for video in yt_results.get('result') if
            video.get('duration') and int(video.get('duration').split(':')[0]) * 60 + int(
                video.get('duration').split(':')[1]) >= self.length / 2
        ]

        while True:
            yt_result = choice(yt_normalized_list if yt_normalized_list else [None])

            self.console.print(f'\n\nUse this content?\n{yt_result}')

            if self.input_validation():
                self.console.clear()
                self.link = yt_result
                return

            yt_normalized_list.remove(yt_result)
            self.console.clear()
            self.console.print('[magenta]Content removed![/magenta]', end='\n\n')

    def download_yt(
            self,
    ) -> None:
        if self.file_folder == 'video':
            YouTube(self.link).streams.filter().order_by('resolution').desc().first().download(
                output_path=f'assets/{self.file_folder}/', filename=f'{self.file_title}.{self.file_extension}')
            return
        if self.file_folder == 'audio':
            YouTube(self.link).streams.filter(type='audio').order_by('abr').desc().first().download(
                output_path=f'assets/{self.file_folder}/', filename=f'{self.file_title}.{self.file_extension}')
            return
        raise ValueError(f'Incorrect file_folder: {self.file_folder}')

    async def download(
            self,
    ) -> None:
        if self.link:
            self.download_yt()
        else:
            await self.search_yt()
            if not self.link:
                raise ValueError(f'Can\'t find video:\ntitle - {self.query}\nlength - {int(self.length)}')

            self.download_yt()
