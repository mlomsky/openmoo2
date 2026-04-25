# vim: set ts=4 sw=4 et: coding=UTF-8

from .race import Race

VALID_COLORS = frozenset(
    ('red', 'yellow', 'green', 'white', 'blue', 'brown', 'purple', 'orange')
)
VALID_PERSONALITIES = frozenset(
    ('xenophobic', 'ruthless', 'aggressive', 'erratic', 'honorable', 'pacifist')
)
VALID_OBJECTIVES = frozenset(
    ('diplomat', 'militarist', 'expansionist', 'technologist', 'industrialist', 'ecologist')
)


class Empire:
    """
    A player's empire: binds a Race to in-game state.

    homeworld      -- StarSystem assigned during galaxy generation
    homeworld_planet -- the Planet marked as homeworld within that system
    explored_systems -- set of StarSystem names the empire has visited
    treasury       -- billion credits (BC)
    """

    def __init__(self, race, emperor_name, color, personality=None, objective=None):
        if not isinstance(race, Race):
            raise TypeError('race must be a Race instance')
        if not emperor_name:
            raise ValueError('emperor_name cannot be empty')
        if color not in VALID_COLORS:
            raise ValueError(f'Unknown color "{color}". Choose from: {sorted(VALID_COLORS)}')
        if personality is not None and personality not in VALID_PERSONALITIES:
            raise ValueError(f'Unknown personality "{personality}"')
        if objective is not None and objective not in VALID_OBJECTIVES:
            raise ValueError(f'Unknown objective "{objective}"')

        self.race = race
        self.emperor_name = emperor_name
        self.color = color
        self.personality = personality
        self.objective = objective

        self.homeworld = None
        self.homeworld_planet = None
        self.treasury = 0
        self.explored_systems = set()

    def __repr__(self):
        return (
            f'Empire({self.race.name!r}, emperor={self.emperor_name!r}, '
            f'color={self.color!r})'
        )
