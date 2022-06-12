from re import sub
from os import getenv

from src.audio.tts.profane_list.en import profane_list


def profane_filter(
        text: str,
        word_list: list = profane_list,
) -> str:
    word_list.sort(reverse=True, key=len)
    filtered_text = text
    if getenv("PROFANE_FILTER", 'False') == 'True' and any([word in word_list for word in text.split()]):
        for word in word_list:
            if word in text:
                word_lenght = word.__len__()
                word_half = word_lenght // 2 if word_lenght % 2 == 0 else word_lenght // 2 + 1
                filtered_text = sub(word, f'{word[:word_half]}', filtered_text)
    return filtered_text
