
/**
 * 汉字大冒险 - Chinese Character Adventure Game
 * Main game logic for all four game modes.
 */

// ===== Global State =====
const state = {
  selectedGrade: null,
  selectedMode: null,
  characters: [],     // characters for the current session
  score: 0,
  streak: 0,
  bestStreak: 0,
  correct: 0,
  total: 0,
  soundOn: true,
};

const ROUND_SIZE = 15; // characters per round for flashcard/quiz/writing

// ===== Audio (Web Audio API beeps) =====
const AudioCtx = window.AudioContext || window.webkitAudioContext;
let audioCtx = null;

function getAudioCtx() {
  if (!audioCtx) audioCtx = new AudioCtx();
  return audioCtx;
}

function playTone(freq, duration, type = 'sine') {
  if (!state.soundOn) return;
  try {
    const ctx = getAudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    gain.gain.value = 0.12;
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  } catch (e) { /* ignore audio errors */ }
}

function playCorrect() { playTone(523, 0.15); setTimeout(() => playTone(659, 0.15), 100); setTimeout(() => playTone(784, 0.2), 200); }
function playWrong() { playTone(200, 0.3, 'square'); }
function playFlip() { playTone(440, 0.08); }
function playMatch() { playTone(660, 0.1); setTimeout(() => playTone(880, 0.15), 80); setTimeout(() => playTone(1047, 0.2), 160); }
function playComplete() { playTone(523, 0.1); setTimeout(() => playTone(659, 0.1), 100); setTimeout(() => playTone(784, 0.1), 200); setTimeout(() => playTone(1047, 0.3), 300); }

// Sound toggle
document.getElementById('soundToggle').addEventListener('click', () => {
  state.soundOn = !state.soundOn;
  document.getElementById('soundToggle').textContent = state.soundOn ? '🔊' : '🔇';
});

// ===== Utility =====
function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function pickRandom(arr, n) {
  return shuffle(arr).slice(0, n);
}

function updateScore() {
  document.getElementById('scoreValue').textContent = state.score;
  document.getElementById('streakValue').textContent = state.streak;
}

function addScore(points) {
  state.score += points;
  state.streak++;
  if (state.streak > state.bestStreak) state.bestStreak = state.streak;
  state.correct++;
  state.total++;
  updateScore();

  // Streak milestones
  if (state.streak > 0 && state.streak % 5 === 0) {
    showStreakPopup(`🔥 ${state.streak}x Streak!`);
  }
}

function resetStreak() {
  state.streak = 0;
  state.total++;
  updateScore();
}

function showStreakPopup(text) {
  const el = document.getElementById('streakPopup');
  el.textContent = text;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 1200);
}

// ===== Confetti =====
function launchConfetti() {
  const container = document.getElementById('confettiContainer');
  const colors = ['#6C63FF', '#FF6584', '#43E97B', '#FFD700', '#FF9A76', '#00B4D8'];
  for (let i = 0; i < 60; i++) {
    const piece = document.createElement('div');
    piece.className = 'confetti-piece';
    piece.style.left = Math.random() * 100 + '%';
    piece.style.background = colors[Math.floor(Math.random() * colors.length)];
    piece.style.animationDelay = Math.random() * 1.5 + 's';
    piece.style.animationDuration = (2 + Math.random() * 2) + 's';
    piece.style.width = (6 + Math.random() * 8) + 'px';
    piece.style.height = (6 + Math.random() * 8) + 'px';
    piece.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
    container.appendChild(piece);
  }
  setTimeout(() => { container.innerHTML = ''; }, 4000);
}

// ===== Screen Management =====
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const target = document.getElementById(id);
  if (target) target.classList.add('active');
}

function goHome() {
  document.getElementById('homeContainer').style.display = '';
  document.getElementById('gameContainer').style.display = 'none';
  showScreen('homeScreen');
  // Reset selections visual
  state.selectedGrade = null;
  state.selectedMode = null;
  document.querySelectorAll('.grade-btn').forEach(b => b.classList.remove('selected'));
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('selected'));
  document.getElementById('startBtn').classList.remove('ready');
}

// ===== Home Screen Initialization =====
function initHome() {
  const grid = document.getElementById('gradeGrid');
  grid.innerHTML = '';
  for (let g = 1; g <= 8; g++) {
    const count = getGradeCharCount(g);
    const btn = document.createElement('button');
    btn.className = 'grade-btn';
    btn.dataset.grade = g;
    btn.innerHTML = `<span class="grade-label">${g}年级</span><span class="grade-count">${count} chars</span>`;
    btn.addEventListener('click', () => selectGrade(g));
    grid.appendChild(btn);
  }
}

