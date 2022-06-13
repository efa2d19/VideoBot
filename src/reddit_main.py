import asyncio
from aiohttp import ClientSession

from src.api.reddit import reddit_setup

from src.video.screenshots import RedditScreenshot
from src.video.back.back_video import background_video

from src.audio.tts.tts_wrapper import tts
from src.audio.back.back_audio import background_audio

from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from moviepy.editor import AudioFileClip, CompositeAudioClip, afx

from os import getenv, remove
from glob import glob

W, H = 1080, 1920

opacity = 0.9  # TODO move to envs
time_before_first_picture = 1  # TODO move to envs
time_before_tts = 1  # TODO move to envs
time_between_pictures = 2  # TODO move to envs
volume_of_background_music = 10  # TODO move to envs (in percents)


async def main():
    print('started')
    async with ClientSession() as client:
        submission, comments, is_nsfw = await reddit_setup(client)
        async_tasks = [tts(client, submission.title, 'title')]
        screenshot = RedditScreenshot()
        screenshot(f'https://www.reddit.com{submission.permalink}', submission.id, 'title', is_nsfw, is_title=True)
        for index, comment in enumerate(comments):
            async_tasks.append(tts(client, comment.body, index))
            screenshot(f'https://www.reddit.com{comment.permalink}', comment.id, index, is_nsfw)
        await asyncio.gather(*async_tasks)
    print('collected')

    def create_audio_clip(
            clip_title: str | int,
            clip_start: float,
    ) -> 'AudioFileClip':
        return (
            AudioFileClip(f'assets/audio/{clip_title}.mp3')
            .set_start(clip_start)
        )

    video_duration = 0
    audio_clip_list = list()

    audio_title = create_audio_clip(
        'title',
        time_before_first_picture,
    )
    video_duration += audio_title.duration
    audio_clip_list.append(audio_title)

    for audio in range(comments.__len__()):
        temp_audio_clip = create_audio_clip(
            audio,
            time_before_tts * 2 + time_between_pictures + video_duration,
        )
        video_duration += temp_audio_clip.duration
        audio_clip_list.append(temp_audio_clip)

    if getenv('enable_background_audio', 'True') == 'True':
        back_audio = (
            AudioFileClip(await background_audio(time_before_tts * 2 + time_between_pictures + video_duration))
            .set_duration(time_before_tts * 2 + time_between_pictures + video_duration)
            .set_start(0)
        )
        back_audio = afx.audio_normalize(back_audio).volumex(volume_of_background_music / 100)

        audio_clip_list.insert(
            0,
            back_audio
            # back_audio.fx(afx.audio_loop())  # TODO Check if works
        )

    final_audio = CompositeAudioClip(audio_clip_list)

    def create_image_clip(
            image_title: str | int,
            audio_start: float,
            audio_end: float,
            audio_duration: float,
    ) -> 'ImageClip':
        return (
            ImageClip(f'assets/img/{image_title}.png')
            .set_start(audio_start - time_before_tts)
            .set_end(audio_end + time_before_tts)
            .set_duration(time_before_tts * 2 + audio_duration)
            .set_position('center')
            .resize(width=W - 100)
            .set_opacity(float(opacity))
        )

    index_offset = 1
    if getenv('enable_background_audio', 'True') == 'True':
        index_offset += 1

    photo_clip_list = list()

    photo_clip_list.append(
        create_image_clip(
            'title',
            audio_clip_list[index_offset - 1].start,
            audio_clip_list[index_offset - 1].end,
            audio_clip_list[index_offset - 1].duration
        )
    )

    for photo in range(comments.__len__()):
        photo_clip_list.append(
            create_image_clip(
                photo,
                audio_clip_list[photo + index_offset].start,
                audio_clip_list[photo + index_offset].end,
                audio_clip_list[photo + index_offset].duration
            )
        )

    back_video = (
        VideoFileClip(await background_video(time_before_tts * 2 + time_between_pictures + video_duration))
        .without_audio()
        .set_start(0)
        .set_end(time_before_tts * 2 + time_between_pictures + video_duration)
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
    [remove(asset) for asset in glob('assets/*/*')]
