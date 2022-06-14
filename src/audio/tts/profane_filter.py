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
                filtered_text = sub(f'{word}(\s+|$)', f'{word[0]} ', filtered_text)
    return filtered_text
