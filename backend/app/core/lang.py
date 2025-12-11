#!/usr/bin/env python3

import re
import nltk
import enchant
import fugashi
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

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
        self.lemmatizer = WordNetLemmatizer()

    def is_word(self, token):
        return len(token) > 1 and self.enchant_dict.check(token) and self.re_word.match(token)

    def _get_wordnet_pos(self, tag):
        """Map POS tag to first character lemmatize() accepts"""
        if tag.startswith("J"):
            return wordnet.ADJ
        elif tag.startswith("V"):
            return wordnet.VERB
        elif tag.startswith("N"):
            return wordnet.NOUN
        elif tag.startswith("R"):
            return wordnet.ADV
        else:
            return wordnet.NOUN

    def get_tokens(self) -> list:
        tokens = nltk.tokenize.word_tokenize(self.content)
        tagged_tokens = nltk.pos_tag(tokens)

        for token, tag in tagged_tokens:
            if token.endswith(".") and token.count(".") == 1:
                token = token.replace(".", "")

            wordnet_pos = self._get_wordnet_pos(tag)
            lemma = self.lemmatizer.lemmatize(token.lower(), pos=wordnet_pos)

            if not self.is_word(lemma):
                continue

            yield lemma


class Japanese(Language):
    def __init__(self, content, subtitle_path):
        super().__init__(content, subtitle_path)

        self.name = LANGUAGE["jp"]
        self.tagger = fugashi.Tagger()

    def is_word(self, token):
        return is_japanese(token)

    def get_tokens(self) -> list:
        for word in self.tagger(self.content):
            token = word.feature.lemma if word.feature.lemma else word.surface
            if self.is_word(token):
                yield token
