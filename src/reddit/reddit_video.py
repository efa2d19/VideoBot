from aiohttp import ClientSession
from tqdm.asyncio import tqdm as async_tqdm

from tqdm import trange
from proglog import TqdmProgressBarLogger

from os import getenv
from dotenv import load_dotenv
from attr import attrs, attrib
from attr.validators import instance_of

from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from moviepy.video.fx.loop import loop
from moviepy.video.fx.resize import resize
from moviepy.video.fx.crop import crop

from moviepy.editor import AudioFileClip, CompositeAudioClip
from moviepy.audio.fx.audio_loop import audio_loop
from moviepy.audio.fx.volumex import volumex
from moviepy.audio.fx.audio_normalize import audio_normalize

from src.common import cleanup, name_normalize, str_to_bool, Console
from src.reddit.reddit_collect import CollectReddit
from src.video.back.back_video import background_video
from src.audio.back.back_audio import background_audio


load_dotenv()


@attrs
class Reddit(Console):
    # Settings w/ checks for incorrect envs
    # TODO maybe move to pydantic
    opacity: int = attrib(converter=int, validator=instance_of(int),
                          default=getenv('OPACITY', 95))
    time_before_first_picture: float = attrib(converter=float, validator=instance_of((float, int)),
                                              default=getenv('TIME_BEFORE_FIRST', 1))
    time_before_tts: float = attrib(converter=float, validator=instance_of((float, int)),
                                    default=getenv('TIME_BEFORE_TTS', 0.5))
    time_between_pictures: float = attrib(converter=float, validator=instance_of((float, int)),
                                          default=getenv('TIME_BETWEEN_PICTURES', 1))
    volume_of_background_music: int = attrib(converter=int, validator=instance_of(int),
                                             default=getenv('BACK_MUSIC_VOLUME', 15))
    final_video_length: int = attrib(converter=int, validator=instance_of(int),
                                     default=getenv('FINAL_VIDEO_LENGTH', 60))
    delay_before_end: int = attrib(converter=int, validator=instance_of(int),
                                   default=getenv('DELAY_BEFORE_END', 1))
    final_video_name: str | None = attrib(validator=instance_of((str, None)),
                                          default=getenv('FINAL_VIDEO_NAME'))
    enable_background_audio: bool = attrib(validator=instance_of(bool),
                                           default=str_to_bool(getenv('ENABLE_BACK_AUDIO')) if getenv(
                                               'ENABLE_BACK_AUDIO') else True)
    width: int = attrib(converter=int, validator=instance_of(int),
                        default=getenv('VIDEO_WIDTH', 1080))
    height: int = attrib(converter=int, validator=instance_of(int),
                         default=getenv('VIDEO_HEIGHT', 1920))

    def create_image_clip(
            self,
            image_title: str | int,
            audio_start: float,
            audio_end: float,
            audio_duration: float,
    ) -> 'ImageClip':
        return (
            ImageClip(f'assets/img/{image_title}.png')
            .set_start(audio_start - self.time_before_tts)
            .set_end(audio_end + self.time_before_tts)
            .set_duration(self.time_before_tts * 2 + audio_duration, change_end=False)
            .set_position('center')
            .set_opacity(self.opacity / 100)
            .fx(resize, width=self.width - 100)
        )

    async def __call__(self):
        async with ClientSession() as client:
            reddit_instance = CollectReddit(client)
            comments_len = await reddit_instance.collect_content()

            if not self.final_video_name:
                self.final_video_name = name_normalize(reddit_instance.submission_instance.title)
            else:
                self.final_video_name = name_normalize(self.final_video_name)

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
        correct_audio_offset = self.time_before_tts * 2 + self.time_between_pictures

        audio_title = create_audio_clip(
            'title',
            self.time_before_first_picture + self.time_before_tts,
        )
        video_duration += audio_title.duration + self.time_before_first_picture + self.time_before_tts
        audio_clip_list.append(audio_title)
        indexes_for_videos = list()

        for audio in trange(
                comments_len,
                desc='Gathering audio clips',
                leave=False,
        ):
            temp_audio_clip = create_audio_clip(
                audio,
                correct_audio_offset + video_duration,
            )
            if video_duration + temp_audio_clip.duration + correct_audio_offset + self.delay_before_end \
                    > self.final_video_length:
                continue
            video_duration += temp_audio_clip.duration + correct_audio_offset
            audio_clip_list.append(temp_audio_clip)
            indexes_for_videos.append(audio)

        video_duration += self.delay_before_end

        async_tasks = list()

        async_tasks.append(background_video(video_duration))
        if self.enable_background_audio:
            async_tasks.append(background_audio(video_duration))

        await async_tqdm.gather(
            *async_tasks,
            desc='Gathering back content',
            leave=False,
        )

        if self.enable_background_audio:
            back_audio = (
                AudioFileClip('assets/audio/back.mp3')
                .set_start(0)
                .fx(audio_loop, duration=video_duration)
                .fx(audio_normalize)
                .fx(volumex, self.volume_of_background_music / 100)
            )

            audio_clip_list.insert(
                0,
                back_audio,
            )

        final_audio = CompositeAudioClip(audio_clip_list)

        index_offset = 1
        if self.enable_background_audio:
            index_offset += 1

        photo_clip_list = list()

        photo_clip_list.append(
            self.create_image_clip(
                'title',
                audio_clip_list[index_offset - 1].start,
                audio_clip_list[index_offset - 1].end,
                audio_clip_list[index_offset - 1].duration
            )
        )

        for photo in trange(
                audio_clip_list.__len__() - index_offset,
                desc='Gathering photo clips',
                leave=False,
        ):
            photo_clip_list.append(
                self.create_image_clip(
                    indexes_for_videos[photo],
                    audio_clip_list[photo + index_offset].start,
                    audio_clip_list[photo + index_offset].end,
                    audio_clip_list[photo + index_offset].duration
                )
            )

        back_video = (
            VideoFileClip('assets/video/back.mp4')
            .without_audio()
            .set_start(0)
            .fx(resize, height=self.height)
            .fx(loop, duration=video_duration)
        )

        back_video_width, back_video_height = back_video.size

        # Fix to crop for vertical videos
        if back_video_width < self.width:
            back_video = (
                back_video
                .fx(resize, width=self.width)
            )
            back_video_width, back_video_height = back_video.size
            back_video = back_video.fx(
                crop,
                x1=0,
                x2=back_video_width,
                y1=back_video_height / 2 - self.height / 2,
                y2=back_video_height / 2 + self.height / 2
            )
        else:
            back_video = back_video.fx(
                crop,
                x1=back_video_width / 2 - self.width / 2,
                x2=back_video_width / 2 + self.width / 2,
                y1=0,
                y2=back_video_height
            )

        photo_clip_list.insert(
            0,
            back_video
        )

        final_video = CompositeVideoClip(photo_clip_list)  # Merge all videos in one
        final_video.audio = final_audio  # Add audio clips to final video

        final_video.write_videofile(
            f'{self.final_video_name}.mp4',
            fps=30,
            audio_codec='aac',
            audio_bitrate='192k',
            verbose=False,
            logger=TqdmProgressBarLogger(print_messages=False)
        )

        reddit_instance.console.print(f'Your video is ready:\n[cyan]{self.final_video_name}.mp4[/cyan]')

        cleanup()
