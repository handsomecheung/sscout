#!/usr/bin/env python3

import re
import shutil
import subprocess

import nltk
import enchant
import fugashi

import common

LANGUAGE = {
    "en": "en",
    "jp": "jp",
}


def is_japanese(content):
    all_count = len(content)
    if all_count == 0:
        return False

    match_count = re.findall(r"[\u2E80-\u9FFF]", content)
    return len(match_count) / all_count > 0.1


def check_language(content):
    if is_japanese(content):
        return LANGUAGE["jp"]
    else:
        return LANGUAGE["en"]


def init_language(content, subtitle_path):
    language = check_language(content)

    if language == "en":
        return English(content, subtitle_path)
    elif language == "jp":
        return Japanese(content, subtitle_path)
    else:
        raise Exception(f"invalid language {language}")


class Language:
    def __init__(self, content, subtitle_path):
        self.content = content
        self.subtitle_path = subtitle_path

    def split_into_words(self) -> set:
        infos = {}
        for token in self.get_tokens():
            if token not in infos:
                infos[token] = 0

            infos[token] += 1

        return [word for word, _ in sorted(infos.items(), key=lambda items: -items[1])]


class English(Language):
    def __init__(self, content, subtitle_path):
        super().__init__(content, subtitle_path)

        self.name = LANGUAGE["en"]
        self.re_word = re.compile(r"[a-zA-Z]")
        self.enchant_dict = enchant.Dict("en_US")

    def is_word(self, token):
        return len(token) > 1 and self.enchant_dict.check(token) and self.re_word.match(token)

    def get_tokens(self) -> list:
        for token in nltk.tokenize.word_tokenize(self.content):
            if token.endswith(".") and token.count(".") == 1:
                token = token.replace(".", "")

            if not self.is_word(token):
                continue

            yield token.lower()


class Japanese(Language):
    def __init__(self, content, subtitle_path):
        super().__init__(content, subtitle_path)

        self.name = LANGUAGE["jp"]
        self.tagger = fugashi.Tagger("-Owakati")

    def get_tokens_auto(self) -> list:
        for word in self.tagger(self.content):
            token = str(word)
            if is_japanese(token):
                yield token

    def get_tokens_manually(self) -> list:
        file_content = common.get_cache_file(self.name, f"{self.subtitle_path.stem}.content")
        with open(file_content, "w") as f:
            f.write(self.content)

        file_token = common.get_cache_file(self.name, f"{self.subtitle_path.stem}.token")
        shutil.copy(file_content, file_token)
        subprocess.Popen(("emacs", "-nw", file_token)).wait()

        with open(file_token, "r") as f:
            return [line.strip() for line in f.readlines()]

    def get_tokens(self) -> list:
        return self.get_tokens_manually()
