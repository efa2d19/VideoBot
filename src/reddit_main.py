import asyncio

from aiohttp import ClientSession

from src.api.reddit import reddit_setup

from src.audio.tts.tts_wrapper import tts
from src.audio.back.back_audio import background_audio

from src.video.screenshots import RedditScreenshot
from src.video.back.back_video import background_video

from moviepy.editor import *
# from moviepy.audio.fx.volumex import volumex
# from moviepy.audio.AudioClip import CompositeAudioClip

from os import getenv
from subprocess import Popen

W, H = 1080, 1920

opacity = 0.9  # TODO move to envs


async def main():
    print('started')
    async with ClientSession() as client:
        submission, comments, is_nsfw = await reddit_setup(client)
        async_tasks = [tts(client, submission.title, 'title')]
        screenshot = RedditScreenshot()
        screenshot(f'https://www.reddit.com{submission.permalink}', '', 'title', is_nsfw)
        # TODO fix (screen of comment)
        for index, comment in enumerate(comments):
            async_tasks.append(tts(client, comment.body, index))
            screenshot(f'https://www.reddit.com{comment.permalink}', comment.id, index, is_nsfw)
        await asyncio.gather(*async_tasks)
    print('collected')

    duration = 0
    audio_clip_list = list()

    audio_title = AudioFileClip('assets/audio/title.mp3').set_start(1)
    duration += audio_title.duration

    audio_clip_list.append(audio_title)

    for audio in range(comments.__len__()):
        audio_clip = AudioFileClip(f'assets/audio/{audio}.mp3').set_start(duration + 2)
        audio_clip_list.append(audio_clip)
        duration += audio_clip.duration

    if getenv('enable_background_audio', 'True') == 'True':
        back_audio = (
                AudioFileClip(await background_audio(duration))
                .set_duration(duration)
                .set_start(0)
                .volumex(0.2)  # TODO Check if works
            )

        audio_clip_list.insert(
            0,
            afx.audio_normalize(back_audio)
            # back_audio.fx(afx.audio_loop())  # TODO Check if works
        )

    final_audio = CompositeAudioClip(audio_clip_list)

    photo_clip_list = list()

    index_offset = 1

    if getenv('enable_background_audio', 'True') == 'True':
        index_offset += 1

    photo_title = ImageClip('assets/img/title.png')
    photo_clip_list.append(
        (
            photo_title
            .set_start(audio_clip_list[index_offset].start - 0.5)
            .set_end(audio_clip_list[index_offset].end + 0.5)
            .set_duration(audio_clip_list[index_offset].duration + 1)
            .set_position('center')
            .resize(width=W - 100)
            .set_opacity(float(opacity)))
        )

    for photo in range(comments.__len__()):
        photo_clip = (
            ImageClip(f'assets/img/{photo}.png')
            .set_start(audio_clip_list[photo + index_offset].start - 0.5)
            .set_end(audio_clip_list[photo + index_offset].end + 0.5)
            .set_duration(audio_clip_list[photo + index_offset].duration + 1)
            .set_position('center')
            .resize(width=W - 100)
            .set_opacity(float(opacity)))
        photo_clip_list.append(photo_clip)

    back_video = (
        VideoFileClip(await background_video(duration))
        .without_audio()
        .set_start(0)
        .set_end(duration)
        .resize(height=H)
        .crop(x1=1166.6, y1=0, x2=2246.6, y2=1920)
    )

    photo_clip_list.insert(
        0,
        back_video
    )

    final_video = CompositeVideoClip(photo_clip_list)  # Merge all videos in one
    final_video.audio = final_audio  # Add audio clips to final video

    print('writing')

    final_video.write_videofile(
        'final_video.mp4',
        fps=30,
        audio_codec='aac',
        audio_bitrate='192k',
    )

    # Clean up
    Popen(['rm', '-rf' 'assets/*/*'])  # TODO doesnt work(
