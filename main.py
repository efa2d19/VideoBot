from asyncio import run, CancelledError

from src.reddit.reddit_video import Reddit


async def main():
    # TODO add selector for different platforms later
    content = Reddit()
    await content()


if __name__ == '__main__':
    try:
        run(main())
    except (KeyboardInterrupt, CancelledError):
        print('\nExiting...')
        exit(1)
    except Exception as e:
        print(f'\nError occurred: {e}')
        exit(1)
