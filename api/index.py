# Flask app that serves a single-page Tic-Tac-Toe (X & O) game.
# The entire game runs client-side in JavaScript: it manages board state,
# detects wins/draws using all 8 possible lines, tracks a scoreboard across
# rounds, and includes a minimax-based AI opponent. Players can toggle between
# 2-player mode and vs-AI mode. Deployed on Vercel via vercel.json.
from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>X & O Game</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
      font-family: 'Segoe UI', sans-serif;
      color: #fff;
    }

    h1 {
      font-size: 2.8rem;
      letter-spacing: 6px;
      text-transform: uppercase;
      margin-bottom: 10px;
      background: linear-gradient(90deg, #ff6ec7, #a78bfa, #38bdf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    #status {
      font-size: 1.2rem;
      margin-bottom: 24px;
      min-height: 32px;
      color: #c4b5fd;
      letter-spacing: 1px;
    }

    #scoreboard {
      display: flex;
      gap: 40px;
      margin-bottom: 28px;
    }

    .score-box {
      text-align: center;
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 14px;
      padding: 12px 28px;
    }

    .score-label {
      font-size: 0.85rem;
      color: #a78bfa;
      letter-spacing: 2px;
      text-transform: uppercase;
    }

    .score-val {
      font-size: 2rem;
      font-weight: 700;
    }

    .score-box.x .score-val { color: #f472b6; }
    .score-box.o .score-val { color: #38bdf8; }
    .score-box.draw .score-val { color: #a3a3a3; }

    #board {
      display: grid;
      grid-template-columns: repeat(3, 110px);
      grid-template-rows: repeat(3, 110px);
      gap: 10px;
    }

    .cell {
      width: 110px;
      height: 110px;
      background: rgba(255,255,255,0.06);
      border: 2px solid rgba(255,255,255,0.12);
      border-radius: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 3rem;
      font-weight: 900;
      cursor: pointer;
      transition: background 0.2s, transform 0.15s, border-color 0.2s;
      user-select: none;
    }

    .cell:hover:not(.taken) {
      background: rgba(255,255,255,0.13);
      border-color: rgba(167,139,250,0.5);
      transform: scale(1.05);
    }

    .cell.x { color: #f472b6; }
    .cell.o { color: #38bdf8; }

    .cell.win {
      background: rgba(167,139,250,0.22);
      border-color: #a78bfa;
      animation: pulse 0.6s ease-in-out infinite alternate;
    }

    @keyframes pulse {
      from { box-shadow: 0 0 8px #a78bfa88; }
      to   { box-shadow: 0 0 22px #a78bfacc; }
    }

    #restart {
      margin-top: 30px;
      padding: 12px 36px;
      font-size: 1rem;
      font-weight: 600;
      letter-spacing: 2px;
      text-transform: uppercase;
      background: linear-gradient(135deg, #7c3aed, #2563eb);
      border: none;
      border-radius: 50px;
      color: #fff;
      cursor: pointer;
      transition: transform 0.15s, box-shadow 0.15s;
    }

    #restart:hover {
      transform: scale(1.05);
      box-shadow: 0 6px 24px rgba(124,58,237,0.5);
    }

    #mode-toggle {
      margin-top: 14px;
      padding: 8px 24px;
      font-size: 0.85rem;
      letter-spacing: 1px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 50px;
      color: #c4b5fd;
      cursor: pointer;
      transition: background 0.2s;
    }

    #mode-toggle:hover { background: rgba(255,255,255,0.15); }
  </style>
</head>
<body>
  <h1>X &amp; O</h1>
  <div id="status">Player X's turn</div>

  <div id="scoreboard">
    <div class="score-box x">
      <div class="score-label">X</div>
      <div class="score-val" id="score-x">0</div>
    </div>
    <div class="score-box draw">
      <div class="score-label">Draw</div>
      <div class="score-val" id="score-d">0</div>
    </div>
    <div class="score-box o">
      <div class="score-label">O</div>
      <div class="score-val" id="score-o">0</div>
    </div>
  </div>

  <div id="board">
    <div class="cell" data-i="0"></div>
    <div class="cell" data-i="1"></div>
    <div class="cell" data-i="2"></div>
    <div class="cell" data-i="3"></div>
    <div class="cell" data-i="4"></div>
    <div class="cell" data-i="5"></div>
    <div class="cell" data-i="6"></div>
    <div class="cell" data-i="7"></div>
    <div class="cell" data-i="8"></div>
  </div>

  <button id="restart">New Game</button>
  <button id="mode-toggle">Mode: 2 Players</button>

  <script>
    const WINS = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
    let board, current, gameOver, scores, vsAI;

    function init() {
      board = Array(9).fill('');
      current = 'X';
      gameOver = false;
      document.querySelectorAll('.cell').forEach(c => {
        c.textContent = '';
        c.className = 'cell';
      });
      setStatus("Player X's turn");
    }

    scores = {X:0, O:0, D:0};
    vsAI = false;

    function setStatus(msg) {
      document.getElementById('status').textContent = msg;
    }

    function checkWin(b, p) {
      return WINS.find(([a,c,d]) => b[a]===p && b[c]===p && b[d]===p) || null;
    }

    function minimax(b, isMax) {
      const xw = checkWin(b,'X'), ow = checkWin(b,'O');
      if (ow) return 10;
      if (xw) return -10;
      if (b.every(v=>v)) return 0;
      if (isMax) {
        let best = -Infinity;
        b.forEach((_,i) => { if(!b[i]){ b[i]='O'; best=Math.max(best,minimax(b,false)); b[i]=''; } });
        return best;
      } else {
        let best = Infinity;
        b.forEach((_,i) => { if(!b[i]){ b[i]='X'; best=Math.min(best,minimax(b,true)); b[i]=''; } });
        return best;
      }
    }

    function aiMove() {
      let best = -Infinity, move = -1;
      board.forEach((_,i) => {
        if (!board[i]) {
          board[i] = 'O';
          const s = minimax(board, false);
          board[i] = '';
          if (s > best) { best = s; move = i; }
        }
      });
      if (move !== -1) playAt(move);
    }

    function playAt(i) {
      if (gameOver || board[i]) return;
      board[i] = current;
      const cell = document.querySelector(`[data-i="${i}"]`);
      cell.textContent = current;
      cell.classList.add('taken', current.toLowerCase());

      const line = checkWin(board, current);
      if (line) {
        line.forEach(idx => document.querySelector(`[data-i="${idx}"]`).classList.add('win'));
        setStatus(`Player ${current} wins! 🎉`);
        scores[current]++;
        updateScores();
        gameOver = true;
        return;
      }
      if (board.every(v => v)) {
        setStatus("It's a draw!");
        scores.D++;
        updateScores();
        gameOver = true;
        return;
      }
      current = current === 'X' ? 'O' : 'X';
      setStatus(vsAI && current==='O' ? "AI is thinking..." : `Player ${current}'s turn`);
      if (vsAI && current === 'O') setTimeout(aiMove, 300);
    }

    function updateScores() {
      document.getElementById('score-x').textContent = scores.X;
      document.getElementById('score-o').textContent = scores.O;
      document.getElementById('score-d').textContent = scores.D;
    }

    document.getElementById('board').addEventListener('click', e => {
      const cell = e.target.closest('.cell');
      if (!cell) return;
      if (vsAI && current === 'O') return;
      playAt(+cell.dataset.i);
    });

    document.getElementById('restart').addEventListener('click', init);

    document.getElementById('mode-toggle').addEventListener('click', () => {
      vsAI = !vsAI;
      document.getElementById('mode-toggle').textContent = vsAI ? 'Mode: vs AI' : 'Mode: 2 Players';
      init();
    });

    init();
  </script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(debug=True)
