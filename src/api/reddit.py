import asyncpraw
from aiohttp import ClientSession

from aiofiles import open

import random
from os import getenv
from dotenv import load_dotenv

from rich.console import Console

from attr import attrs, attrib
from attrs.validators import instance_of, optional

from src.common import str_to_bool

load_dotenv()


@attrs
class RedditAPI:
    client: ClientSession = attrib()
    console: Console = attrib(validator=instance_of(Console))
    subreddit_instance = attrib(validator=optional(instance_of(asyncpraw.Reddit)),
                                default=None)
    submission_instance = attrib(validator=optional(instance_of(asyncpraw.Reddit)),
                                 default=None)
    submission_instances: list = attrib(validator=optional(instance_of(list)),
                                        default=None)
    is_nsfw: bool = attrib(default=False)
    comments: list | bool = attrib(validator=optional(instance_of(list)),
                                   default=None)
    default_useragent: str = attrib(validator=instance_of(str),
                                    default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                                            '(KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36')

    client_id: str = attrib(validator=instance_of(str),
                            default=getenv('CLIENT_ID'))
    client_secret: str = attrib(validator=instance_of(str),
                                default=getenv('CLIENT_SECRET'))
    submission_from_envs: str = attrib(validator=instance_of(str),
                                       default=getenv('SUBMISSION'))
    allow_nsfw: bool = attrib(validator=instance_of(bool),
                              default=str_to_bool(getenv('ALLOW_NSFW')) if getenv('ALLOW_NSFW') else True)
    subreddit: str = attrib(validator=instance_of(str),
                            default=getenv('SUBREDDIT'))
    number_of_comments: int = attrib(validator=instance_of(int), converter=int,
                                     default=getenv('NUM_OF_COMMENTS'))
    min_comment_lenght: int = attrib(validator=instance_of(int), converter=int,
                                     default=getenv('MIN_COMMENT_LENGTH'))
    max_comment_lenght: int = attrib(validator=instance_of(int), converter=int,
                                     default=getenv('MAX_COMMENT_LENGTH'))
    min_upvotes: int = attrib(validator=instance_of(int), converter=int,
                              default=getenv('MIN_UPVOTES'))
    submission_settings: list = attrib(default=getenv('SUBMISSION_SETTINGS', 'hot 50').split())

    @submission_settings.validator
    def check_submission_settings(self, attribute, value: list):
        if value.__len__() != 2:
            raise ValueError('Check SUBMISSION_SETTINGS: not enough arguments')
        if value[0].lower() not in ['hot', 'top']:
            raise ValueError('Check SUBMISSION_SETTINGS: not in (hot, top)')
        if value[0].lower() == 'hot':
            try:
                int(value[1])
            except ValueError:
                raise ValueError(f'Check SUBMISSION_SETTINGS: wrong limit - {value[1]}')
        if value[0].lower() == 'top':
            if value[1] not in ['all', 'day', 'hour', 'month', 'week', 'year']:
                raise ValueError(f'Check SUBMISSION_SETTINGS: wrong period - {value[1]}')

    if not client_id or not client_secret:
        raise ValueError('Check .env file, client_id or client_secret is not set')

    def __attrs_post_init__(self):
        self.reddit = asyncpraw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.default_useragent,
            requestor_kwargs={'session': self.client},
        )
        self.reddit.read_only = True

    async def get_subreddit(
            self,
    ) -> None:
        if not self.subreddit or self.subreddit == 'random':  # TODO add check for comments w/ pictures
            self.subreddit_instance = await self.reddit.random_subreddit(self.allow_nsfw)
        else:
            self.subreddit_instance = await self.reddit.subreddit(self.subreddit)

    async def check_submission(
            self,
            submission,
    ) -> bool:
        if self.submission_from_envs:
            return True
        async with open('.submission.log', 'r') as out:
            if submission.id in await out.read():
                self.console.clear()
                self.console.print('[magenta]Submission was already used.[/magenta]')
                self.console.print('Skipping...', end='\n\n')
                return False
        if not self.allow_nsfw and not self.submission_from_envs:
            if 'nsfw' in submission.whitelist_status:
                self.console.clear()
                self.console.print('[magenta]Submission is NSFW.[/magenta]')
                self.console.print('Skipping...', end='\n\n')
                return False

        if submission.score < self.min_upvotes and not self.submission_from_envs:
            self.console.clear()
            self.console.print(f'[magenta]Not enough upvotes: {submission.score}.[/magenta]')
            self.console.print('Skipping...', end='\n\n')
            return False

        self.is_nsfw = 'nsfw' in submission.whitelist_status
        return True

    async def get_submissions(
            self,
    ) -> None:
        if self.submission_from_envs:
            if 'http' in self.submission_from_envs:
                self.submission_instances = await self.reddit.submission(url=self.submission_from_envs)
            else:
                self.submission_instances = await self.reddit.submission(id=self.submission_from_envs)
        else:
            if self.submission_settings[0] == 'hot':
                self.submission_instances = [i async for i in
                                             self.subreddit_instance.hot(limit=int(self.submission_settings[1]))]
            else:
                self.submission_instances = [i async for i in
                                             self.subreddit_instance.top(time_filter=self.submission_settings[1])]

    async def get_submission(
            self,
    ) -> None:
        while True:
            result = random.choice(self.submission_instances)
            if not await self.check_submission(result):
                self.submission_instances.remove(result)
                continue
            break

        self.submission_instance = result

    async def get_comments(
            self,
    ) -> None:
        await self.submission_instance.load()
        async with open(f'.submission.log', 'a') as out:
            await out.write('\n')
            await out.write(self.submission_instance.id)

        top_level_comments = [comment for comment in self.submission_instance.comments if
                              self.max_comment_lenght >= getattr(comment, 'body',
                                                                 '').__len__() >= self.min_comment_lenght]

        def sort_by_score(comment):
            return comment.score

        top_level_comments.sort(key=sort_by_score, reverse=True)

        self.comments = top_level_comments[:self.number_of_comments]
