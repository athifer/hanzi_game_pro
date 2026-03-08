#!/usr/bin/env python3
"""
Generate web/js/characters.js from official Chinese character data.

Uses:
- 通用规范汉字表 (Table of General Standard Chinese Characters) Level 1: 3500 常用字
- CC-CEDICT dictionary for pinyin and English meanings
- Character frequency data for grade-level assignment

Grade distribution (approximating 部编版 elementary curriculum):
  Grade 1: 600 chars (most frequent / simplest)
  Grade 2: 600 chars
  Grade 3: 600 chars
  Grade 4: 600 chars
  Grade 5: 600 chars
  Grade 6: 500 chars
  Total:  3500 chars
"""

import os
import re
import ssl
import urllib.request

# Fix SSL for macOS Python
ssl._create_default_https_context = ssl._create_unverified_context

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_FILE = os.path.join(PROJECT_DIR, "web", "js", "characters.js")

COMMON_3500_SOURCE_URL = "https://raw.githubusercontent.com/wy-luke/All-Chinese-Character-Set/master/source/3500.txt"

# Grade distribution: maps grade -> number of characters
GRADE_SIZES = {1: 600, 2: 600, 3: 600, 4: 600, 5: 600, 6: 500}

# ── Download helpers ──

def download(url, desc=""):
    """Download URL content as string."""
    print(f"  Downloading {desc or url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def download_common_3500_chars():
    """Download canonical 3500 常用字 list and return as unique CJK char array."""
    raw = download(COMMON_3500_SOURCE_URL, "通用规范汉字表 Level 1 (3500)")
    chars = []
    seen = set()
    for ch in raw:
        if '\u4e00' <= ch <= '\u9fff' and ch not in seen:
            chars.append(ch)
            seen.add(ch)
    if len(chars) > 3500:
        chars = chars[:3500]
    return chars


def download_cedict():
    """Download and parse CC-CEDICT. Returns dict: char -> (pinyin, meaning)."""
    url = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
    print("Downloading CC-CEDICT...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        import gzip
        data = gzip.decompress(resp.read()).decode("utf-8", errors="replace")

    entries = {}  # char -> (pinyin, meaning)
    for line in data.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        # Format: Traditional Simplified [pinyin] /meaning1/meaning2/
        m = re.match(r"(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+/(.+)/", line)
        if not m:
            continue
        _trad, simp, pinyin, meaning = m.groups()
        if len(simp) == 1:
            # Only store single-character entries
            meanings = meaning.split("/")
            # Filter out classifier definitions and variant references
            clean = []
            for mg in meanings:
                mg = mg.strip()
                if not mg:
                    continue
                # Skip entries that are just references to other forms
                if mg.startswith("variant of") or mg.startswith("old variant"):
                    continue
                if mg.startswith("see ") and "[" in mg:
                    continue
                clean.append(mg)
            if not clean:
                clean = meanings[:1]  # fallback to first meaning

            best_meaning = clean[0] if clean else meaning.split("/")[0]
            # Truncate very long meanings
            if len(best_meaning) > 50:
                best_meaning = best_meaning[:47] + "..."

            pinyin_clean = convert_pinyin_numbers(pinyin.strip())

            # Prefer entries that are NOT surnames to keep primary meaning
            if simp not in entries:
                entries[simp] = (pinyin_clean, best_meaning)
            else:
                # If existing entry starts with "surname", replace it
                existing_meaning = entries[simp][1]
                if existing_meaning.lower().startswith("surname") and not best_meaning.lower().startswith("surname"):
                    entries[simp] = (pinyin_clean, best_meaning)

    return entries


def convert_pinyin_numbers(pinyin_str):
    """Convert numbered pinyin to tone-marked pinyin: 'ni3 hao3' -> 'nǐ hǎo'."""
    tone_marks = {
        'a': ['ā', 'á', 'ǎ', 'à'],
        'e': ['ē', 'é', 'ě', 'è'],
        'i': ['ī', 'í', 'ǐ', 'ì'],
        'o': ['ō', 'ó', 'ǒ', 'ò'],
        'u': ['ū', 'ú', 'ǔ', 'ù'],
        'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ'],
        'v': ['ǖ', 'ǘ', 'ǚ', 'ǜ'],
    }

    def convert_syllable(syl):
        syl = syl.strip()
        if not syl:
            return syl
        # Extract tone number
        if syl[-1].isdigit():
            tone = int(syl[-1])
            syl = syl[:-1]
        else:
            return syl  # no tone number

        if tone == 5 or tone == 0:
            return syl  # neutral tone

        # Replace 'u:' or 'v' with 'ü'
        syl = syl.replace("u:", "ü").replace("U:", "Ü")

        # Find the vowel to mark
        # Rules: 'a' or 'e' always get the mark; in 'ou', mark 'o'; otherwise mark last vowel
        vowels = 'aeiouüAEIOUÜ'
        if 'a' in syl.lower():
            for i, c in enumerate(syl):
                if c.lower() == 'a':
                    base = c.lower()
                    marked = tone_marks.get(base, [base]*4)[tone-1]
                    if c.isupper():
                        marked = marked.upper()
                    return syl[:i] + marked + syl[i+1:]
        elif 'e' in syl.lower():
            for i, c in enumerate(syl):
                if c.lower() == 'e':
                    base = c.lower()
                    marked = tone_marks.get(base, [base]*4)[tone-1]
                    if c.isupper():
                        marked = marked.upper()
                    return syl[:i] + marked + syl[i+1:]
        elif 'ou' in syl.lower():
            for i, c in enumerate(syl):
                if c.lower() == 'o':
                    base = c.lower()
                    marked = tone_marks.get(base, [base]*4)[tone-1]
                    if c.isupper():
                        marked = marked.upper()
                    return syl[:i] + marked + syl[i+1:]
        else:
            # Mark the last vowel
            for i in range(len(syl)-1, -1, -1):
                if syl[i].lower() in vowels:
                    base = syl[i].lower()
                    if base == 'v':
                        base = 'ü'
                    marked = tone_marks.get(base, [base]*4)[tone-1]
                    if syl[i].isupper():
                        marked = marked.upper()
                    return syl[:i] + marked + syl[i+1:]
        return syl

    parts = pinyin_str.split()
    converted = [convert_syllable(p) for p in parts]
    return " ".join(converted)


def download_frequency():
    """Download character frequency data. Returns dict: char -> rank (1=most frequent)."""
    # Try Jun Da's character frequency list (Modern Chinese)
    urls = [
        ("https://raw.githubusercontent.com/kaienfr/Font/master/learnfiles/char_freq.txt",
         "kaienfr frequency list"),
    ]

    for url, desc in urls:
        try:
            data = download(url, desc)
            freq = {}
            rank = 1
            for line in data.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("//"):
                    continue
                # Try tab or space separated: rank char freq
                parts = line.split()
                if len(parts) >= 2:
                    char = None
                    for p in parts:
                        if len(p) == 1 and '\u4e00' <= p <= '\u9fff':
                            char = p
                            break
                    if char and char not in freq:
                        freq[char] = rank
                        rank += 1
            if len(freq) >= 2000:
                print(f"  Loaded {len(freq)} frequency entries from {desc}")
                return freq
        except Exception as e:
            print(f"  Warning: failed to download {desc}: {e}")

    # Fallback: use a built-in frequency approximation
    # Top ~500 most frequent characters in Modern Chinese (well-established)
    print("  Using built-in frequency approximation...")
    TOP_FREQ = (
        "的一是了不在有人我他这中来上大个们到说时地为子就出会也你对生能而那得于着下自之年后作里如家"
        "可进多学都同工已经没好把又问行只其把开方还体应心去部种事么过所然很当面与前合从还手给已全"
        "点最因天国便但看外什又正些主想将它起两现到实少每次回才话新或系被好很现她分位别开回日并没"
        "水意高头长定实间本电加力理道气者成情情全小书提接基入化给明名重更美员走解完数几第直身加合"
        "月由比命感使教公问报特根民相条次变样立世活平别通果西何真教色利书市场指运思品此工口法共"
        "又二义特物走话通道四文想战八联门任金原任间身西革反认政利门军常白件场求量及表华指关打信"
        "让放今空知性海北题光设常强老即林记位少路图内至言论传计程切深认接住农技产取难近再白业织"
        "装受达解路干收总住考改清张济形达石影争流建望期始先统局南节史容调约干效业装受程除转候论"
        "语称至议选规治听切青记整局断准办约热保持首议确连千育委需层英集校持律深究式千六单思号准"
        "济病找证花价般观断造元术器言究容死必整府权花段杀千号况斗确越绝"
    )
    freq = {}
    rank = 1
    for ch in TOP_FREQ:
        if '\u4e00' <= ch <= '\u9fff' and ch not in freq:
            freq[ch] = rank
            rank += 1
    return freq


def sort_by_frequency(chars, freq_dict):
    """Sort characters by frequency (most frequent first). Unknown chars go to end."""
    max_rank = max(freq_dict.values()) + 1 if freq_dict else 1
    return sorted(chars, key=lambda c: freq_dict.get(c, max_rank + ord(c)))


# ── Main generation ──

def main():
    print("=" * 60)
    print("Generating characters.js")
    print("=" * 60)

    # 1. Download canonical 3500 list
    chars_3500 = download_common_3500_chars()
    print(f"\n1. Extracted {len(chars_3500)} unique characters from 通用规范汉字表 Level 1")

    # 2. Download frequency data
    print("\n2. Downloading frequency data...")
    freq = download_frequency()

    # 3. Sort by frequency
    print("\n3. Sorting characters by frequency...")
    chars_sorted = sort_by_frequency(chars_3500, freq)
    # Show first 20 for verification
    print(f"   Most frequent: {''.join(chars_sorted[:20])}")
    print(f"   Least frequent: {''.join(chars_sorted[-20:])}")

    # 4. Download CC-CEDICT
    print("\n4. Downloading CC-CEDICT for pinyin and meanings...")
    cedict = download_cedict()
    print(f"   CC-CEDICT: {len(cedict)} single-character entries")

    # 5. Split into grades
    print("\n5. Splitting into grades...")
    grades = {}
    idx = 0
    for grade, size in GRADE_SIZES.items():
        end = min(idx + size, len(chars_sorted))
        grades[grade] = chars_sorted[idx:end]
        idx = end
        print(f"   Grade {grade}: {len(grades[grade])} characters")

    # 6. Build JavaScript output
    print("\n6. Generating characters.js...")
    missing = 0
    total_chars = 0

    js_lines = []
    js_lines.append("/**")
    js_lines.append(" * Chinese Characters Dataset organized by grade level (1-6)")
    js_lines.append(" * Based on 通用规范汉字表 (Table of General Standard Chinese Characters) Level 1: 3500 常用字")
    js_lines.append(" * Characters sorted by frequency and assigned to grades 1-6.")
    js_lines.append(" * Pinyin and meanings from CC-CEDICT dictionary.")
    js_lines.append(" * Auto-generated by scripts/generate_characters_js.py")
    js_lines.append(" */")
    js_lines.append("")
    js_lines.append("const CHARACTERS_BY_GRADE = {")

    for grade in sorted(grades.keys()):
        js_lines.append(f"")
        js_lines.append(f"  {grade}: [")
        for ch in grades[grade]:
            total_chars += 1
            if ch in cedict:
                pinyin, meaning = cedict[ch]
            else:
                pinyin = "?"
                meaning = "(no definition found)"
                missing += 1
            # Escape quotes in meaning
            meaning = meaning.replace("\\", "\\\\").replace('"', '\\"')
            pinyin = pinyin.replace("\\", "\\\\").replace('"', '\\"')
            js_lines.append(f'    {{ char: "{ch}", pinyin: "{pinyin}", meaning: "{meaning}" }},')
        js_lines.append(f"  ],")

    js_lines.append("};")
    js_lines.append("")
    js_lines.append("// Helper: get all characters for a given grade range")
    js_lines.append("function getCharactersForGrades(minGrade, maxGrade) {")
    js_lines.append("  let result = [];")
    js_lines.append("  for (let g = minGrade; g <= maxGrade; g++) {")
    js_lines.append("    if (CHARACTERS_BY_GRADE[g]) {")
    js_lines.append("      result = result.concat(CHARACTERS_BY_GRADE[g]);")
    js_lines.append("    }")
    js_lines.append("  }")
    js_lines.append("  return result;")
    js_lines.append("}")
    js_lines.append("")
    js_lines.append("// Helper: get character count for a grade")
    js_lines.append("function getGradeCharCount(grade) {")
    js_lines.append("  return CHARACTERS_BY_GRADE[grade] ? CHARACTERS_BY_GRADE[grade].length : 0;")
    js_lines.append("}")
    js_lines.append("")

    # Write file
    output = "\n".join(js_lines)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\n{'=' * 60}")
    print(f"Done! Generated {OUTPUT_FILE}")
    print(f"  Total characters: {total_chars}")
    print(f"  Missing pinyin/meaning: {missing}")
    for g in sorted(grades.keys()):
        print(f"  Grade {g}: {len(grades[g])} characters")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
