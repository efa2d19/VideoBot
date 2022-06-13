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
            await tts(client, comment.body, f'{index}.mp3')
            tts_list.append(f'{index}_body.mp3')
            screenshot(f'https://www.reddit.com{comment.permalink}', comment.id, f'{index}.png', is_nsfw)
            screenshot_list.append(f'{index}_photo.png')
    print('collected')

    background_audio()
    background_video()

    audio_clip_list = list()
    audio_title = AudioFileClip('assets/audio/title.mp3')
    duration = audio_title.duration
    audio_clip_list.append(
        (
            audio_title
            .set_duration(duration + 2)
            .set_start(1)
            .set_end(duration + 2)
        )
    )
    for audio in tts_list:
        audio_clip = AudioFileClip(audio)
        clip_duration = audio_clip.duration
        audio_clip = (
            audio_clip
            .set_duration(clip_duration + 2)
            .set_start(duration + 1)
            .set_end(duration + clip_duration + 2)
        )
        audio_clip_list.append(audio_clip)
        duration += clip_duration
    back_audio = (
            AudioFileClip('assets/audio/back.mp3')
            .set_start(0)
            .set_end(duration)
            .fx(afx.audio_normalize)  # TODO Check if works
            .volumex(0.2)  # TODO Check if works
        )

    audio_clip_list.insert(
        0,
        afx.audio_loop(back_audio)  # TODO Check if works
    )

    audio = CompositeAudioClip(audio_clip_list)

    photo_clip_list = list()
    for index, photo in enumerate(screenshot_list):
        index_offset = 1

        if getenv('enable_background_audio', 'True') == 'True':
            index_offset += 1
        photo_clip = (
            ImageClip(photo)
            .set_duration(audio_clip_list[index + index_offset].duration + 1)
            .set_start(audio_clip_list[index + index_offset].start - 0.5)
            .set_end(audio_clip_list[index + index_offset].end + 0.5)
            .set_position('center')
            .resize(width=W - 100)
            .set_opacity(float(opacity)))
        photo_clip_list.append(photo_clip)

    back_video = (
        VideoFileClip('assets/video/back.mp4')
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

    final_video = CompositeVideoClip(photo_clip_list)
    final_video.audio = audio

    print('writing')

    final_video.write_videofile(
        'final_video.mp4',
        fps=30,
        audio_codec='aac',
        audio_bitrate='192k',
    )

    # Clean up
    Popen(['rm', '-rf' 'assets/*/*'])
