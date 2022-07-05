from attr import attrs, attrib
from attr.validators import instance_of

from rich.columns import Columns
from rich.console import Console


@attrs()
class Console:
    console: Console = attrib(
        validator=instance_of(Console),
        default=Console(style='yellow'),
        kw_only=True,
    )
    options: list[str] = attrib(
        validator=instance_of(list),
        default=['[green](y)es[/green]', '[magenta](n)o[/magenta]', '[red](e)xit[/red]'],
        kw_only=True,
    )

    def column_from_obj(
            self,
            obj: list | str,
    ) -> None:
        self.console.print(Columns(obj, equal=True, padding=(0, 3)))

    def input_validation(
            self,
    ):
        self.column_from_obj(self.options)

        received = input()

        if all(map(lambda x, y: x.upper() == y.upper(), [i for i in received if i], [i for i in 'exit'])):
            self.console.clear()
            self.console.print('[red]Exiting...[/red]')
            cleanup(exit_code=1)
        if all(map(lambda x, y: x.upper() == y.upper(), [i for i in received if i],
                   [i for i in 'no'])):
            return False
        if all(map(lambda x, y: x.upper() == y.upper(), [i for i in received if i],
                   [i for i in 'yes'])):
            return True
        else:
            self.console.clear()
            self.console.print('[red]I don\'t understand you... Let\'s try again[/red]', end='\n\n')


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


def str_to_bool(s):
    if s in ['True', 'true']:
        return True
    elif s in ['False', 'false']:
        return False
    else:
        raise ValueError('Can\'t convert to bool:', s)


def audio_length(
        path: str,
) -> float | int:
    from mutagen.mp3 import MP3

    try:
        audio = MP3(path)
        return audio.info.length
    except Exception as e:  # TODO add logging
        return 0
