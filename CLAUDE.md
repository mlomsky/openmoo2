# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An open-source Python reimplementation of Master of Orion II: Battle at Antares. The project reads original MOO2 `.LBX` data files for assets and aims to rebuild the game logic from scratch. The `oldmess/` directory contains an older abandoned attempt; the active code is under `openmoo2/`.

## Running the game

```bash
python run_game.py                  # medium galaxy, 2 players
python run_game.py small 3          # small galaxy, 3 players
python run_game.py huge 6           # huge galaxy, 6 players
```

Controls: left-click a star to inspect it; **N / Enter / Space** to end a turn; **Escape** to quit.

## Tests

```bash
python -m pytest tests/ -v
python -m pytest tests/test_colony.py -v   # single file
```

## Installing (editable/dev mode)

```bash
pip install -e .
pip install pygame      # required for the GUI
```

## Architecture

```
openmoo2/
  objects/
    planet.py      # Planet — size, mineral, gravity, environment, colony flag
    system.py      # StarSystem — star class/color, x/y coords, special, planets dict
    galaxy.py      # Galaxy — procedural generation, star placement, planet gen, empire placement
    race.py        # Race — 30 MOO2 racepick fields; CANONICAL_RACES dict (13 races)
    empire.py      # Empire — links Race to game state (homeworld, treasury, colonies, research)
    colony.py      # Colony — farmers/workers/scientists, MOO2 food/industry/research/growth formulas
    turn.py        # TurnManager + TurnResult — per-turn game loop
  gui/
    colors.py      # All colour constants (star classes, empire colours, UI chrome)
    main_window.py # MainWindow — pygame galaxy map with right-side info panel
  orion.py         # Skeleton top-level game object (server/client stubs)
  oriondataloader.py  # Finds data/ dir and LBX file paths
  orionexception.py   # Base OrionException
  probabilities.py    # Random helpers
run_game.py        # Entry point — generates galaxy, places empires, opens MainWindow
data/              # LBX assets go here (data/lbx/)
tests/             # pytest suite (185 tests)
oldmess/           # Old abandoned implementation — reference only, do not edit
```

## Key notes

- Python 3.13 on Windows. pygame 2.6.1 required for the GUI.
- Tests use pytest (nose was incompatible with Python 3.13 and has been ported out).
- `StarSystem._systems` is a class-level set — tests must clear it via `StarSystem._systems.clear()` in fixtures; `Galaxy.generate()` does this automatically.
- Galaxy coordinates go from `(0,0)` to `(galaxy.width, galaxy.height)`; `MainWindow` maps these to screen pixels using a linear scale.
- Colony growth uses the canonical MOO2 formula: `growth = (a * floor(sqrt(2000*pop*(max-pop)/max))) / 100` where `a = 100 + race.population` (Sakkra: 200, most races: 100). Reserve hits 1000 → new colonist.
- `race.population` stores the raw MOO2 bonus value (0 for most, 100 for Sakkra, -20 for Silicoid), not a normalised [-2,+2] like other traits.
- Many Planet/StarSystem exceptions are bare `raise Exception` with `# TODO` — replacing them with `OrionException` subclasses is a standing improvement task.
