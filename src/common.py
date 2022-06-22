def cleanup(
        exit_code: int = 0
) -> None:
    from os import remove
    from glob import glob

    # Clean up
    [remove(asset) for asset in glob('assets/*/*')]

    # Exiting
    exit(exit_code)