function selectGrade(grade) {
  state.selectedGrade = grade;
  document.querySelectorAll('.grade-btn').forEach(b => {
    b.classList.toggle('selected', parseInt(b.dataset.grade) === grade);
  });
  checkReady();
}

function selectMode(mode) {
  state.selectedMode = mode;
  document.querySelectorAll('.mode-btn').forEach(b => {
    b.classList.toggle('selected', b.dataset.mode === mode);
  });
  checkReady();
}

function checkReady() {
  const ready = state.selectedGrade && state.selectedMode;
  document.getElementById('startBtn').classList.toggle('ready', !!ready);
}

function startGame() {
  if (!state.selectedGrade || !state.selectedMode) return;

  // Reset game state
  state.score = 0;
  state.streak = 0;
  state.bestStreak = 0;
  state.correct = 0;
  state.total = 0;
  updateScore();

  // Get characters for selected grade
  const allChars = CHARACTERS_BY_GRADE[state.selectedGrade] || [];
  state.characters = shuffle(allChars);

  // Switch to game screen
  document.getElementById('homeContainer').style.display = 'none';
  document.getElementById('gameContainer').style.display = '';

  const modeNames = {
    flashcard: '🃏 Flashcards · Grade ' + state.selectedGrade,
    quiz: '❓ Quiz · Grade ' + state.selectedGrade,
    match: '🧩 Memory Match · Grade ' + state.selectedGrade,
    writing: '✍️ Writing · Grade ' + state.selectedGrade,
    phrases: '📝 Phrase Builder · Grade ' + state.selectedGrade,
  };
  document.getElementById('gameTitle').textContent = modeNames[state.selectedMode] || '';

  // Launch the appropriate mode
  switch (state.selectedMode) {
    case 'flashcard': initFlashcard(); break;
    case 'quiz': initQuiz(); break;
    case 'match': initMatch(); break;
    case 'writing': initWriting(); break;
    case 'phrases': initPhrases(); break;
  }
}

function replay() {
  startGame();
}

// =============================================
// ===== FLASHCARD MODE =====
// =============================================
let fcState = { chars: [], index: 0, known: 0 };

function initFlashcard() {
  showScreen('flashcardScreen');
  fcState.chars = state.characters.slice(0, ROUND_SIZE);
  fcState.index = 0;
  fcState.known = 0;
  showFlashcard();
}

function showFlashcard() {
  if (fcState.index >= fcState.chars.length) {
    // Round complete
    finishGame();
    return;
  }
  const c = fcState.chars[fcState.index];
  document.getElementById('fcChar').textContent = c.char;
  document.getElementById('fcCharBack').textContent = c.char;
  document.getElementById('fcPinyin').textContent = c.pinyin;
  document.getElementById('fcMeaning').textContent = c.meaning;

  // Show phrases on back of card
  const phrasesEl = document.getElementById('fcPhrases');
  phrasesEl.innerHTML = '';
  if (c.phrases && c.phrases.length > 0) {
    c.phrases.forEach(p => {
      const div = document.createElement('div');
      div.className = 'phrase-item';
      div.innerHTML = `<span class="phrase-zh">${p.zh}</span> <span class="phrase-py">${p.py}</span> <span class="phrase-en">${p.en}</span>`;
      phrasesEl.appendChild(div);
    });
  }

  document.getElementById('flashcard').classList.remove('flipped');

  const pct = (fcState.index / fcState.chars.length) * 100;
  document.getElementById('fcProgress').style.width = pct + '%';
}

function flipCard() {
  document.getElementById('flashcard').classList.toggle('flipped');
  playFlip();
}

function fcKnow() {
  fcState.known++;
  addScore(10);
  playCorrect();
  fcState.index++;
  showFlashcard();
}

function fcDontKnow() {
  resetStreak();
  // Move to end for review
  fcState.chars.push(fcState.chars[fcState.index]);
  fcState.index++;
  showFlashcard();
}

// =============================================
// ===== QUIZ MODE =====
// =============================================
let quizState = { chars: [], index: 0, questionType: 'meaning', answered: false };

function initQuiz() {
  showScreen('quizScreen');
  quizState.chars = state.characters.slice(0, ROUND_SIZE);
  quizState.index = 0;
  quizState.answered = false;
  showQuizQuestion();
}

