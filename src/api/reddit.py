from aiohttp import ClientSession
import asyncpraw

import random
from os import getenv


async def reddit_setup(client: 'ClientSession') -> tuple:
    default_useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
                        '(KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36'

    client_id = getenv('CLIENT_ID')
    client_secret = getenv('CLIENT_SECRET')

    if not client_id or not client_secret:
        raise ValueError('Check .env file, client_id or client_secret is not set')

    reddit = asyncpraw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=default_useragent,
        requestor_kwargs={'session': client},
    )
    reddit.read_only = True

    subreddit = getenv('subreddit')
    if not subreddit or subreddit == 'random':  # TODO add check for comments w/ pictures
        subreddit = await reddit.random_subreddit()
    else:
        subreddit = await reddit.subreddit(subreddit)

    submission_from_envs = getenv('submission')

    async def get_submission():
        if submission_from_envs:
            if 'http' in submission_from_envs:
                results = await reddit.submission(url=submission_from_envs)
            else:
                results = await reddit.submission(id=submission_from_envs)
        else:
            results = random.choice([i async for i in subreddit.hot(limit=50)])
        await results.load()
        return results

    allow_nsfw = getenv('allow_nsfw', 'True') == 'True'
    is_nsfw = False
    while True:
        submission = await get_submission()
        if not allow_nsfw and not submission_from_envs:
            if 'nsfw' in submission.whitelist_status:
                continue
        else:
            is_nsfw = 'nsfw' in submission.whitelist_status
            break

    # TODO add min max comment lenght
    number_of_comments = int(getenv('number_of_comments', 15)) if getenv('number_of_comments', 15) else 15
    top_level_comments = list(submission.comments)[:number_of_comments]
    return submission, top_level_comments, is_nsfw
