# 汉字大冒险 — Chinese Character Adventure

An interactive web-based game for kids in **grades 1–8** to learn and practice Chinese characters (汉字). Covers **~3,500 commonly used characters** from the 通用规范汉字表 (Table of General Standard Chinese Characters), sorted by frequency. No installation required — just open a file in your browser.

![Grade Selection](https://img.shields.io/badge/Grades-1--8-6C63FF) ![Characters](https://img.shields.io/badge/Characters-3500-FF6584) ![Modes](https://img.shields.io/badge/Game%20Modes-4-43E97B) ![No Dependencies](https://img.shields.io/badge/Dependencies-None-FFD700)

---

## How to Run

### Option A: Open directly (simplest)

Double-click or open this file in any modern browser:

```
web/index.html
```

> **Note:** The Writing mode canvas works best when served via HTTP (Option B).

### Option B: Local HTTP server (recommended)

```bash
cd web
python3 -m http.server 8765
```

Then open **http://localhost:8765** in your browser.

### Option C: Any static file server

```bash
# Node.js
npx serve web

# PHP
php -S localhost:8765 -t web
```

**Requirements:** Any modern browser (Chrome, Firefox, Safari, Edge). No build step, no npm install, no frameworks — pure HTML/CSS/JS.

---

## How to Play

### 1. Choose a Grade (年级)

Select a grade level from 1 to 8. Characters are drawn from the 通用规范汉字表 Level 1 (~3,500 common characters), sorted by usage frequency (Jun Da's Modern Chinese Character Frequency List) with stroke count as secondary sort. Simpler, more common characters appear in lower grades; rarer, more complex characters in higher grades.

| Grade | Characters | Avg Freq Rank | Avg Strokes | Description |
|-------|-----------|---------------|-------------|-------------|
| **1** | 350 | ~176 | ~6.9 | Most frequently used characters |
| **2** | 400 | ~550 | ~8.4 | High-frequency characters |
| **3** | 425 | ~963 | ~9.0 | Upper-mid frequency characters |
| **4** | 425 | ~1389 | ~9.7 | Mid-frequency characters |
| **5** | 450 | ~1828 | ~10.0 | Lower-mid frequency characters |
| **6** | 475 | ~2305 | ~10.5 | Less common characters |
| **7** | 475 | ~2821 | ~10.9 | Uncommon characters |
| **8** | 500 | ~3614 | ~11.4 | Least common standard characters |

### 2. Pick a Game Mode (游戏模式)

| Mode | Icon | Description |
|------|------|-------------|
| **Flashcards** | 🃏 | See a character → tap to flip and reveal pinyin & meaning → mark "Know It" or "Don't Know." Missed characters repeat at the end for reinforcement. |
| **Quiz** | ❓ | Multiple-choice questions. Alternates between "What does it mean?" and "What is the pinyin?" — 4 options each round. |
| **Memory Match** | 🧩 | A 12-card memory game. Flip cards to match each character with its pinyin. Fewest moves wins! |
| **Writing** | ✍️ | Practice writing characters on a drawing canvas with guide grid lines and a ghost overlay you can show/hide for tracing. |

### 3. Play & Score

- **⭐ Points** — Earn points for correct answers (10–20 per character depending on mode).
- **🔥 Streak** — Build combos by answering correctly in a row. Milestone popups appear at 5x, 10x, 15x…
- **🏆 Results** — After each round, see your score, accuracy %, best streak, and an achievement trophy (🥉 → 🥈 → 🥇 → 🏆).
- **🔊 Sound** — Toggle sound effects on/off with the speaker button in the top-right corner.

---

## Project Structure

```
hanzi_game_pro/
├── README.md
├── characters_by_grade.html        # Printable character reference (open → Print → PDF)
├── scripts/
│   ├── build_datasets.py           # Downloads & builds CSV datasets (optional)
│   ├── generate_characters_js.py   # Regenerate web/js/characters.js from source data
│   └── generate_characters_pdf.py  # Generate the printable character HTML page
└── web/
    ├── index.html                  # Main game page — open this!
    └── js/
        ├── characters.js           # ~3,500 characters organized by grades 1-8
        └── game.js                 # Game engine: all 4 modes, scoring, UI
```

### Character Data

The game ships with **~3,500 built-in characters** in `web/js/characters.js` — no CSV download needed. Characters are sourced from the **通用规范汉字表** Level 1, enriched with pinyin and English meanings from **hanziDB** (based on Jun Da's frequency list and CC-CEDICT). Characters are sorted by **frequency rank** (most common first) with **stroke count** as a tiebreaker (simpler first), then split into 8 progressive grades. Each character entry looks like:

```javascript
{ char: "山", pinyin: "shān", meaning: "mountain" }
```

To regenerate the character data from scratch:

```bash
python3 scripts/generate_characters_js.py
```

To generate a printable HTML reference of all characters by grade:

```bash
python3 scripts/generate_characters_pdf.py
# Then open characters_by_grade.html in a browser and Print → Save as PDF
```

### Optional: Build Extended Datasets

For advanced use (e.g., building word-level or sentence-level games), you can download larger datasets:

```bash
pip install pandas requests tqdm
python scripts/build_datasets.py
```

This creates:

```
data/
  characters_3500.csv    # 3,500 common characters
  words_frequency.csv    # ~50k words from CC-CEDICT
  sentences_basic.csv    # 50k Chinese sentences from Tatoeba
```

---

## Features

- **No dependencies** — Pure HTML, CSS, and JavaScript. No build tools or npm.
- **Works offline** — All character data is embedded. No network requests needed.
- **Responsive** — Works on desktop, tablet, and phone screens.
- **Kid-friendly UI** — Colorful animated design with emoji, confetti, and sound effects.
- **Progress saving** — Best scores saved to localStorage per grade and mode.
- **Bilingual** — Interface labels are in both English and Chinese.

## Datasets Used (for `build_datasets.py`)

| Dataset | Description |
|---------|-------------|
| **通用规范汉字表** | Official 3,500 commonly used characters |
| **CC-CEDICT** | Open Chinese-English dictionary (~120k words) |
| **SUBTLEX-CH** | Word frequencies from film subtitles |
| **Tatoeba** | Large corpus of Chinese example sentences |

---

## Ideas for Extension

- Add stroke-order animation to the Writing mode
- Build a word-building mode (combine characters into words)
- Sentence ordering / fill-in-the-blank with Tatoeba data
- Spaced repetition scheduling (track which characters need review)
- Story RPG literacy quests
- Multiplayer / classroom leaderboard
- Text-to-speech pronunciation

---

*Designed for hacking together literacy games with kids. 一起学汉字！*
