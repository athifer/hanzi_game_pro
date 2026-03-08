# 汉字大冒险 — Chinese Character Adventure

An interactive web-based game for kids in **grades 1–9** to learn and practice Chinese characters (汉字). No installation required — just open a file in your browser.

![Grade Selection](https://img.shields.io/badge/Grades-1--9-6C63FF) ![Characters](https://img.shields.io/badge/Characters-540+-FF6584) ![Modes](https://img.shields.io/badge/Game%20Modes-4-43E97B) ![No Dependencies](https://img.shields.io/badge/Dependencies-None-FFD700)

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

Select a grade level from 1 to 9. Each grade has ~60 characters matched to the standard Chinese education curriculum:

| Grade | Theme | Example Characters |
|-------|-------|--------------------|
| **1** | Numbers, nature, basic words | 一 二 三 人 大 小 山 水 |
| **2** | Seasons, colors, family, verbs | 春 夏 红 蓝 爸 妈 吃 喝 |
| **3** | School, body, food, actions | 语 文 教 习 头 脸 饭 菜 |
| **4** | Places, animals, daily life | 城 河 猫 狗 龙 虎 买 卖 |
| **5** | Country, sports, movement | 国 民 球 游 推 拉 请 谢 |
| **6** | Emotions, senses, adjectives | 感 觉 甜 苦 冷 热 难 易 |
| **7** | Society, economy, environment | 政 法 商 钱 环 保 研 究 |
| **8** | History, literature, mythology | 古 朝 诗 词 神 仙 智 慧 |
| **9** | Abstract thinking, systems | 哲 逻 变 化 创 技 系 统 |

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
hanzi_game_repo_pro/
├── README.md
├── scripts/
│   └── build_datasets.py      # Downloads & builds CSV datasets (optional)
└── web/
    ├── index.html              # Main game page — open this!
    └── js/
        ├── characters.js       # 540 characters organized by grade 1-9
        └── game.js             # Game engine: all 4 modes, scoring, UI
```

### Character Data

The game ships with **540 built-in characters** in `web/js/characters.js` — no CSV download needed. Each character includes:

```javascript
{ char: "山", pinyin: "shān", meaning: "mountain" }
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