function showQuizQuestion() {
  if (quizState.index >= quizState.chars.length) {
    finishGame();
    return;
  }

  quizState.answered = false;
  const c = quizState.chars[quizState.index];

  // Alternate between meaning and pinyin questions
  quizState.questionType = quizState.index % 2 === 0 ? 'meaning' : 'pinyin';

  document.getElementById('quizChar').textContent = c.char;
  document.getElementById('quizFeedback').textContent = '';

  if (quizState.questionType === 'meaning') {
    document.getElementById('quizQuestion').textContent = 'What does this character mean? / 这个字是什么意思？';
  } else {
    document.getElementById('quizQuestion').textContent = 'What is the pinyin? / 拼音是什么？';
  }

  // Generate options
  const allChars = CHARACTERS_BY_GRADE[state.selectedGrade];
  const field = quizState.questionType; // 'meaning' or 'pinyin'
  const correctAnswer = c[field];

  // Get 3 wrong answers (different from correct)
  let wrongPool = allChars.filter(x => x[field] !== correctAnswer);
  let wrongs = pickRandom(wrongPool, 3).map(x => x[field]);

  // Deduplicate
  const uniqueWrongs = [...new Set(wrongs)].slice(0, 3);
  while (uniqueWrongs.length < 3) {
    const extra = wrongPool[Math.floor(Math.random() * wrongPool.length)];
    if (extra && !uniqueWrongs.includes(extra[field]) && extra[field] !== correctAnswer) {
      uniqueWrongs.push(extra[field]);
    }
  }

  const options = shuffle([correctAnswer, ...uniqueWrongs.slice(0, 3)]);

  const optionsEl = document.getElementById('quizOptions');
  optionsEl.innerHTML = '';
  options.forEach(opt => {
    const btn = document.createElement('button');
    btn.className = 'quiz-option';
    btn.textContent = opt;
    btn.addEventListener('click', () => handleQuizAnswer(btn, opt, correctAnswer));
    optionsEl.appendChild(btn);
  });

  const pct = (quizState.index / quizState.chars.length) * 100;
  document.getElementById('quizProgress').style.width = pct + '%';
}

function handleQuizAnswer(btn, selected, correct) {
  if (quizState.answered) return;
  quizState.answered = true;

  // Disable all buttons
  document.querySelectorAll('.quiz-option').forEach(b => b.classList.add('disabled'));

  if (selected === correct) {
    btn.classList.add('correct');
    addScore(15);
    playCorrect();
    document.getElementById('quizFeedback').textContent = '✅ Correct! 太棒了！';
    document.getElementById('quizFeedback').style.color = '#2E7D32';
  } else {
    btn.classList.add('wrong');
    // Highlight correct answer
    document.querySelectorAll('.quiz-option').forEach(b => {
      if (b.textContent === correct) b.classList.add('correct');
    });
    resetStreak();
    playWrong();
    document.getElementById('quizFeedback').textContent = `❌ The answer is: ${correct}`;
    document.getElementById('quizFeedback').style.color = '#C62828';
  }

  // Auto-advance after delay
  setTimeout(() => {
    quizState.index++;
    showQuizQuestion();
  }, 1500);
}

// =============================================
// ===== MEMORY MATCH MODE =====
// =============================================
let matchState = { cards: [], revealed: [], matched: 0, totalPairs: 0, moves: 0, busy: false };

function initMatch() {
  showScreen('matchScreen');

  const numPairs = 6; // 6 pairs = 12 cards
  const selected = pickRandom(state.characters, numPairs);

  // Create card pairs: character + pinyin
  let cards = [];
  selected.forEach((c, i) => {
    cards.push({ id: i, type: 'char', display: c.char, pairId: i });
    cards.push({ id: i, type: 'pinyin', display: c.pinyin, pairId: i });
  });
  cards = shuffle(cards);

  matchState = {
    cards,
    revealed: [],
    matched: 0,
    totalPairs: numPairs,
    moves: 0,
    busy: false,
  };

  document.getElementById('matchMoves').textContent = '0';
  document.getElementById('matchPairs').textContent = '0';
  document.getElementById('matchTotal').textContent = numPairs;

  const grid = document.getElementById('matchGrid');
  grid.innerHTML = '';
  grid.className = 'match-grid size-12';

  cards.forEach((card, idx) => {
    const el = document.createElement('div');
    el.className = 'match-card';
    el.dataset.index = idx;
    el.innerHTML = `
      <div class="match-card-inner">
        <div class="match-card-face front">?</div>
        <div class="match-card-face back">${card.display}</div>
      </div>
    `;
    el.addEventListener('click', () => handleMatchClick(idx, el));
    grid.appendChild(el);
  });
}

