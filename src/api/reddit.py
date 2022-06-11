from os import getenv
import random
import asyncpraw
from aiohttp import ClientSession


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

    submission = random.choice([i async for i in subreddit.hot(limit=10)])
    await submission.load()

    # submission.comment_sort = "new"
    top_level_comments = list(submission.comments)
    return submission.title, top_level_comments
