# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An open-source Python reimplementation of Master of Orion II: Battle at Antares. The project reads original MOO2 `.LBX` data files for assets and aims to rebuild the game logic from scratch. The `oldmess/` directory contains an older abandoned attempt; the active code is under `openmoo2/`.

## Running tests

```bash
python -m pytest tests/ -v
```

Run a single test file:
```bash
python -m pytest tests/test_planet.py -v
```

## Installing (editable/dev mode)

```bash
pip install -e .
```

## Architecture

```
openmoo2/          # active source package
  objects/
    planet.py      # Planet class — size, mineral, gravity, colony, environment
    system.py      # StarSystem class — star color, planets, administrator
  orion.py         # Orion class — top-level game object; wires server + client
  oriondataloader.py  # finds the data/ dir and provides paths to LBX files
  orionexception.py   # base OrionException
  probabilities.py    # probability helpers
data/              # game data dir (LBX files go in data/lbx/)
tests/             # pytest test suite
oldmess/           # old abandoned implementation — do not edit
```

## Key notes

- Requires Python 3.4+; tested on 3.13.
- Tests were ported from `nose` to `pytest` (nose is incompatible with Python 3.13).
- The `oriondataloader` looks for data files first at `../data` relative to the package, then `/usr/share/openmoo2`. On Windows, only the first path applies.
- `StarSystem` maintains a class-level `_systems` registry of all named systems — be aware of test isolation if adding new system tests.
- Many exceptions in the game objects are bare `raise Exception` with `# TODO` comments — a good area for improvement is replacing these with specific `OrionException` subclasses.
