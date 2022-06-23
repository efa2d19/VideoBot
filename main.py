from asyncio import run

from src.reddit.reddit_main import Reddit


async def main():
    # TODO add selector for different platforms later
    content = Reddit()
    await content()


if __name__ == '__main__':
    run(main())