function handleMatchClick(idx, el) {
  if (matchState.busy) return;
  if (el.classList.contains('revealed') || el.classList.contains('matched')) return;

  el.classList.add('revealed');
  playFlip();
  matchState.revealed.push({ idx, el, card: matchState.cards[idx] });

  if (matchState.revealed.length === 2) {
    matchState.moves++;
    document.getElementById('matchMoves').textContent = matchState.moves;
    state.total++;

    const [a, b] = matchState.revealed;

    if (a.card.pairId === b.card.pairId && a.idx !== b.idx) {
      // Match found!
      matchState.busy = true;
      setTimeout(() => {
        a.el.classList.add('matched');
        b.el.classList.add('matched');
        matchState.matched++;
        state.correct++;
        addScore(20);
        playMatch();
        document.getElementById('matchPairs').textContent = matchState.matched;
        matchState.revealed = [];
        matchState.busy = false;

        if (matchState.matched === matchState.totalPairs) {
          setTimeout(() => finishGame(), 600);
        }
      }, 400);
    } else {
      // No match
      matchState.busy = true;
      setTimeout(() => {
        a.el.classList.remove('revealed');
        b.el.classList.remove('revealed');
        matchState.revealed = [];
        matchState.busy = false;
        resetStreak();
      }, 800);
    }
  }
}

// =============================================
// ===== WRITING MODE =====
// =============================================
let writeState = { chars: [], index: 0, ghostVisible: true };
let canvas, ctx;
let drawing = false;
let lastPos = null;

function initWriting() {
  showScreen('writingScreen');
  writeState.chars = state.characters.slice(0, ROUND_SIZE);
  writeState.index = 0;
  writeState.ghostVisible = true;

  canvas = document.getElementById('writingCanvas');
  ctx = canvas.getContext('2d');

  // Draw grid lines
  setupCanvas();

  // Setup canvas events
  canvas.removeEventListener('pointerdown', onPointerDown);
  canvas.removeEventListener('pointermove', onPointerMove);
  canvas.removeEventListener('pointerup', onPointerUp);
  canvas.removeEventListener('pointerleave', onPointerUp);

  canvas.addEventListener('pointerdown', onPointerDown);
  canvas.addEventListener('pointermove', onPointerMove);
  canvas.addEventListener('pointerup', onPointerUp);
  canvas.addEventListener('pointerleave', onPointerUp);

  showWritingChar();
}

function setupCanvas() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // Draw grid
  ctx.strokeStyle = '#E8E8E8';
  ctx.lineWidth = 1;
  ctx.setLineDash([5, 5]);
  // Vertical center
  ctx.beginPath();
  ctx.moveTo(canvas.width / 2, 0);
  ctx.lineTo(canvas.width / 2, canvas.height);
  ctx.stroke();
  // Horizontal center
  ctx.beginPath();
  ctx.moveTo(0, canvas.height / 2);
  ctx.lineTo(canvas.width, canvas.height / 2);
  ctx.stroke();
  // Diagonals
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(canvas.width, canvas.height);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(canvas.width, 0);
  ctx.lineTo(0, canvas.height);
  ctx.stroke();
  ctx.setLineDash([]);
}

function showWritingChar() {
  if (writeState.index >= writeState.chars.length) {
    finishGame();
    return;
  }
  const c = writeState.chars[writeState.index];
  document.getElementById('writeChar').textContent = c.char;
  document.getElementById('writePinyin').textContent = c.pinyin;
  document.getElementById('writeMeaning').textContent = c.meaning;
  document.getElementById('ghostChar').textContent = c.char;
  document.getElementById('ghostChar').style.opacity = writeState.ghostVisible ? '1' : '0';

  clearCanvas();

  const pct = (writeState.index / writeState.chars.length) * 100;
  document.getElementById('writeProgress').style.width = pct + '%';
}

function clearCanvas() {
  setupCanvas();
}

function toggleGhost() {
  writeState.ghostVisible = !writeState.ghostVisible;
  document.getElementById('ghostChar').style.opacity = writeState.ghostVisible ? '1' : '0';
}

function nextWritingChar() {
  addScore(10);
  playCorrect();
  writeState.index++;
  showWritingChar();
}

// Canvas drawing
function getCanvasPos(e) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: (e.clientX - rect.left) * (canvas.width / rect.width),
    y: (e.clientY - rect.top) * (canvas.height / rect.height)
  };
}

