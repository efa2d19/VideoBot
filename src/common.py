def cleanup(
        exit_code: int = 0
) -> None:
    from os import remove
    from glob import glob

    # Clean up
    [remove(asset) for asset in glob('assets/*/*')]

    # Exiting
    exit(exit_code)


def name_normalize(
        name: str
) -> str:
    from re import sub

    name = sub(r'[?\\"%*:|<>]', '', name)
    name = sub(r'( [w,W]\s?\/\s?[o,O,0])', r' without', name)
    name = sub(r'( [w,W]\s?\/)', r' with', name)
    name = sub(r'([0-9]+)\s?\/\s?([0-9]+)', r'\1 of \2', name)
    name = sub(r'(\w+)\s?\/\s?(\w+)', r'\1 or \2', name)
    name = sub(r'\/', r'', name)
    return name
