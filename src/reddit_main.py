from aiohttp import ClientSession

from src.api.reddit import reddit_setup

from src.audio.tts.tts_wrapper import tts
from src.audio.back.back_audio import background_audio

from src.video.screenshots import RedditScreenshot
from src.video.back.back_video import background_video

from moviepy.editor import *
from moviepy.audio.fx.volumex import volumex
from moviepy.audio.AudioClip import CompositeAudioClip

from os import remove

W, H = 1080, 1920

opacity = 0.9


async def main():
    print('started')
    async with ClientSession() as client:
        submission_title, comments, is_nsfw = await reddit_setup(client)
        await tts(client, submission_title, 'title.mp3')
        screenshot = RedditScreenshot()
        tts_list = list()
        screenshot_list = list()
        for index, comment in enumerate(comments):
            await tts(client, comment.body, f'{index}_body.mp3')
            tts_list.append(f'{index}_body.mp3')
            screenshot(f'https://www.reddit.com{comment.permalink}', comment.id, f'{index}_photo.png', is_nsfw)
            screenshot_list.append(f'{index}_photo.png')
    print('collected')
    audio_clip_list = list()
    photo_clip_list = list()
    duration = 1
    for audio, photo in zip(tts_list, screenshot_list):
        audio_clip = AudioFileClip(audio)
        photo_clip = (
            ImageClip(photo)
            .set_duration(audio_clip.duration + 1)
            .set_start(duration - 0.5)
            .set_position('center')
            .resize(width=W - 100)
            .set_opacity(float(opacity)))
        audio_clip = (
            audio_clip
            # .set_duration(audio_clip.duration + 2)
            # .set_start(duration)
        )
        duration += audio_clip.duration
        # audio_clip = audio_clip \
        #     .set_end(duration)
        photo_clip = photo_clip \
            .set_end(duration - 1)
        audio_clip_list.append(audio_clip)
        photo_clip_list.append(photo_clip)
    print('got lists')
    background_video('background_video.mp4', 120)
    # background_audio('background_audio.mp3', duration)
    print('got background')

    # back_audio = (
    #     volumex(AudioFileClip('background_audio.mp3'), 0.2)
    #     .set_duration(duration)
    #     .set_start(0)
    #     .set_end(duration)
    # )
    # audio_clip_list.insert(
    #     0,
    #     back_audio
    # )
    audio_concate = concatenate_audioclips(audio_clip_list)
    audio = CompositeAudioClip([audio_concate])
    images_concate = concatenate_videoclips(photo_clip_list).set_position(
        ("center", "center")
    )
    images_concate.audio = audio
    back_video = (
        VideoFileClip('background_video.mp4')
        .without_audio()
        .set_start(0)
        .set_end(duration)
        .resize(height=H)
        .crop(x1=1166.6, y1=0, x2=2246.6, y2=1920)
    )
    final_video = CompositeVideoClip([back_video, images_concate])
    print('writing')

    final_video.write_videofile(
        'final_video.mp4',
        fps=30,
        audio_codec="aac",
        audio_bitrate="192k"
    )

    print('cleaning up')
    for audio, video in zip(tts_list, screenshot_list):
        remove(audio)
        remove(video)
    remove('title.mp3')