function onPointerDown(e) {
  e.preventDefault();
  drawing = true;
  lastPos = getCanvasPos(e);
}

function onPointerMove(e) {
  if (!drawing) return;
  e.preventDefault();
  const pos = getCanvasPos(e);
  ctx.strokeStyle = '#2D3436';
  ctx.lineWidth = 6;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(lastPos.x, lastPos.y);
  ctx.lineTo(pos.x, pos.y);
  ctx.stroke();
  lastPos = pos;
}

function onPointerUp(e) {
  drawing = false;
  lastPos = null;
}

// =============================================
// ===== PHRASE BUILDER MODE =====
// =============================================
let phraseState = { rounds: [], index: 0, answered: false, selectedSlots: [] };

function initPhrases() {
  showScreen('phrasesScreen');

  // Build rounds: for each character that has phrases, create a puzzle
  const charsWithPhrases = state.characters.filter(c => c.phrases && c.phrases.length > 0);
  const selected = charsWithPhrases.slice(0, ROUND_SIZE);
  const allChars = CHARACTERS_BY_GRADE[state.selectedGrade] || [];

  phraseState.rounds = selected.map(c => {
    // Pick a random phrase for this character
    const phrase = c.phrases[Math.floor(Math.random() * c.phrases.length)];
    const wordChars = [...phrase.zh]; // array of characters in the phrase

    // Find the position of the target character in the phrase
    const targetIdx = wordChars.indexOf(c.char);

    // The missing characters are all chars except the target
    const missingIndices = [];
    for (let i = 0; i < wordChars.length; i++) {
      if (i !== targetIdx) missingIndices.push(i);
    }
    const missingChars = missingIndices.map(i => wordChars[i]);

    // Generate distracting characters (wrong answers)
    // Pick chars from the same grade that are NOT in the phrase
    const phraseCharSet = new Set(wordChars);
    const distractorPool = allChars
      .filter(x => !phraseCharSet.has(x.char))
      .map(x => x.char);

    // We want enough distractors to fill a grid of choices
    // Total choices = missing chars + distractors, shown in a grid
    const numDistractors = Math.max(4, 8 - missingChars.length);
    const distractors = pickRandom(distractorPool, numDistractors);
    const allChoices = shuffle([...missingChars, ...distractors.slice(0, numDistractors)]);

    return {
      char: c,
      phrase: phrase,
      wordChars: wordChars,
      targetIdx: targetIdx,
      missingIndices: missingIndices,
      missingChars: missingChars,
      allChoices: allChoices,
    };
  });

  phraseState.index = 0;
  phraseState.answered = false;
  showPhraseRound();
}

function showPhraseRound() {
  if (phraseState.index >= phraseState.rounds.length) {
    finishGame();
    return;
  }

  const round = phraseState.rounds[phraseState.index];
  phraseState.answered = false;
  phraseState.selectedSlots = [];

  // Update progress
  const pct = (phraseState.index / phraseState.rounds.length) * 100;
  document.getElementById('phraseProgress').style.width = pct + '%';

  // Prompt
  document.getElementById('phrasePrompt').textContent =
    `Build a word using 「${round.char.char}」 / 用「${round.char.char}」组一个词`;

  // Show phrase meaning as hint
  document.getElementById('phraseHint').textContent =
    `Hint: ${round.phrase.py} — ${round.phrase.en}`;

  // Build slots
  const slotsEl = document.getElementById('phraseSlots');
  slotsEl.innerHTML = '';
  round.wordChars.forEach((ch, i) => {
    const slot = document.createElement('div');
    slot.className = 'phrase-slot';
    slot.dataset.index = i;
    if (i === round.targetIdx) {
      // This is the given character (fixed)
      slot.classList.add('fixed');
      slot.textContent = ch;
    } else {
      // Empty slot to fill
      slot.textContent = '';
      slot.id = `phraseSlot_${i}`;
    }
    slotsEl.appendChild(slot);
  });

  // Show meaning below slots
  document.getElementById('phraseMeaning').textContent = '';

  // Build choices grid
  const choicesEl = document.getElementById('phraseChoices');
  choicesEl.innerHTML = '';
  round.allChoices.forEach((ch, i) => {
    const btn = document.createElement('button');
    btn.className = 'phrase-choice-btn';
    btn.textContent = ch;
    btn.dataset.char = ch;
    btn.addEventListener('click', () => handlePhraseChoice(btn, ch));
    choicesEl.appendChild(btn);
  });

  document.getElementById('phraseFeedback').textContent = '';
}

