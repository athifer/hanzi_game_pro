#!/usr/bin/env python3
"""
Generate web/js/characters.js from official Chinese character data.

Uses:
- hanziDB dataset (based on Jun Da's frequency list) for frequency rank, stroke count,
  pinyin, definitions, and 通用规范汉字表 (general_standard_num)
- CC-CEDICT dictionary for mining common 2-4 character phrases per character
- Characters are sorted by frequency rank (most common first) with stroke count
  as a secondary criterion (simpler characters first among same frequency tier)

Grade distribution (8 grades, ~3500 chars from 通用规范汉字表 Level 1):
  Grade 1: 350 chars  (most frequent / simplest)
  Grade 2: 400 chars
  Grade 3: 425 chars
  Grade 4: 425 chars
  Grade 5: 450 chars
  Grade 6: 475 chars
  Grade 7: 475 chars
  Grade 8: 500 chars
  Total:  3500 chars
"""

import csv
import gzip
import io
import json
import os
import re
import ssl
import urllib.request

# Fix SSL for macOS Python
ssl._create_default_https_context = ssl._create_unverified_context

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_FILE = os.path.join(PROJECT_DIR, "web", "js", "characters.js")

HANZI_DB_URL = "https://raw.githubusercontent.com/ruddfawcett/hanziDB.csv/master/hanzi_db.csv"

# Grade distribution: maps grade -> number of characters
GRADE_SIZES = {1: 350, 2: 400, 3: 425, 4: 425, 5: 450, 6: 475, 7: 475, 8: 500}

NUM_GRADES = 8

# ── Download helpers ──

