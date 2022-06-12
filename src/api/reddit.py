from aiohttp import ClientSession
import asyncpraw

import random
from os import getenv


async def reddit_setup(client: 'ClientSession') -> tuple:
    default_useragent = 'Video bot'

    reddit = asyncpraw.Reddit(
        client_id=getenv('CLIENT_ID'),
        client_secret=getenv('CLIENT_SECRET'),
        user_agent=default_useragent,
        requestor_kwargs={"session": client},
    )
    reddit.read_only = True

    subreddit = getenv('subreddit', False)
    if not subreddit or subreddit == 'random':
        subreddit = await reddit.random_subreddit()
    else:
        subreddit = await reddit.subreddit(subreddit)

    async def get_submission():
        results = random.choice([i async for i in subreddit.hot(limit=50)])
        await results.load()
        return results

    allow_nsfw = getenv('allow_nsfw', 'True') == 'True'
    is_nsfw = False
    while True:
        submission = await get_submission()
        if not allow_nsfw:
            if 'nsfw' in submission.whitelist_status:
                continue
        else:
            is_nsfw = 'nsfw' in submission.whitelist_status
            break
    # submission.comment_sort = "new"

    number_of_comments = int(getenv('number_of_comments', 10))
    top_level_comments = list(submission.comments)[:number_of_comments]
    return submission.title, top_level_comments, is_nsfw
