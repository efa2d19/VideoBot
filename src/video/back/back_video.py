from pytube import YouTube
from os import getenv
import requests


def background_video(
        title: str
) -> None:
    link = getenv('youtube_background_video', False)
    if link:
        YouTube(link).streams.first().download(title)
    else:
        # results = requests.get(
        #     'https://www.youtube.com/results',
        #     params={
        #         'search_query': 'minecraft parkour gameplay',
        #     }).json()

        from src.video.back.default import default_list
        from random import choice
        link = choice(default_list)
        YouTube(link).streams.first().download(title)
