from tqdm.asyncio import tqdm as async_tqdm

from os import getenv
from dotenv import load_dotenv
from attr import attrs, attrib
from attr.validators import instance_of

from src.video.screenshots import RedditScreenshot
from src.audio.tts.tts_wrapper import TikTokTTS

from src.api.reddit import RedditAPI
from src.common import str_to_bool

load_dotenv()


@attrs
class CollectReddit(RedditAPI):
    manual_mode: bool = attrib(validator=instance_of(bool),
                               default=str_to_bool(getenv('MANUAL_MODE', 'True')))

    async def collect_reddit(self):
        if self.manual_mode:
            await self.get_submission()
            if not await self.confirm_submission():
                self.submission_instances.remove(self.submission_instance)
                return await self.collect_reddit()

            self.console.clear()

            await async_tqdm.gather(  # TODO remove newline before bar
                self.get_comments(),
                desc='Gathering comments',
                leave=False,
            )
            confirmed_comments = await self.confirm_comments()
            self.comments = confirmed_comments if confirmed_comments else self.comments

    async def confirm_submission(
            self,
    ) -> bool:
        self.console.clear()
        while True:
            self.console.print(
                'Use this submission?',
                end='\n\n'
            )
            self.console.print(
                f'[cyan]{self.submission_instance.title}[/cyan]', style=f'link {self.submission_instance.shortlink}',
                end='\n\n'
            )
            self.column_from_obj(
                [
                    f'Upvotes: [cyan]{self.submission_instance.score}[/cyan]',
                    f'Comments: [cyan]{self.submission_instance.num_comments}[/cyan]',
                ]
            )

            return True if self.input_validation() else False

    async def confirm_comments(
            self,
    ) -> list | None:
        self.console.clear()
        while True:
            self.console.print('Wanna approve comments by hand?', end='\n\n')

            if self.input_validation():
                self.console.clear()
                confirmed_comments = list()

                for comment in self.comments:
                    while True:
                        self.console.print(
                            f'Use this comment?',
                            end='\n\n'
                        )
                        self.console.print(
                            f'[white]{comment.body}[/white]',
                            style=f'link https://reddit.com{comment.permalink}',
                            end='\n\n'
                        )
                        self.column_from_obj(
                            [
                                f'Upvotes: [cyan]{comment.score}[/cyan]',
                                f'Awards: [cyan]{comment.total_awards_received}[/cyan]',
                            ]
                        )
                        if not self.input_validation():
                            self.console.clear()
                            self.console.print('[magenta]Comment removed![/magenta]', end='\n\n')
                            break
                        else:
                            confirmed_comments.append(comment)
                            self.console.clear()
                            self.console.print('[green]Comment approved![/green]', end='\n\n')
                            break
                return confirmed_comments
            self.console.clear()
            return

    async def collect_content(
            self,
    ) -> int:
        await self.get_subreddit()

        await async_tqdm.gather(
            self.get_submissions(),
            desc='Gathering submission',
            leave=False,
        )

        await async_tqdm.gather(
            self.collect_reddit(),
            desc='Gathering Reddit',
            leave=False,
        )

        async_tasks_primary = list()
        screenshot = RedditScreenshot()
        tts = TikTokTTS(self.client)
        async_browser = await screenshot.get_browser()
        # To enable dark_mode or accept nsfw once
        await async_tqdm.gather(
            screenshot(
                async_browser,
                f'https://www.reddit.com{self.submission_instance.permalink}',
                self.submission_instance.fullname,
                'title',
                self.is_nsfw,
            ),
            desc='Setting up browser',
            leave=False,
        )
        async_tasks_primary.append(
            tts(
                self.submission_instance.title,
                'title'
            )
        )

        for index, comment in enumerate(self.comments):
            async_tasks_primary.append(
                tts(
                    comment.body,
                    index,
                )
            )

        await async_tqdm.gather(
            *async_tasks_primary,
            desc='Gathering TTS',
            leave=False,
        )

        async_tasks_secondary = list()

        voiced_comments = [
            comments for comments, condition in zip(self.comments, async_tasks_secondary[1:]) if condition
        ]

        for index, comment in enumerate(voiced_comments):
            async_tasks_secondary.append(
                screenshot(
                    async_browser,
                    f'https://www.reddit.com{comment.permalink}',
                    comment.fullname,
                    index,
                    self.is_nsfw,
                )
            )

        await async_tqdm.gather(
            *async_tasks_secondary,
            desc='Gathering screenshots',
            leave=False,
            # Crutch for screenshot with title
            total=async_tasks_secondary.__len__() + 1,
        )
        await screenshot.close_browser(async_browser)
        return self.comments.__len__()
