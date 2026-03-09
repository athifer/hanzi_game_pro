
import json
import os

import pandas as pd
import requests
import zipfile
import io
from tqdm import tqdm

DATA_DIR = "data"

def download(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.content

def build_characters():
    print("Downloading common characters list...")

    # Public mirror of 3500 common characters
    url = "https://raw.githubusercontent.com/skishore/makemeahanzi/master/dictionary.txt"

    txt = download(url).decode("utf-8").splitlines()

    chars = []
    for line in txt:
        try:
            j = json.loads(line)
        except json.JSONDecodeError:
            continue
        ch = j.get("character", "")
        if len(ch) == 1:
            chars.append(ch)

    chars = list(dict.fromkeys(chars))[:3500]

    df = pd.DataFrame({"character": chars})
    df.to_csv(f"{DATA_DIR}/characters_3500.csv", index=False)

    print("characters_3500.csv created")

def build_words():
    print("Downloading CC-CEDICT...")

    url = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
    data = download(url)

    import gzip
    txt = gzip.decompress(data).decode("utf-8").splitlines()

    words = []

    for line in txt:
        if line.startswith("#"):
            continue
        parts = line.split(" ")
        if len(parts) < 2:
            continue

        word = parts[1]
        if 1 < len(word) <= 4:
            words.append(word)

    df = pd.DataFrame({"word": list(set(words))})
    df.to_csv(f"{DATA_DIR}/words_frequency.csv", index=False)

    print("words_frequency.csv created")

def build_sentences():
    print("Downloading Tatoeba Chinese sentences...")

    url = "https://downloads.tatoeba.org/exports/sentences.csv"

    txt = download(url).decode("utf-8").splitlines()

    rows = []

    for line in txt:
        parts = line.split("\t")
        if len(parts) >= 3 and parts[1] == "cmn":
            rows.append(parts[2])

    df = pd.DataFrame({"sentence": rows[:50000]})
    df.to_csv(f"{DATA_DIR}/sentences_basic.csv", index=False)

    print("sentences_basic.csv created")

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    build_characters()
    build_words()
    build_sentences()

if __name__ == "__main__":
    main()
