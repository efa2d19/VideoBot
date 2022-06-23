from aiohttp import ClientSession
from tqdm.asyncio import tqdm as async_tqdm

import attr
from os import getenv
from dotenv import load_dotenv

from rich.console import Console
from rich.columns import Columns

from src.api.reddit import reddit_setup
from src.common import cleanup


load_dotenv()

manual_mode = getenv('manual_mode')


@attr.s(auto_attribs=True)
class CollectReddit:
    client: ClientSession
    options: list[str] = ['[green](y)es[/green]', '[magenta](n)o[/magenta]', '[red](e)xit[/red]']
    console_options: dict = {'style': 'yellow'}
    console: Console = Console(**console_options)

    async def __call__(
            self,
    ):
        reddit_results = await async_tqdm.gather(
            reddit_setup(self.client),
            desc='Gathering Reddit',
            leave=False,
        )
        self.submission, self.comments, self.is_nsfw = reddit_results[0]
        if manual_mode:
            if not await self.confirm_submission():
                return await self.__call__()
            confirmed_comments = await self.confirm_comments()
            self.comments = confirmed_comments if confirmed_comments else self.comments
        return self.submission, self.comments, self.is_nsfw

    def column_from_obj(
            self,
            obj: list | str,
    ) -> None:
        self.console.print(Columns(obj, equal=True, padding=(0, 3)))

    def input_validation(
            self,
    ):
        while True:
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
                return confirmed_comments
