from flask import Flask, render_template_string, request, jsonify, session
import random

app = Flask(__name__)
app.secret_key = 'rps_secret_key_2024'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rock Paper Scissors</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --win: #00e676;
    --lose: #ff5252;
    --tie: #ffd740;
    --bg: #0d0f14;
    --surface: #161a23;
    --surface2: #1e2330;
    --border: rgba(255,255,255,0.07);
    --text: #e8edf5;
    --muted: #6b7590;
  }

  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    overflow-x: hidden;
  }
  body::before {
    content: '';
    position: fixed;
    top: -30%; left: 50%;
    transform: translateX(-50%);
    width: 700px; height: 700px;
    background: radial-gradient(ellipse, rgba(99,102,241,0.12) 0%, transparent 70%);
    pointer-events: none; z-index: 0;
  }

  .game-wrap {
    position: relative; z-index: 1;
    width: 100%; max-width: 700px;
    padding: 2rem 1.5rem 4rem;
    display: flex; flex-direction: column;
    align-items: center; gap: 1.6rem;
  }

  /* Header */
  header { text-align: center; padding-top: 1rem; }
  header h1 {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(2.8rem, 8vw, 4.5rem);
    letter-spacing: 0.08em;
    background: linear-gradient(135deg, #818cf8, #c084fc, #67e8f9);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1;
  }
  header p { color: var(--muted); font-size: 0.9rem; margin-top: 0.4rem; letter-spacing: 0.05em; text-transform: uppercase; }

  /* Scoreboard */
  .scoreboard {
    display: grid; grid-template-columns: repeat(3,1fr);
    gap: 1rem; width: 100%;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 20px; padding: 1.4rem 1.2rem;
  }
  .score-item { display: flex; flex-direction: column; align-items: center; gap: 0.3rem; }
  .score-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); font-weight: 500; }
  .score-value {
    font-family: 'Bebas Neue', sans-serif; font-size: 3rem; line-height: 1;
    transition: transform 0.25s cubic-bezier(0.34,1.56,0.64,1);
  }
  .score-item:nth-child(1) .score-value { color: #818cf8; }
  .score-item:nth-child(2) .score-value { color: #f472b6; }
  .score-item:nth-child(3) .score-value { color: #fbbf24; }
  .score-value.pop { transform: scale(1.35); }

  /* ── Countdown ring ── */
  .countdown-wrap {
    display: flex; flex-direction: column;
    align-items: center; gap: 0.5rem; width: 100%;
    transition: opacity 0.4s;
  }
  .countdown-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); }
  .countdown-ring-wrap { position: relative; width: 86px; height: 86px; }
  .countdown-svg { width: 86px; height: 86px; transform: rotate(-90deg); }
  .ring-bg   { fill: none; stroke: var(--surface2); stroke-width: 7; }
  .ring-prog {
    fill: none; stroke: #818cf8; stroke-width: 7; stroke-linecap: round;
    stroke-dasharray: 213.63;   /* 2*PI*34 */
    stroke-dashoffset: 0;
    transition: stroke-dashoffset 1s linear, stroke 0.5s;
  }
  .countdown-number {
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Bebas Neue', sans-serif; font-size: 2.2rem;
    color: #818cf8; transition: color 0.5s;
  }
  /* urgency */
  .urgent .ring-prog   { stroke: var(--lose); }
  .urgent .countdown-number { color: var(--lose); }
  .urgent { animation: shk 0.3s infinite; }
  @keyframes shk { 0%,100%{transform:translateX(0)} 33%{transform:translateX(-3px)} 66%{transform:translateX(3px)} }

  /* Arena */
  .arena { display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 1rem; }
  .fighter {
    flex: 1; background: var(--surface); border: 1px solid var(--border);
    border-radius: 20px; padding: 1.5rem 1rem; text-align: center;
    min-height: 130px; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 0.5rem;
    transition: border-color 0.3s, box-shadow 0.3s;
  }
  .fighter.win-glow  { border-color: var(--win);  box-shadow: 0 0 20px rgba(0,230,118,0.2); }
  .fighter.lose-glow { border-color: var(--lose); box-shadow: 0 0 20px rgba(255,82,82,0.2); }
  .fighter.tie-glow  { border-color: var(--tie);  box-shadow: 0 0 20px rgba(255,215,64,0.15); }
  .fighter-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); }
  .fighter-emoji { font-size: 3.2rem; line-height: 1; filter: grayscale(0.2); }
  .fighter-emoji.bounce { animation: bnc 0.5s cubic-bezier(0.34,1.56,0.64,1); }
  .fighter-name { font-size: 0.85rem; font-weight: 700; color: var(--muted); transition: color 0.3s; }
  .fighter-name.revealed { color: var(--text); }
  .vs-badge { font-family: 'Bebas Neue', sans-serif; font-size: 1.8rem; color: var(--muted); flex-shrink: 0; }
  @keyframes bnc {
    0%   { transform: scale(0.3) rotate(-15deg); opacity: 0; }
    60%  { transform: scale(1.2) rotate(5deg);   opacity: 1; }
    100% { transform: scale(1)   rotate(0deg);   opacity: 1; }
  }

  /* Result */
  .result-banner { height: 2.5rem; display: flex; align-items: center; justify-content: center; }
  .result-text {
    font-family: 'Bebas Neue', sans-serif; font-size: 2rem; letter-spacing: 0.1em;
    opacity: 0; transform: translateY(10px); transition: opacity 0.3s, transform 0.3s;
  }
  .result-text.show { opacity: 1; transform: translateY(0); }
  .result-text.win  { color: var(--win); }
  .result-text.lose { color: var(--lose); }
  .result-text.tie  { color: var(--tie); }

  /* Choice buttons */
  .choices { display: flex; gap: 1rem; width: 100%; justify-content: center; flex-wrap: wrap; }
  .choice-btn {
    flex: 1; min-width: 130px; max-width: 195px; aspect-ratio: 1;
    border: 2px solid var(--border); border-radius: 24px;
    background: var(--surface); cursor: pointer;
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.6rem;
    transition: transform 0.18s, border-color 0.2s, box-shadow 0.2s;
    position: relative; overflow: hidden;
  }
  .choice-btn::before {
    content: ''; position: absolute; inset: 0; opacity: 0;
    transition: opacity 0.2s; border-radius: inherit;
  }
  .choice-btn[data-choice="rock"]::before     { background: radial-gradient(circle at 50% 120%, rgba(124,138,158,0.25), transparent 70%); }
  .choice-btn[data-choice="paper"]::before    { background: radial-gradient(circle at 50% 120%, rgba(212,228,247,0.15), transparent 70%); }
  .choice-btn[data-choice="scissors"]::before { background: radial-gradient(circle at 50% 120%, rgba(192,200,212,0.2),  transparent 70%); }
  .choice-btn:hover:not(:disabled)::before { opacity: 1; }
  .choice-btn:hover:not(:disabled) {
    transform: translateY(-6px) scale(1.03);
    border-color: rgba(255,255,255,0.2);
    box-shadow: 0 16px 40px rgba(0,0,0,0.4);
  }
  .choice-btn:active:not(:disabled) { transform: translateY(-2px) scale(0.98); }
  .choice-btn:disabled { opacity: 0.35; cursor: not-allowed; }
  .choice-btn.locked {
    border-color: #00e676;
    box-shadow: 0 0 0 3px rgba(0,230,118,0.25);
  }
  /* "LOCKED" badge top-right */
  .lock-badge {
    position: absolute; top: 8px; right: 10px;
    font-size: 0.6rem; font-weight: 700; letter-spacing: 0.05em;
    color: #00e676; opacity: 0; transition: opacity 0.2s;
  }
  .choice-btn.locked .lock-badge { opacity: 1; }
  .btn-emoji { font-size: 2.8rem; pointer-events: none; }
  .btn-label {
    font-family: 'Bebas Neue', sans-serif; font-size: 1.1rem;
    letter-spacing: 0.08em; color: var(--muted); transition: color 0.2s; pointer-events: none;
  }
  .choice-btn:hover:not(:disabled) .btn-label { color: var(--text); }

  /* Prompt panel */
  .prompt-panel {
    width: 100%; background: var(--surface); border: 1px solid var(--border);
    border-radius: 20px; padding: 1.6rem 2rem; text-align: center;
    display: none; flex-direction: column; align-items: center; gap: 1rem;
    animation: slideUp 0.3s ease;
  }
  .prompt-panel.show { display: flex; }
  .prompt-panel p { font-size: 1rem; color: var(--muted); }
  .prompt-btns { display: flex; gap: 1rem; }
  .btn-yes, .btn-no {
    padding: 0.75rem 2.2rem; border-radius: 50px;
    font-family: 'DM Sans', sans-serif; font-size: 0.9rem; font-weight: 700;
    cursor: pointer; border: none;
    transition: transform 0.15s, box-shadow 0.15s; letter-spacing: 0.05em;
  }
  .btn-yes { background: linear-gradient(135deg,#818cf8,#c084fc); color:#fff; box-shadow: 0 4px 20px rgba(129,140,248,0.4); }
  .btn-yes:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(129,140,248,0.5); }
  .btn-no  { background: var(--surface2); color: var(--muted); border: 1px solid var(--border); }
  .btn-no:hover { transform: translateY(-2px); color: var(--text); }

  /* Final panel */
  .final-panel {
    width: 100%; background: var(--surface); border: 1px solid var(--border);
    border-radius: 20px; padding: 2rem; text-align: center;
    display: none; flex-direction: column; align-items: center; gap: 1.2rem;
    animation: slideUp 0.4s ease;
  }
  .final-panel.show { display: flex; }
  .final-panel h2 {
    font-family: 'Bebas Neue', sans-serif; font-size: 2rem; letter-spacing: 0.1em;
    background: linear-gradient(135deg,#818cf8,#c084fc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  }
  .final-scores { display: flex; gap: 2rem; flex-wrap: wrap; justify-content: center; }
  .final-score-item { display: flex; flex-direction: column; align-items: center; }
  .final-score-item .label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); }
  .final-score-item .value { font-family: 'Bebas Neue', sans-serif; font-size: 2.8rem; }
  .final-score-item:nth-child(1) .value { color: #818cf8; }
  .final-score-item:nth-child(2) .value { color: #f472b6; }
  .final-score-item:nth-child(3) .value { color: #fbbf24; }
  .final-msg { color: var(--muted); font-size: 0.95rem; }
  .btn-restart {
    padding: 0.8rem 2.5rem; border-radius: 50px;
    background: linear-gradient(135deg,#818cf8,#c084fc); color: #fff;
    font-family: 'DM Sans', sans-serif; font-weight: 700; font-size: 0.9rem;
    cursor: pointer; border: none;
    box-shadow: 0 4px 20px rgba(129,140,248,0.4);
    transition: transform 0.15s, box-shadow 0.15s; letter-spacing: 0.05em; margin-top: 0.5rem;
  }
  .btn-restart:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(129,140,248,0.5); }

  @keyframes slideUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
  #confetti-canvas { position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:999; }
  .ripple {
    position:absolute;border-radius:50%;
    background:rgba(255,255,255,0.15);transform:scale(0);
    animation:rpl 0.5s linear;pointer-events:none;
  }
  @keyframes rpl { to{transform:scale(4);opacity:0} }

  @media(max-width:480px){
    .choice-btn{min-width:100px} .btn-emoji{font-size:2.2rem}
    .scoreboard{padding:1rem} .score-value{font-size:2.4rem}
    .fighter{min-height:110px;padding:1rem 0.6rem} .fighter-emoji{font-size:2.5rem}
  }
</style>
</head>
<body>
<canvas id="confetti-canvas"></canvas>

<div class="game-wrap">
  <header>
    <h1>Rock Paper Scissors</h1>
    <p>Pick before time runs out!</p>
  </header>

  <!-- Scoreboard -->
  <div class="scoreboard">
    <div class="score-item">
      <span class="score-label">You</span>
      <span class="score-value" id="score-user">0</span>
    </div>
    <div class="score-item">
      <span class="score-label">Computer</span>
      <span class="score-value" id="score-computer">0</span>
    </div>
    <div class="score-item">
      <span class="score-label">Ties</span>
      <span class="score-value" id="score-ties">0</span>
    </div>
  </div>

  <!-- Countdown ring -->
  <div class="countdown-wrap" id="countdown-wrap">
    <span class="countdown-label">Time to choose</span>
    <div class="countdown-ring-wrap" id="ring-wrap">
      <svg class="countdown-svg" viewBox="0 0 86 86">
        <circle class="ring-bg"   cx="43" cy="43" r="34"/>
        <circle class="ring-prog" cx="43" cy="43" r="34" id="ring-prog"/>
      </svg>
      <div class="countdown-number" id="countdown-num">5</div>
    </div>
  </div>

  <!-- Arena -->
  <div class="arena">
    <div class="fighter" id="fighter-user">
      <span class="fighter-label">You</span>
      <span class="fighter-emoji" id="emoji-user">❓</span>
      <span class="fighter-name"  id="name-user">Waiting…</span>
    </div>
    <div class="vs-badge">VS</div>
    <div class="fighter" id="fighter-comp">
      <span class="fighter-label">Computer</span>
      <span class="fighter-emoji" id="emoji-comp">❓</span>
      <span class="fighter-name"  id="name-comp">Waiting…</span>
    </div>
  </div>

  <!-- Result -->
  <div class="result-banner">
    <div class="result-text" id="result-text">—</div>
  </div>

  <!-- Choices -->
  <div class="choices" id="choices">
    <button class="choice-btn" data-choice="rock"     onclick="lockChoice(this,'rock')">
      <span class="lock-badge">LOCKED ✓</span>
      <span class="btn-emoji">🪨</span><span class="btn-label">Rock</span>
    </button>
    <button class="choice-btn" data-choice="paper"    onclick="lockChoice(this,'paper')">
      <span class="lock-badge">LOCKED ✓</span>
      <span class="btn-emoji">📄</span><span class="btn-label">Paper</span>
    </button>
    <button class="choice-btn" data-choice="scissors" onclick="lockChoice(this,'scissors')">
      <span class="lock-badge">LOCKED ✓</span>
      <span class="btn-emoji">✂️</span><span class="btn-label">Scissors</span>
    </button>
  </div>

  <!-- Play-again prompt -->
  <div class="prompt-panel" id="prompt-panel">
    <p>Play another round?</p>
    <div class="prompt-btns">
      <button class="btn-yes" onclick="continueGame()">▶ Yes!</button>
      <button class="btn-no"  onclick="quitGame()">Quit</button>
    </div>
  </div>

  <!-- Final summary -->
  <div class="final-panel" id="final-panel">
    <h2>Game Over</h2>
    <div class="final-scores">
      <div class="final-score-item"><span class="label">You</span><span class="value" id="final-user">0</span></div>
      <div class="final-score-item"><span class="label">Computer</span><span class="value" id="final-comp">0</span></div>
      <div class="final-score-item"><span class="label">Ties</span><span class="value" id="final-ties">0</span></div>
    </div>
    <p class="final-msg" id="final-msg">Thanks for playing!</p>
    <button class="btn-restart" onclick="restartGame()">↩ Play Again</button>
  </div>
</div>

<script>
const EMOJIS = { rock:'🪨', paper:'📄', scissors:'✂️' };
const TOTAL   = 5;
const CIRCUM  = 2 * Math.PI * 34; // ~213.63

let timer       = null;
let secsLeft    = TOTAL;
let lockedChoice = null;
let roundActive  = false;
let busy         = false;

// ── Countdown ─────────────────────────────────────────────────────────────────
function startCountdown() {
  roundActive  = true;
  lockedChoice = null;
  secsLeft     = TOTAL;
  busy         = false;

  updateRing(TOTAL);
  setButtonsDisabled(false);
  document.querySelectorAll('.choice-btn').forEach(b => b.classList.remove('locked'));
  document.getElementById('countdown-wrap').style.opacity = '1';

  timer = setInterval(() => {
    secsLeft--;
    updateRing(secsLeft);
    if (secsLeft <= 0) {
      clearInterval(timer); timer = null;
      submitPlay(lockedChoice); // null = timed out
    }
  }, 1000);
}

function updateRing(s) {
  const num  = document.getElementById('countdown-num');
  const ring = document.getElementById('ring-prog');
  const wrap = document.getElementById('ring-wrap');
  const safe = Math.max(s, 0);

  num.textContent = safe;
  ring.style.strokeDashoffset = CIRCUM * (1 - safe / TOTAL);
  wrap.classList.toggle('urgent', s <= 2);
}

// ── User clicks ───────────────────────────────────────────────────────────────
function lockChoice(btn, choice) {
  if (!roundActive || busy) return;

  // Ripple effect
  const rpl  = document.createElement('span');
  rpl.className = 'ripple';
  const sz = Math.max(btn.offsetWidth, btn.offsetHeight);
  rpl.style.cssText = `width:${sz}px;height:${sz}px;left:${(btn.offsetWidth-sz)/2}px;top:${(btn.offsetHeight-sz)/2}px`;
  btn.appendChild(rpl);
  setTimeout(() => rpl.remove(), 600);

  lockedChoice = choice;
  document.querySelectorAll('.choice-btn').forEach(b => b.classList.remove('locked'));
  btn.classList.add('locked');
  setFighter('user', choice, false);
}

// ── Submit to server ──────────────────────────────────────────────────────────
function submitPlay(choice) {
  if (busy) return;
  busy = true; roundActive = false;
  setButtonsDisabled(true);

  if (!choice) {
    // Timed out — show ⏰ immediately
    const rt = document.getElementById('result-text');
    rt.textContent = "⏰ Time's Up!";
    rt.className   = 'result-text show lose';
    const eu = document.getElementById('emoji-user');
    const nu = document.getElementById('name-user');
    eu.textContent = '💨'; nu.textContent = 'Too slow!'; nu.classList.add('revealed');
  }

  setCompThinking();

  fetch('/play', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ choice: choice || 'none' })
  })
  .then(r => r.json())
  .then(data => setTimeout(() => showResult(data, !choice), choice ? 0 : 500))
  .catch(() => { busy = false; });
}

function setCompThinking() {
  const e = document.getElementById('emoji-comp');
  const n = document.getElementById('name-comp');
  e.textContent = '🤔'; e.classList.remove('bounce');
  n.textContent = 'Thinking…'; n.classList.remove('revealed');
  document.getElementById('fighter-comp').className = 'fighter';
}

function setFighter(who, choice, animate=true) {
  const e = document.getElementById(`emoji-${who}`);
  const n = document.getElementById(`name-${who}`);
  e.textContent = EMOJIS[choice] || '❓';
  n.textContent = choice.charAt(0).toUpperCase() + choice.slice(1);
  n.classList.add('revealed');
  if (animate) { e.classList.remove('bounce'); void e.offsetWidth; e.classList.add('bounce'); }
}

function showResult(data, timedOut) {
  setFighter('comp', data.comp_choice, true);

  if (!timedOut) {
    const rt = document.getElementById('result-text');
    rt.classList.remove('show','win','lose','tie');
    void rt.offsetWidth;
    let cls, text;
    if      (data.result==='win')  { cls='win';  text='🎉 You Win!'; }
    else if (data.result==='lose') { cls='lose'; text='💀 You Lose!'; }
    else                           { cls='tie';  text="🤝 It's a Tie!"; }
    rt.textContent = text;
    rt.classList.add('show', cls);
  }

  const uf = document.getElementById('fighter-user');
  const cf = document.getElementById('fighter-comp');
  uf.className = cf.className = 'fighter';
  if      (data.result==='win')  { uf.classList.add('win-glow');  cf.classList.add('lose-glow'); }
  else if (data.result==='lose') { uf.classList.add('lose-glow'); cf.classList.add('win-glow'); }
  else                           { uf.classList.add('tie-glow');  cf.classList.add('tie-glow'); }

  updateScore('score-user',     data.scores.user);
  updateScore('score-computer', data.scores.computer);
  updateScore('score-ties',     data.scores.ties);

  document.getElementById('countdown-wrap').style.opacity = '0.3';

  setTimeout(() => {
    document.getElementById('prompt-panel').classList.add('show');
    busy = false;
  }, 900);
}

function updateScore(id, value) {
  const el = document.getElementById(id);
  const prev = parseInt(el.textContent);
  el.textContent = value;
  if (value !== prev) {
    el.classList.remove('pop'); void el.offsetWidth;
    el.classList.add('pop');
    setTimeout(() => el.classList.remove('pop'), 300);
  }
}

// ── Continue / Quit / Restart ─────────────────────────────────────────────────
function continueGame() {
  document.getElementById('prompt-panel').classList.remove('show');

  ['user','comp'].forEach(who => {
    const id = who === 'comp' ? 'comp' : 'user';
    document.getElementById(`emoji-${who}`).textContent = '❓';
    document.getElementById(`emoji-${who}`).classList.remove('bounce');
    document.getElementById(`name-${who}`).textContent = 'Waiting…';
    document.getElementById(`name-${who}`).classList.remove('revealed');
    document.getElementById(`fighter-${id}`).className = 'fighter';
  });

  const rt = document.getElementById('result-text');
  rt.classList.remove('show','win','lose','tie'); rt.textContent = '—';

  startCountdown();
}

function quitGame() {
  if (timer) { clearInterval(timer); timer = null; }
  roundActive = false;
  document.getElementById('prompt-panel').classList.remove('show');
  setButtonsDisabled(true);

  const u = parseInt(document.getElementById('score-user').textContent);
  const c = parseInt(document.getElementById('score-computer').textContent);
  const t = parseInt(document.getElementById('score-ties').textContent);

  document.getElementById('final-user').textContent = u;
  document.getElementById('final-comp').textContent = c;
  document.getElementById('final-ties').textContent = t;

  let msg;
  if (u > c)      msg = '🏆 You beat the machine!';
  else if (c > u) msg = '🤖 The computer wins this time!';
  else            msg = '🤝 A perfectly balanced match!';
  document.getElementById('final-msg').textContent = msg;
  document.getElementById('final-panel').classList.add('show');
  document.getElementById('countdown-wrap').style.opacity = '0.3';

  if (u > c) launchConfetti();
}

function restartGame() {
  fetch('/restart',{method:'POST'})
    .then(r=>r.json())
    .then(()=>{
      ['score-user','score-computer','score-ties'].forEach(id=>{
        document.getElementById(id).textContent='0';
      });
      document.getElementById('final-panel').classList.remove('show');
      continueGame();
    });
}

function setButtonsDisabled(d) {
  document.querySelectorAll('.choice-btn').forEach(b=>b.disabled=d);
}

// ── Confetti ──────────────────────────────────────────────────────────────────
function launchConfetti() {
  const canvas=document.getElementById('confetti-canvas');
  const ctx=canvas.getContext('2d');
  canvas.width=window.innerWidth; canvas.height=window.innerHeight;
  const colors=['#818cf8','#c084fc','#67e8f9','#fbbf24','#f472b6','#34d399'];
  const pieces=Array.from({length:140},()=>({
    x:Math.random()*canvas.width, y:Math.random()*-canvas.height,
    w:Math.random()*10+6, h:Math.random()*14+8,
    color:colors[Math.floor(Math.random()*colors.length)],
    vx:(Math.random()-0.5)*3, vy:Math.random()*3+2,
    angle:Math.random()*Math.PI*2, vAngle:(Math.random()-0.5)*0.15, opacity:1
  }));
  let frame;
  function draw(){
    ctx.clearRect(0,0,canvas.width,canvas.height);
    let alive=false;
    pieces.forEach(p=>{
      p.x+=p.vx; p.y+=p.vy; p.angle+=p.vAngle;
      if(p.y>canvas.height*0.6) p.opacity-=0.02;
      if(p.opacity<=0) return;
      alive=true;
      ctx.save(); ctx.translate(p.x,p.y); ctx.rotate(p.angle);
      ctx.globalAlpha=Math.max(0,p.opacity); ctx.fillStyle=p.color;
      ctx.fillRect(-p.w/2,-p.h/2,p.w,p.h); ctx.restore();
    });
    if(alive) frame=requestAnimationFrame(draw);
    else ctx.clearRect(0,0,canvas.width,canvas.height);
  }
  draw();
  setTimeout(()=>{cancelAnimationFrame(frame);ctx.clearRect(0,0,canvas.width,canvas.height);},4000);
}

// Kick off!
startCountdown();
</script>
</body>
</html>
"""

def get_scores():
    session.setdefault('user', 0)
    session.setdefault('computer', 0)
    session.setdefault('ties', 0)
    return {'user': session['user'], 'computer': session['computer'], 'ties': session['ties']}

@app.route('/')
def index():
    session.setdefault('user', 0)
    session.setdefault('computer', 0)
    session.setdefault('ties', 0)
    return render_template_string(HTML_TEMPLATE)

@app.route('/play', methods=['POST'])
def play():
    data        = request.get_json()
    user_choice = data.get('choice', '').lower()
    comp_choice = random.choice(['rock', 'paper', 'scissors'])

    # 'none' or anything invalid → user timed out → computer wins
    if user_choice not in ('rock', 'paper', 'scissors'):
        session['computer'] = session.get('computer', 0) + 1
        session.modified = True
        return jsonify({'comp_choice': comp_choice, 'result': 'lose', 'scores': get_scores()})

    beats = {'rock': 'scissors', 'scissors': 'paper', 'paper': 'rock'}
    if user_choice == comp_choice:
        result = 'tie';  session['ties']     = session.get('ties',     0) + 1
    elif beats[user_choice] == comp_choice:
        result = 'win';  session['user']     = session.get('user',     0) + 1
    else:
        result = 'lose'; session['computer'] = session.get('computer', 0) + 1

    session.modified = True
    return jsonify({'comp_choice': comp_choice, 'result': result, 'scores': get_scores()})

@app.route('/restart', methods=['POST'])
def restart():
    session['user'] = session['computer'] = session['ties'] = 0
    session.modified = True
    return jsonify({'status': 'ok', 'scores': get_scores()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
