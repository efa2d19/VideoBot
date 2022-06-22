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
    console = Console(style='yellow')
    confirmed_comments = list()
    submission_is_ok = None
    options = ['[green](y)es[/green]', '[magenta](n)o[/magenta]', '[red](e)xit[/red]']

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
            await self.confirm_submission()
            if not self.submission_is_ok:
                return await self.__call__()
            await self.confirm_comments()
            if self.confirmed_comments:
                self.comments = self.confirmed_comments
        return self.submission, self.comments, self.is_nsfw

    def input_options(
            self
    ) -> None:
        self.console.print(Columns(self.options, equal=True, padding=(0, 3)))

    def column_from_obj(
            self,
            obj: list | str,
    ) -> None:
        self.console.print(Columns(obj, equal=True, padding=(0, 3)))

    async def confirm_submission(
            self,
    ) -> None:
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
            self.input_options()
            manual_confirmation = input()
            if all(map(lambda x, y: x.upper() == y.upper(), [i for i in manual_confirmation if i],
                       [i for i in 'exit'])):
                self.console.clear()
                self.console.print('[red]Exiting...[/red]')
                cleanup(exit_code=1)
            if all(map(lambda x, y: x.upper() == y.upper(), [i for i in manual_confirmation if i], [i for i in 'no'])):
                self.console.clear()
                break
            if all(map(lambda x, y: x.upper() == y.upper(), [i for i in manual_confirmation if i], [i for i in 'yes'])):
                self.console.clear()
                self.submission_is_ok = True
                break
            else:
                self.console.clear()
                self.console.print('[red]I don\'t understand you... Let\'s try again[/red]', end='\n\n')

    async def confirm_comments(
            self,
    ) -> None:
        while True:
            self.console.print('Wanna approve comments by hand?', end='\n\n')
            self.input_options()

            comment_confirm = input()
            if all(map(lambda x, y: x.upper() == y.upper(), [i for i in comment_confirm if i], [i for i in 'exit'])):
                self.console.clear()
                self.console.print('[red]Exiting...[/red]')
                cleanup(exit_code=1)
            if all(map(lambda x, y: x.upper() == y.upper(), [i for i in comment_confirm if i], [i for i in 'no'])):
                self.console.clear()
                break
            if all(map(lambda x, y: x.upper() == y.upper(), [i for i in comment_confirm if i], [i for i in 'yes'])):
                self.console.clear()
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
                        self.input_options()
                        comment_approve = input()

                        if all(map(lambda x, y: x.upper() == y.upper(), [i for i in comment_approve if i],
                                   [i for i in 'exit'])):
                            self.console.clear()
                            self.console.print('[red]Exiting...[/red]')
                            cleanup(exit_code=1)
                        if all(map(lambda x, y: x.upper() == y.upper(), [i for i in comment_approve if i],
                                   [i for i in 'no'])):
                            self.console.clear()
                            self.console.print('[magenta]Comment removed![/magenta]', end='\n\n')
                            break
                        if all(map(lambda x, y: x.upper() == y.upper(), [i for i in comment_approve if i],
                                   [i for i in 'yes'])):
                            self.console.clear()
                            self.confirmed_comments.append(comment)
                            break
                        else:
                            self.console.clear()
                            self.console.print('I don\'t understand you... Let\'s try again', end='\n\n')
                self.console.clear()
                break
            else:
                self.console.clear()
                self.console.print('I don\'t understand you... Let\'s try again', end='\n\n')