def download(url, desc=""):
    """Download URL content as string."""
    print(f"  Downloading {desc or url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


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
        if syl[-1].isdigit():
            tone = int(syl[-1])
            syl = syl[:-1]
        else:
            return syl
        if tone == 5 or tone == 0:
            return syl
        if tone < 1 or tone > 4:  # guard against malformed tone digits
            return syl
        syl = syl.replace("u:", "ü").replace("U:", "Ü")
        vowels = 'aeiouüAEIOUÜ'
        if 'a' in syl.lower():
            for i, c in enumerate(syl):
                if c.lower() == 'a':
                    marked = tone_marks.get(c.lower(), [c]*4)[tone-1]
                    return syl[:i] + (marked.upper() if c.isupper() else marked) + syl[i+1:]
        elif 'e' in syl.lower():
            for i, c in enumerate(syl):
                if c.lower() == 'e':
                    marked = tone_marks.get(c.lower(), [c]*4)[tone-1]
                    return syl[:i] + (marked.upper() if c.isupper() else marked) + syl[i+1:]
        elif 'ou' in syl.lower():
            for i, c in enumerate(syl):
                if c.lower() == 'o':
                    marked = tone_marks.get(c.lower(), [c]*4)[tone-1]
                    return syl[:i] + (marked.upper() if c.isupper() else marked) + syl[i+1:]
        else:
            for i in range(len(syl)-1, -1, -1):
                if syl[i].lower() in vowels:
                    base = syl[i].lower()
                    if base == 'v':
                        base = 'ü'
                    marked = tone_marks.get(base, [base]*4)[tone-1]
                    return syl[:i] + (marked.upper() if syl[i].isupper() else marked) + syl[i+1:]
        return syl

    parts = pinyin_str.split()
    return " ".join(convert_syllable(p) for p in parts)


def escape_js_string(text):
    """Escape text for safe embedding in double-quoted JavaScript strings."""
    if text is None:
        return ""
    text = str(text)
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    return text


def download_hanzi_db():
    """
    Download hanziDB.csv and return list of dicts for 通用规范汉字表 Level 1 chars.
    Each dict: {char, pinyin, meaning, frequency_rank, stroke_count, general_standard_num}
    """
    raw = download(HANZI_DB_URL, "hanziDB.csv (frequency + stroke count + definitions)")
    reader = csv.DictReader(io.StringIO(raw))

    entries = {}  # char -> dict (keep first/best entry per character)
    for row in reader:
        char = row.get("character", "").strip()
        if not char or len(char) != 1:
            continue
        if not ('\u4e00' <= char <= '\u9fff'):
            continue

        # Parse general_standard_num to identify Level 1 (1-3500)
        gsn_str = row.get("general_standard_num", "").strip()
        gsn = int(gsn_str) if gsn_str.isdigit() else 0

        freq_str = row.get("frequency_rank", "").strip()
        freq_rank = int(freq_str) if freq_str.isdigit() else 99999

        stroke_str = row.get("stroke_count", "").strip()
        stroke_count = int(stroke_str) if stroke_str.isdigit() else 99

        pinyin_raw = row.get("pinyin", "").strip()
        definition = row.get("definition", "").strip()

        # Convert pinyin (hanziDB uses tone-marked pinyin already, but handle both)
        # Check if it has numbered tones
        if re.search(r'[a-zA-ZüÜ][1-5]', pinyin_raw):
            pinyin = convert_pinyin_numbers(pinyin_raw)
        else:
            pinyin = pinyin_raw

        # Clean up definition
        if definition:
            # Take first meaning if semicolon-separated
            parts = definition.split(";")
            definition = parts[0].strip()
            if len(definition) > 50:
                definition = definition[:47] + "..."
        else:
            definition = "(no definition)"

        entry = {
            "char": char,
            "pinyin": pinyin or "?",
            "meaning": definition,
            "frequency_rank": freq_rank,
            "stroke_count": stroke_count,
            "general_standard_num": gsn,
        }

        # Keep entry with better (lower) general_standard_num, or first occurrence
        if char not in entries:
            entries[char] = entry
        else:
            # Prefer entry that has a valid general_standard_num
            existing = entries[char]
            if gsn > 0 and (existing["general_standard_num"] == 0 or gsn < existing["general_standard_num"]):
                entries[char] = entry

    return entries


CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
MAKEMEAHANZI_URL = "https://raw.githubusercontent.com/skishore/makemeahanzi/master/dictionary.txt"
JIEBA_DICT_URL = "https://raw.githubusercontent.com/fxsjy/jieba/master/jieba/dict.txt"


def download_cedict():
    """Download and parse CC-CEDICT. Returns list of (simplified, pinyin, english) tuples."""
    print("  Downloading CC-CEDICT...")
    req = urllib.request.Request(CEDICT_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = gzip.decompress(resp.read()).decode("utf-8", errors="replace")

    entries = []
    for line in data.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        m = re.match(r"(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+/(.+)/", line)
        if not m:
            continue
        _trad, simp, pinyin_raw, meaning = m.groups()
        entries.append((simp, pinyin_raw, meaning))
    print(f"  CC-CEDICT: {len(entries)} total entries")
    return entries


def download_makemeahanzi():
    """Download Make Me a Hanzi dictionary. Returns dict: char -> etymology dict."""
    data = download(MAKEMEAHANZI_URL, "Make Me a Hanzi dictionary (etymology data)")
    etym_map = {}
    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        ch = d.get("character", "")
        if len(ch) == 1 and '\u4e00' <= ch <= '\u9fff':
            etym_map[ch] = {
                "etymology": d.get("etymology", {}),
                "decomposition": d.get("decomposition", ""),
                "radical": d.get("radical", ""),
            }
    print(f"  Loaded etymology data for {len(etym_map)} characters")
    return etym_map


def build_memory_hint(char, etym_data):
    """Build a memory hint sentence from Make Me a Hanzi etymology data."""
    if char not in etym_data:
        return ""
    info = etym_data[char]
    etym = info.get("etymology", {})
    hint = etym.get("hint", "")
    etype = etym.get("type", "")
    if not hint:
        return ""

    # Format based on etymology type
    if etype == "pictographic":
        return f"Pictograph: {hint}"
    elif etype == "ideographic":
        return hint[0].upper() + hint[1:] if hint else ""
    elif etype == "pictophonetic":
        semantic = etym.get("semantic", "")
        phonetic = etym.get("phonetic", "")
        parts = []
        if semantic and hint:
            parts.append(f"{semantic} ({hint}) for meaning")
        elif hint:
            parts.append(f"meaning: {hint}")
        if phonetic:
            parts.append(f"{phonetic} for sound")
        if parts:
            return "; ".join(parts)
        return hint
    else:
        return hint


def download_word_frequency():
    """Download jieba's word frequency dict. Returns dict: word -> frequency count."""
    data = download(JIEBA_DICT_URL, "jieba word frequency dict (337k words)")
    word_freq = {}
    for line in data.splitlines():
        parts = line.strip().split(" ")
        if len(parts) >= 2:
            word = parts[0]
            try:
                freq = int(parts[1])
            except ValueError:
                continue
            if len(word) >= 2 and all('\u4e00' <= c <= '\u9fff' for c in word):
                word_freq[word] = freq
    print(f"  Loaded {len(word_freq)} multi-char Chinese word frequencies")
    return word_freq


def mine_phrases(cedict_entries, char_set, char_to_grade, word_freq, max_per_char=3):
    """
    For each character in char_set, find the most common 2-4 character compound
    words from CC-CEDICT, scored by real word frequency (from jieba dict).

    Filters:
    - All constituent characters must be in our char_set
    - Skips proper nouns (place names, person names) where possible
    - Prefers high-frequency everyday words

    Returns dict: char -> list of {zh, pinyin, en}
    """
    # Build candidates per character
    candidates = {}  # char -> list of dicts

    for simp, pinyin_raw, meaning in cedict_entries:
        word_len = len(simp)
        if word_len < 2 or word_len > 4:
            continue
        # All characters must be CJK and in our char_set
        if not all('\u4e00' <= c <= '\u9fff' and c in char_set for c in simp):
            continue

        # Convert pinyin
        pinyin = convert_pinyin_numbers(pinyin_raw)

        # Clean up meaning - take first definition, skip variants/references/classifiers
        meanings = meaning.split("/")
        clean = []
        for mg in meanings:
            mg = mg.strip()
            if not mg:
                continue
            if mg.startswith("variant of") or mg.startswith("old variant"):
                continue
            if mg.startswith("see ") and "[" in mg:
                continue
            if mg.startswith("CL:"):
                continue
            clean.append(mg)
        if not clean:
            continue
        best_meaning = clean[0]

        # Skip entries that are likely proper nouns / place names / person names
        # (pinyin starts with uppercase = proper noun in CEDICT convention)
        pinyin_syllables = pinyin_raw.strip().split()
        is_proper = all(s[0].isupper() for s in pinyin_syllables if s and s[0].isalpha())
        if is_proper and word_len >= 2:
            # Allow some common proper-noun-ish words through if very high frequency
            freq = word_freq.get(simp, 0)
            if freq < 5000:  # skip low-freq proper nouns
                continue

        if len(best_meaning) > 40:
            best_meaning = best_meaning[:37] + "..."

        # Score by real word frequency (higher = more common = better)
        freq = word_freq.get(simp, 0)
        max_grade = max(char_to_grade.get(c, 99) for c in simp)

        for ch in simp:
            if ch not in candidates:
                candidates[ch] = []
            candidates[ch].append({
                "zh": simp,
                "pinyin": pinyin,
                "en": best_meaning,
                "freq": freq,
                "max_grade": max_grade,
            })

    # For each character, pick the best phrases by frequency
    result = {}
    for ch in char_set:
        if ch not in candidates:
            result[ch] = []
            continue

        # Sort by frequency descending (most common first), deduplicate
        sorted_cands = sorted(candidates[ch], key=lambda x: -x["freq"])
        seen = set()
        unique = []
        for p in sorted_cands:
            if p["zh"] not in seen:
                seen.add(p["zh"])
                unique.append(p)

        # Prefer phrases where all chars are from same or lower grade
        this_grade = char_to_grade.get(ch, 99)
        appropriate = [p for p in unique if p["max_grade"] <= this_grade]

        # Pick from grade-appropriate first (by freq), then fill from all
        picked = []
        for p in appropriate:
            if len(picked) >= max_per_char:
                break
            picked.append(p)
        if len(picked) < max_per_char:
            for p in unique:
                if p["zh"] not in {x["zh"] for x in picked}:
                    picked.append(p)
                    if len(picked) >= max_per_char:
                        break

        result[ch] = [{"zh": p["zh"], "pinyin": p["pinyin"], "en": p["en"]} for p in picked]

    return result


# ── Main generation ──

def main():
    print("=" * 60)
    print("Generating characters.js (8 grades, frequency-ordered)")
    print("=" * 60)

    # 1. Download hanziDB
    print("\n1. Downloading hanziDB dataset...")
    all_entries = download_hanzi_db()
    print(f"   Total entries loaded: {len(all_entries)}")

    # 2. Filter to 通用规范汉字表 Level 1 (general_standard_num 1-3500)
    level1 = {ch: e for ch, e in all_entries.items() if 1 <= e["general_standard_num"] <= 3500}
    print(f"\n2. 通用规范汉字表 Level 1 characters: {len(level1)}")

    if len(level1) < 3000:
        print(f"   WARNING: Only found {len(level1)} Level 1 chars; expected ~3500")
        print("   Supplementing with highest-frequency chars not in Level 1...")
        # Add the most frequent chars that aren't already included
        remaining = {ch: e for ch, e in all_entries.items() if ch not in level1}
        by_freq = sorted(remaining.values(), key=lambda e: e["frequency_rank"])
        for entry in by_freq:
            if len(level1) >= 3500:
                break
            level1[entry["char"]] = entry

    # 3. Sort by frequency rank (primary), stroke count (secondary)
    print("\n3. Sorting by frequency (primary) and stroke count (secondary)...")
    chars_sorted = sorted(
        level1.values(),
        key=lambda e: (e["frequency_rank"], e["stroke_count"])
    )

    # Cap at 3500
    if len(chars_sorted) > 3500:
        chars_sorted = chars_sorted[:3500]

    print(f"   Total characters to assign: {len(chars_sorted)}")
    print(f"   Most frequent: {''.join(e['char'] for e in chars_sorted[:30])}")
    print(f"   Least frequent: {''.join(e['char'] for e in chars_sorted[-30:])}")

    # Show frequency rank range and avg stroke count for verification
    freq_ranks = [e["frequency_rank"] for e in chars_sorted]
    strokes = [e["stroke_count"] for e in chars_sorted]
    print(f"   Frequency rank range: {min(freq_ranks)} - {max(freq_ranks)}")
    print(f"   Stroke count range: {min(strokes)} - {max(strokes)}")

    # 4. Split into grades
    print(f"\n4. Splitting into {NUM_GRADES} grades...")
    grades = {}
    idx = 0
    for grade, size in GRADE_SIZES.items():
        end = min(idx + size, len(chars_sorted))
        grades[grade] = chars_sorted[idx:end]
        idx = end
        avg_freq = sum(e["frequency_rank"] for e in grades[grade]) / len(grades[grade])
        avg_strk = sum(e["stroke_count"] for e in grades[grade]) / len(grades[grade])
        sample = ''.join(e['char'] for e in grades[grade][:15])
        print(f"   Grade {grade}: {len(grades[grade]):>4} chars | "
              f"avg freq rank: {avg_freq:>6.0f} | avg strokes: {avg_strk:.1f} | "
              f"sample: {sample}...")

    # 5. Download CC-CEDICT and mine phrases
    print(f"\n5. Downloading CC-CEDICT for phrase mining...")
    cedict_entries = download_cedict()

    # 5.5. Download word frequency data
    print(f"\n5.5. Downloading word frequency data...")
    word_freq = download_word_frequency()

    # 5.6. Download etymology data for memory hints
    print(f"\n5.6. Downloading etymology data for memory hints...")
    etym_data = download_makemeahanzi()

    # Build char_set and char_to_grade lookup
    char_set = set()
    char_to_grade = {}
    for grade in sorted(grades.keys()):
        for entry in grades[grade]:
            char_set.add(entry["char"])
            char_to_grade[entry["char"]] = grade

    print(f"   Mining phrases for {len(char_set)} characters...")
    phrases = mine_phrases(cedict_entries, char_set, char_to_grade, word_freq, max_per_char=3)

    with_phrases = sum(1 for ch in char_set if phrases.get(ch))
    total_phrases = sum(len(v) for v in phrases.values())
    print(f"   Characters with phrases: {with_phrases}/{len(char_set)}")
    print(f"   Total phrases mined: {total_phrases}")

    # Build memory hints
    hints = {}
    for ch in char_set:
        hints[ch] = build_memory_hint(ch, etym_data)
    with_hints = sum(1 for h in hints.values() if h)
    print(f"   Characters with memory hints: {with_hints}/{len(char_set)}")

    # 6. Build JavaScript output
    print(f"\n6. Generating characters.js...")
    missing = 0
    total_chars = 0

    js_lines = []
    js_lines.append("/**")
    js_lines.append(f" * Chinese Characters Dataset organized by grade level (1-{NUM_GRADES})")
    js_lines.append(" * Based on 通用规范汉字表 (Table of General Standard Chinese Characters) Level 1: 3500 常用字")
    js_lines.append(" * Characters sorted by frequency rank (Jun Da's Modern Chinese Character Frequency List)")
    js_lines.append(" * with stroke count as secondary sort (simpler characters first).")
    js_lines.append(" * Phrases mined from CC-CEDICT (2-4 char compounds using chars from same/lower grade).")
    js_lines.append(" * Memory hints from Make Me a Hanzi etymology data.")
    js_lines.append(" * Data sources: hanziDB.csv + CC-CEDICT + Make Me a Hanzi")
    js_lines.append(" * Auto-generated by scripts/generate_characters_js.py")
    js_lines.append(" */")
    js_lines.append("")
    js_lines.append("const CHARACTERS_BY_GRADE = {")

    for grade in sorted(grades.keys()):
        js_lines.append(f"")
        js_lines.append(f"  {grade}: [")
        for entry in grades[grade]:
            total_chars += 1
            ch = entry["char"]
            pinyin = entry["pinyin"]
            meaning = entry["meaning"]
            if meaning == "(no definition)" or pinyin == "?":
                missing += 1
            meaning_esc = escape_js_string(meaning)
            pinyin_esc = escape_js_string(pinyin)

            # Build phrases array
            char_phrases = phrases.get(ch, [])
            ph_parts = []
            if char_phrases:
                for p in char_phrases:
                    pzh = escape_js_string(p["zh"])
                    ppy = escape_js_string(p["pinyin"])
                    pen = escape_js_string(p["en"])
                    ph_parts.append(f'{{zh:"{pzh}",py:"{ppy}",en:"{pen}"}}')
            phrases_str = "[" + ",".join(ph_parts) + "]"

            # Build hint
            hint = hints.get(ch, "")
            hint_esc = escape_js_string(hint)

            js_lines.append(f'    {{ char: "{ch}", pinyin: "{pinyin_esc}", meaning: "{meaning_esc}", hint: "{hint_esc}", phrases: {phrases_str} }},')
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
    print(f"  Characters with phrases: {with_phrases}/{total_chars}")
    print(f"  Total phrases: {total_phrases}")
    print(f"  Characters with memory hints: {with_hints}/{total_chars}")
    for g in sorted(grades.keys()):
        print(f"  Grade {g}: {len(grades[g])} characters")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
