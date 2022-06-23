from aiohttp import ClientSession
from tqdm.asyncio import tqdm as async_tqdm

import attr
from os import getenv
from dotenv import load_dotenv

from rich.console import Console
from rich.columns import Columns

from src.video.screenshots import RedditScreenshot
from src.audio.tts.tts_wrapper import TikTokTTS

from src.api.reddit import reddit_setup
from src.common import cleanup


load_dotenv()

manual_mode = getenv('manual_mode')


class CollectReddit:
    def __init__(
            self,
            client: ClientSession,
            options: dict | None = None,
            console: Console = Console(style='yellow')
    ):
        if options is None:
            options = ['[green](y)es[/green]', '[magenta](n)o[/magenta]', '[red](e)xit[/red]']
        self.client = client
        self.options = options
        self.console = console
        self.submission, self.comments, self.is_nsfw = None, None, None

    async def collect_reddit(self):
        reddit_results = await async_tqdm.gather(
            reddit_setup(self.client),
            desc='Gathering Reddit',
            leave=False,
        )
        self.submission, self.comments, self.is_nsfw = reddit_results[0]
        if manual_mode:
            if not await self.confirm_submission():
                return await self.collect_reddit()
            confirmed_comments = await self.confirm_comments()
            self.comments = confirmed_comments if confirmed_comments else self.comments

    def column_from_obj(
            self,
            obj: list | str,
    ) -> None:
        self.console.print(Columns(obj, equal=True, padding=(0, 3)))

    def input_validation(
            self,
    ):
        self.column_from_obj(self.options)

        received = input()

        if all(map(lambda x, y: x.upper() == y.upper(), [i for i in received if i], [i for i in 'exit'])):
            self.console.clear()
            self.console.print('[red]Exiting...[/red]')
            cleanup(exit_code=1)
        if all(map(lambda x, y: x.upper() == y.upper(), [i for i in received if i],
                   [i for i in 'no'])):
            self.console.clear()
            return False
        if all(map(lambda x, y: x.upper() == y.upper(), [i for i in received if i],
                   [i for i in 'yes'])):
            self.console.clear()
            return True
        else:
            self.console.clear()
            self.console.print('[red]I don\'t understand you... Let\'s try again[/red]', end='\n\n')

    async def confirm_submission(
            self,
    ) -> bool:
        while True:
            self.console.print(
                'Use this submission?',
                end='\n\n'
            )
            self.console.print(
                f'[cyan]{self.submission.title}[/cyan]', style=f'link {self.submission.shortlink}', end='\n\n'
            )
            self.column_from_obj(
                [
                    f'Upvotes: [cyan]{self.submission.score}[/cyan]',
                    f'Comments: [cyan]{self.submission.num_comments}[/cyan]',
                ]
            )

            return True if self.input_validation() else False

    async def confirm_comments(
            self,
    ) -> list | None:
        while True:
            self.console.print('Wanna approve comments by hand?', end='\n\n')

            if self.input_validation():
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
                            self.console.print('[magenta]Comment removed![/magenta]', end='\n\n')
                            break
                        else:
                            confirmed_comments.append(comment)
                            self.console.print('[green]Comment approved![/green]', end='\n\n')
                            break
                self.console.clear()
                return confirmed_comments
            self.console.clear()
            return

    async def collect_content(
            self,
    ) -> int:
        await self.collect_reddit()

        async_tasks_primary = list()
        screenshot = RedditScreenshot()
        tts = TikTokTTS(self.client)
        async_browser = await screenshot.get_browser()
        # It's a crutch to enable dark_mode or accept nsfw once
        async_tasks_primary.append(
            screenshot(
                async_browser,
                f'https://www.reddit.com{self.submission.permalink}',
                self.submission.fullname,
                'title',
                self.is_nsfw,
            )
        )
        async_tasks_primary.append(
            tts(
                self.submission.title,
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
            # Crutch for screenshot with title
            total=async_tasks_primary.__len__() - 1,
        )

        async_tasks_secondary = list()

        for index, comment in enumerate(self.comments):
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
