#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""sscout - subtitle scout

Usage:
    sscout [options] <path>

Arguments:
    <path>                The path to the subtitle

Options:
    --style <style>       style for ssa font
"""

import os
import re
import sys
import time
import pathlib
import subprocess

import ass
import nltk
import docopt
import enchant

NAME = "sscout"
VERSION = "0.0.1"
LANGUAGE = {
    "en": "en",
    "jp": "jp",
}

enchant_dict = enchant.Dict("en_US")
re_word = re.compile(r"[a-zA-Z]")


def main(args) -> None:
    subtitle_path = pathlib.Path(args["<path>"])

    if not subtitle_path.exists():
        print(f"subtitle {subtitle_path} not exists")
        sys.exit(1)

    valid_lines = get_valid_lines(subtitle_path, args)
    content = "\n".join(valid_lines)

    lang = check_language(content)

    words = remove_known_words(split_into_words(content), lang)
    tfile = write_tfile(words, lang)
    subprocess.Popen(("vim", tfile)).wait()

    unknown_words = []
    with open(tfile, "r") as f:
        for new_word in f.readlines():
            w = new_word.strip()
            if w != "":
                unknown_words.append(w)

    add_known_words(set(words) - set(unknown_words), lang)

    top_unknown_words = unknown_words[0:20]
    topfile = pathlib.Path("/mnt/user-data-app/static-resource").joinpath(f"{NAME}.top-words.{tfile.name}")
    with open(topfile, "w") as f:
        f.write("\n".join(top_unknown_words) + "\n")

    print(f"open https://static-server.uen.site/{topfile.name}")


def get_valid_lines(subtitle_path, args):
    name = subtitle_path.name.lower()
    if name.endswith(".ass"):
        return get_valid_lines_ass(subtitle_path, args["--style"])
    elif name.endswith(".srt"):
        return get_valid_lines_srt(subtitle_path)
    else:
        raise Exception("supported format")


def get_valid_lines_ass(subtitle_path, style):
    with open(subtitle_path, encoding="utf_8_sig") as f:
        doc = ass.parse(f)

    styles = [s.name for s in doc.styles]
    if not style:
        if len(styles) == 1:
            style = styles[0]
        else:
            print(f"no style. set style to one of {styles}")
            sys.exit(1)

    if style not in styles:
        print(f"style must be one of {styles}")
        sys.exit(1)

    return [e.text for e in doc.events if e.style == style]


def get_valid_lines_srt(subtitle_path):
    with open(subtitle_path, "r") as f:
        return f.readlines()


def remove_known_words(words, lang):
    all_known_words = get_known_words(lang)

    unknown_words = []
    for word in words:
        if word not in all_known_words:
            unknown_words.append(word)

    return unknown_words


def add_known_words(words, lang):
    if len(words) == 0:
        return

    with open(get_known_file(lang), "a") as f:
        f.write("\n".join(words) + "\n")


def get_home_dir():
    d = pathlib.Path.home().joinpath(f".{NAME}")
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_cache_dir():
    d = get_home_dir().joinpath("cache")
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_known_file(lang):
    f = get_home_dir().joinpath(f"known-words.{lang}.txt")
    if not f.exists():
        f.touch()
    return f


def get_known_words(lang):
    words = set()
    with open(get_known_file(lang), "r") as f:
        for word in f.readlines():
            w = word.strip()
            if w != "":
                words.add(w)
    return words


def write_tfile(words, lang):
    tfilename = get_cache_dir().joinpath(f"{time.strftime('%Y%m%d%H%M%S')}.{lang}.txt")
    with open(tfilename, "w") as f:
        f.write("\n".join(words))
    return tfilename


def is_word(token):
    return len(token) > 1 and enchant_dict.check(token) and re_word.match(token)


def split_into_words(content) -> set:
    infos = {}
    for token in nltk.tokenize.word_tokenize(content):
        if token.endswith(".") and token.count(".") == 1:
            token = token.replace(".", "")

        if not is_word(token):
            continue

        token = token.lower()
        if token not in infos:
            infos[token] = 0

        infos[token] += 1

    return [word for word, _ in sorted(infos.items(), key=lambda items: -items[1])]


def check_language(content):
    if check_japanese(content):
        return LANGUAGE["jp"]
    else:
        return LANGUAGE["en"]


def check_japanese(content):
    all_count = len(content)
    if all_count == 0:
        return False

    match_count = re.findall(r"[\u2E80-\u9FFF]", content)
    return len(match_count) / all_count > 0.1


if __name__ == "__main__":
    args = docopt.docopt(__doc__, version=VERSION)
    main(args)
