import asyncio
from datetime import datetime

from aiohttp import ClientSession

from src.api.reddit import reddit_setup

from src.video.screenshots import RedditScreenshot
from src.video.back.back_video import background_video

from src.audio.tts.tts_wrapper import TikTokTTS
from src.audio.back.back_audio import background_audio

from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from moviepy.video.fx.loop import loop
from moviepy.video.fx.resize import resize
from moviepy.video.fx.crop import crop

from moviepy.editor import AudioFileClip, CompositeAudioClip
from moviepy.audio.fx.audio_loop import audio_loop
from moviepy.audio.fx.volumex import volumex
from moviepy.audio.fx.audio_normalize import audio_normalize

from os import getenv

from dotenv import load_dotenv

W, H = 1080, 1920

load_dotenv()

# Settings w/ checks for incorrect envs
opacity = int(getenv('opacity')) if getenv('opacity') else 95
time_before_first_picture = float(getenv('time_before_first_picture')) if getenv('time_before_first_picture') else 1
time_before_tts = float(getenv('time_before_tts')) if getenv('time_before_tts') else 0.5
time_between_pictures = float(getenv('time_between_pictures')) if getenv('time_between_pictures') else 1
volume_of_background_music = int(getenv('volume_of_background_music')) if getenv('volume_of_background_music') else 15
final_video_length = int(getenv('final_video_length')) if getenv('final_video_length') else 60
delay_before_end = int(getenv('delay_before_end')) if getenv('delay_before_end') else 1
final_video_name = getenv("final_video_name") if getenv("final_video_name") else "final_video"
enable_background_audio = getenv('enable_background_audio') if getenv('enable_background_audio') else 'True'
manual_mode = getenv('manual_mode')


def cleanup(
        exit_code: int = 0
) -> None:
    from os import remove
    from glob import glob

    # Clean up
    [remove(asset) for asset in glob('assets/*/*')]

    # Exiting
    exit(exit_code)


async def collect_content(  # TODO add progress bars in CLI
) -> int:
    async with ClientSession() as client:
        submission, comments, is_nsfw = await reddit_setup(client)
        if manual_mode:
            while True:
                print(f'Is this submission ok? (y/n/e)\n{submission.title}')
                manual_confirmation = input()
                if all(map(lambda x, y: x.upper() == y.upper(), [i for i in manual_confirmation], [i for i in 'exit'])):
                    print('Exiting...')
                    cleanup(exit_code=1)
                if all(map(lambda x, y: x.upper() == y.upper(), [i for i in manual_confirmation], [i for i in 'no'])):
                    await main()
                if all(map(lambda x, y: x.upper() == y.upper(), [i for i in manual_confirmation], [i for i in 'yes'])):
                    break
                else:
                    print('I don\'t understand you... Let\'s try again')

        start = datetime.now()
        async_tasks = list()
        screenshot = RedditScreenshot()
        tts = TikTokTTS(client)
        async_browser = await screenshot.get_browser()
        async_tasks.append(
            tts(
                submission.title,
                'title'
            )
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
                tts(
                    comment.body,
                    index,
                )
            )

        await asyncio.gather(*async_tasks)

        async_tasks_secondary = list()

        for index, comment in enumerate(comments):
            async_tasks_secondary.append(
                screenshot(
                    async_browser,
                    f'https://www.reddit.com{comment.permalink}',
                    comment.fullname,
                    index,
                    is_nsfw,
                )
            )

        await asyncio.gather(*async_tasks_secondary)
        await screenshot.close_browser(async_browser)
        end = datetime.now()
        print((end - start).total_seconds())
        return comments.__len__()


async def main():
    print('started')  # TODO add progress bars in CLI

    comments_len = await collect_content()

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

    for audio in range(comments_len):
        temp_audio_clip = create_audio_clip(
            audio,
            correct_audio_offset + video_duration,
        )
        if video_duration + temp_audio_clip.duration + correct_audio_offset > final_video_length:
            continue
        video_duration += temp_audio_clip.duration + correct_audio_offset
        audio_clip_list.append(temp_audio_clip)
        indexes_for_videos.append(audio)

    video_duration += delay_before_end

    if enable_background_audio == 'True':
        back_audio = (
            AudioFileClip(await background_audio(video_duration))
            .set_start(0)
            .fx(audio_loop, duration=video_duration)
            .fx(audio_normalize)
            .fx(volumex, volume_of_background_music / 100)
        )

        audio_clip_list.insert(
            0,
            back_audio,
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
            .set_opacity(opacity / 100)
            .fx(resize, width=W - 100)
        )

    index_offset = 1
    if enable_background_audio == 'True':
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
        VideoFileClip(await background_video(video_duration))
        .without_audio()
        .set_start(0)
        .fx(resize, height=H)
        .fx(loop, duration=video_duration)
    )

    back_video_width, back_video_height = back_video.size

    # Fix to crop for vertical videos
    if back_video_width < W:
        back_video = (
            back_video
            .fx(resize, width=W)
        )
        back_video_width, back_video_height = back_video.size
        back_video = back_video.fx(
            crop,
            x1=0,
            x2=back_video_width,
            y1=back_video_height / 2 - H / 2,
            y2=back_video_height / 2 + H / 2
        )
    else:
        back_video = back_video.fx(
            crop,
            x1=back_video_width / 2 - W / 2,
            x2=back_video_width / 2 + W / 2,
            y1=0,
            y2=back_video_height
        )

    photo_clip_list.insert(
        0,
        back_video
    )

    final_video = CompositeVideoClip(photo_clip_list)  # Merge all videos in one
    final_video.audio = final_audio  # Add audio clips to final video

    print('writing')

    final_video.write_videofile(
        f'{final_video_name}.mp4',
        fps=30,
        audio_codec='aac',
        audio_bitrate='192k',
    )

    cleanup()
