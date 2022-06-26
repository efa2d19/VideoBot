import asyncpraw
from aiohttp import ClientSession

import random
from os import getenv
from dotenv import load_dotenv

from rich.console import Console

from attr import attrs, attrib
from attrs.validators import instance_of

from src.common import str_to_bool

load_dotenv()


@attrs
class RedditAPI:
    client: ClientSession = attrib()
    console: Console = attrib(validator=instance_of(Console))
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

    async def get_submission(
            self,
            subreddit: asyncpraw.models.Subreddit,
    ):
        if self.submission_from_envs:
            if 'http' in self.submission_from_envs:
                results = await self.reddit.submission(url=self.submission_from_envs)
            else:
                results = await self.reddit.submission(id=self.submission_from_envs)
        else:
            # TODO add top/hot selector in envs
            #  'time_filter: Can be one of: all, day, hour, month, week, year (default: all).'
            results = random.choice([i async for i in subreddit.hot(limit=50)])
        await results.load()
        return results

    async def reddit_setup(
            self,
    ) -> tuple:
        if not self.subreddit or self.subreddit == 'random':  # TODO add check for comments w/ pictures
            subreddit = await self.reddit.random_subreddit()
        else:
            subreddit = await self.reddit.subreddit(self.subreddit)

        is_nsfw = False
        while True:
            submission = await self.get_submission(subreddit)
            if not self.allow_nsfw and not self.submission_from_envs:
                if 'nsfw' in submission.whitelist_status:
                    self.console.print('[magenta]Submission is NSFW.[/magenta]')
                    self.console.print('Skipping...')
                    continue
            is_nsfw = 'nsfw' in submission.whitelist_status
            break

        while True:
            submission = await self.get_submission(subreddit)
            if submission.score < self.min_upvotes and not self.submission_from_envs:
                self.console.print(f'[magenta]Not enough upvotes: {submission.score}.[/magenta]')
                self.console.print('Skipping...')
                continue
            break

        top_level_comments = [comment for comment in submission.comments if
                              self.max_comment_lenght >= getattr(comment, 'body',
                                                                 '').__len__() >= self.min_comment_lenght][
                             :self.number_of_comments]
        return submission, top_level_comments, is_nsfw
