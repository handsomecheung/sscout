#!/usr/bin/env python3


import time

import pathlib

NAME = "sscout"
VERSION = "0.0.1"


def get_home_dir():
    d = pathlib.Path.home().joinpath(f".{NAME}")
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_cache_dir():
    d = get_home_dir().joinpath("cache")
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_cache_file(lang, suffix):
    return get_cache_dir().joinpath(f"{time.strftime('%Y%m%d%H%M%S')}.{lang}.{suffix}.txt")
