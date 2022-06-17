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

from dotenv import load_dotenv

W, H = 1080, 1920

load_dotenv()

# Settings
# TODO add checks if envs unset or incorrect
opacity = int(getenv('opacity'))
time_before_first_picture = float(getenv('time_before_first_picture'))
time_before_tts = float(getenv('time_before_tts'))
time_between_pictures = float(getenv('time_between_pictures'))
volume_of_background_music = int(getenv('volume_of_background_music'))
final_video_length = int(getenv('final_video_length'))
delay_before_end = int(getenv('delay_before_end'))
manual_mode = getenv('manual_mode')


async def main():
    print('started')  # TODO add progress bars in CLI
    async with ClientSession() as client:
        submission, comments, is_nsfw = await reddit_setup(client)
        if manual_mode:
            print(f'Is this submission ok? (y/n/e)\n{submission.title}')
            manual_confirmation = input()
            if not all(map(lambda x, y: x.upper() == y.upper(), [i for i in manual_confirmation], [i for i in 'exit'])):
                print('Exiting...')
                exit(1)
            if not all(map(lambda x, y: x.upper() == y.upper(), [i for i in manual_confirmation], [i for i in 'yes'])):
                await main()
        async_tasks = list()
        screenshot = RedditScreenshot()
        async_browser = await screenshot.get_browser()
        async_tasks.append(
            tts(client, submission.title, 'title')
        )
        async_tasks.append(
            screenshot(
                async_browser,
                f'https://www.reddit.com{submission.permalink}',
                submission.fullname,
                'title',
                is_nsfw,
            )
        )
        for index, comment in enumerate(comments):
            async_tasks.append(
                tts(client, comment.body, index)
            )

            async_tasks.append(
                screenshot(
                    async_browser,
                    f'https://www.reddit.com{comment.permalink}',
                    comment.fullname,
                    index,
                    is_nsfw
                )
            )
        await asyncio.gather(*async_tasks)
        await screenshot.close_browser(async_browser)
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
    correct_audio_offset = time_before_tts * 2 + time_between_pictures

    audio_title = create_audio_clip(
        'title',
        time_before_first_picture + time_before_tts,
    )
    video_duration += audio_title.duration + time_before_first_picture + time_before_tts
    audio_clip_list.append(audio_title)
    indexes_for_videos = list()

    for audio in range(comments.__len__()):
        temp_audio_clip = create_audio_clip(
            audio,
            correct_audio_offset + video_duration,
        )
        if video_duration + temp_audio_clip.duration + correct_audio_offset > final_video_length:
            continue
        video_duration += temp_audio_clip.duration + correct_audio_offset
        audio_clip_list.append(temp_audio_clip)
        indexes_for_videos.append(audio)

    if getenv('enable_background_audio', 'True') == 'True':
        back_audio = (
            AudioFileClip(await background_audio(video_duration + delay_before_end))
            .set_start(0)
            .set_duration(video_duration + delay_before_end)
        )
        back_audio = (
            afx
            .audio_normalize(back_audio)
            .volumex(volume_of_background_music / 100)
        )

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
            .set_duration(time_before_tts * 2 + audio_duration, change_end=False)
            .set_position('center')
            .resize(width=W - 100)
            .set_opacity(opacity / 100)
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

    for photo in range(audio_clip_list.__len__() - index_offset):
        photo_clip_list.append(
            create_image_clip(
                indexes_for_videos[photo],
                audio_clip_list[photo + index_offset].start,
                audio_clip_list[photo + index_offset].end,
                audio_clip_list[photo + index_offset].duration
            )
        )

    back_video = (
        VideoFileClip(await background_video(video_duration + delay_before_end))
        .without_audio()
        .set_start(0)
        .set_end(video_duration + delay_before_end)
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
        f'{getenv("final_video_name", "final_video")}.mp4',  # TODO test is, fails
        fps=30,
        audio_codec='aac',
        audio_bitrate='192k',
    )

    # Clean up
    [remove(asset) for asset in glob('assets/*/*')]
