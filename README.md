# Space Invader (Python + Pygame)

A compact Space Invader game implemented in Python using Pygame. The project includes a simple enemy AI that combines a finite-state controller with a lightweight Q-learning component so enemies can adapt their high-level decisions (patrol / attack / evade) over time.

**Quick Controls**
- **Left / Right arrows**: move the player ship
- **Spacebar**: fire a bullet

The game ends when an enemy reaches the player's vertical level.

**Notable Features**
- Classic Space Invader gameplay with sprite-based enemies and bullets.
- Enemy AI:
  - Finite-state logic (patrol, attack, evade) governs movement behavior.
  - A lightweight Q-learning agent discretizes a small state (distance bucket, bullet proximity, player-above, low HP) and learns to choose between the high-level actions.
  - A fuzzy logic difficulty tweak adjusts enemy speed based on player accuracy and score.
  - The learned Q-table is persisted to `spaceEnvader/q_table.pkl` so learning continues across sessions.

Getting started (Windows PowerShell)
1. Open a PowerShell terminal and change into the project folder's `spaceEnvader` directory:

```powershell
Set-Location -LiteralPath 'c:\Users\<you>\Downloads\space_invader_pygame-main\space_invader_pygame-main\spaceEnvader'
```

2. (Recommended) Create and activate a virtual environment:

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
```

3. Install pygame:

```powershell
python -m pip install pygame
```

4. Run the game:

```powershell
python main.py
```

Notes about the AI and tuning
- Q-table file: `spaceEnvader/q_table.pkl`. Delete this file to reset learning and start from scratch.
- Tuning variables live in `spaceEnvader/ai_brain.py` (examples: `EPSILON`, `ALPHA`, `GAMMA`, `EVADE_SPEED`, `BULLET_EVADE_DIST`). Changing these values will affect exploration, learning speed, and evasion behavior.
- The Q-learning implementation is intentionally lightweight and uses discrete states and a small action set so it is easy to inspect and reset.

Project structure
```
README.md
space_invader_pygame-main/
├── spaceEnvader/
│   ├── main.py            # game entry
│   ├── ai_brain.py        # enemy AI + Q-learning
│   ├── q_table.pkl        # (generated) persisted Q-table
│   ├── audio/             # audio assets
│   └── images/            # sprite assets
```

Troubleshooting
- If you get "No module named 'pygame'", ensure you installed Pygame into the active environment (see step 3 above).
- If the game window opens but sprites are missing or errors appear, check that the `images/` and `audio/` folders exist under `spaceEnvader/` and contain the expected assets.

Resetting learned AI
- To reset enemy learning, delete `spaceEnvader/q_table.pkl` and restart the game.

**note that it's a Student project for (CSCI218 - intro to AI)
