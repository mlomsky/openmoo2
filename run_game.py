#!/usr/bin/env python3
"""Launch OpenMOO2 with a randomly generated galaxy."""

import random
import sys

from openmoo2.objects.galaxy import Galaxy
from openmoo2.objects.empire import Empire
from openmoo2.objects.race import CANONICAL_RACES
from openmoo2.objects.system import StarSystem
from openmoo2.objects.turn import TurnManager
from openmoo2.gui.main_window import MainWindow

# Default settings — can be overridden via argv
GALAXY_SIZE  = 'medium'   # tiny small medium large huge
NUM_PLAYERS  = 2

PLAYER_SETUP = [
    ('Human',   'blue',   'Emperor Jones'),
    ('Psilon',  'red',    'Psion the Great'),
    ('Mrrshan', 'orange', 'Warlord Kat'),
    ('Sakkra',  'green',  'Overlord Sseth'),
    ('Klackon', 'yellow', 'The Hive'),
    ('Bulrathi','brown',  'Khan Ursa'),
    ('Silicoid','purple', 'The Rock'),
    ('Meklar',  'white',  'The Machine'),
]


def main():
    size = sys.argv[1] if len(sys.argv) > 1 else GALAXY_SIZE
    n    = int(sys.argv[2]) if len(sys.argv) > 2 else NUM_PLAYERS

    StarSystem._systems.clear()
    g = Galaxy(size=size, num_players=n)
    g.generate()

    races  = CANONICAL_RACES
    setups = PLAYER_SETUP[:n]
    empires = [
        Empire(races[race], name, color)
        for race, color, name in setups
    ]
    g.place_empires(empires)

    turns = TurnManager()
    for emp in empires:
        turns.register_empire(emp)

    player = empires[0]   # human player is always first
    MainWindow(g, empires, player, turns).run()


if __name__ == '__main__':
    main()