function handlePhraseChoice(btn, chosenChar) {
  if (phraseState.answered) return;
  const round = phraseState.rounds[phraseState.index];

  // Find the next empty slot to fill
  const nextMissing = round.missingIndices.find(i => !phraseState.selectedSlots.some(s => s.slotIdx === i));
  if (nextMissing === undefined) return;

  // Place the chosen character in the slot
  const slotEl = document.getElementById(`phraseSlot_${nextMissing}`);
  if (slotEl) {
    slotEl.textContent = chosenChar;
    slotEl.classList.add('filled');
  }
  btn.classList.add('selected');

  phraseState.selectedSlots.push({
    slotIdx: nextMissing,
    char: chosenChar,
    correctChar: round.wordChars[nextMissing],
    btnEl: btn,
  });

  // Check if all slots are filled
  if (phraseState.selectedSlots.length === round.missingIndices.length) {
    phraseState.answered = true;

    // Check correctness
    const allCorrect = phraseState.selectedSlots.every(s => s.char === s.correctChar);

    // Disable all choice buttons
    document.querySelectorAll('.phrase-choice-btn').forEach(b => b.classList.add('disabled'));

    if (allCorrect) {
      // Mark all slots correct
      round.missingIndices.forEach(i => {
        const el = document.getElementById(`phraseSlot_${i}`);
        if (el) el.classList.add('correct-slot');
      });
      addScore(15);
      playCorrect();
      document.getElementById('phraseFeedback').textContent = `✅ ${round.phrase.zh} — ${round.phrase.en}`;
      document.getElementById('phraseFeedback').style.color = '#2E7D32';
    } else {
      // Mark wrong slots, show correct answer
      phraseState.selectedSlots.forEach(s => {
        const el = document.getElementById(`phraseSlot_${s.slotIdx}`);
        if (el) {
          if (s.char === s.correctChar) {
            el.classList.add('correct-slot');
          } else {
            el.classList.add('wrong-slot');
            // Show correct char
            setTimeout(() => {
              el.textContent = s.correctChar;
              el.classList.remove('wrong-slot');
              el.classList.add('correct-slot');
            }, 800);
          }
        }
      });
      resetStreak();
      playWrong();
      document.getElementById('phraseFeedback').textContent = `❌ The word is: ${round.phrase.zh} (${round.phrase.en})`;
      document.getElementById('phraseFeedback').style.color = '#C62828';
    }

    // Show meaning
    document.getElementById('phraseMeaning').textContent = `${round.phrase.py} — ${round.phrase.en}`;

    // Auto-advance
    setTimeout(() => {
      phraseState.index++;
      showPhraseRound();
    }, 2000);
  }
}

// =============================================
// ===== RESULTS / FINISH =====
// =============================================
function finishGame() {
  playComplete();
  launchConfetti();

  showScreen('resultsScreen');

  const accuracy = state.total > 0 ? Math.round((state.correct / state.total) * 100) : 0;

  // Determine trophy
  let trophy = '🥉';
  let title = 'Good Try!';
  let subtitle = 'Keep practicing! 继续加油！';
  if (accuracy >= 90) { trophy = '🏆'; title = 'Amazing! 太厉害了！'; subtitle = 'You are a Hanzi master!'; }
  else if (accuracy >= 70) { trophy = '🥇'; title = 'Great Job! 做得好！'; subtitle = 'You are learning fast!'; }
  else if (accuracy >= 50) { trophy = '🥈'; title = 'Nice Work! 不错！'; subtitle = 'Keep going, you can do it!'; }

  document.getElementById('resultsTrophy').textContent = trophy;
  document.getElementById('resultsTitle').textContent = title;
  document.getElementById('resultsSubtitle').textContent = subtitle;
  document.getElementById('resultsScore').textContent = state.score;
  document.getElementById('resultsAccuracy').textContent = accuracy + '%';
  document.getElementById('resultsBestStreak').textContent = state.bestStreak;
  document.getElementById('resultsCharsLearned').textContent = state.correct;

  // Save best score to localStorage
  saveProgress();
}

function saveProgress() {
  try {
    const key = `hanzi_best_g${state.selectedGrade}_${state.selectedMode}`;
    const prev = parseInt(localStorage.getItem(key) || '0');
    if (state.score > prev) {
      localStorage.setItem(key, state.score);
    }
  } catch (e) { /* localStorage might not be available */ }
}

// ===== INIT =====
initHome();
