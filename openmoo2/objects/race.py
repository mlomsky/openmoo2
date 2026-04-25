# vim: set ts=4 sw=4 et: coding=UTF-8

# Numeric traits are signed modifiers (e.g. farming=+1, science=-1).
# Boolean traits are flags.
_NUMERIC_TRAITS = (
    'population', 'farming', 'industry', 'science', 'money',
    'ship_defense', 'ship_attack', 'ground_combat', 'spying',
)
_BOOL_TRAITS = (
    'low_g', 'high_g', 'aquatic', 'subterranean',
    'large_homeworld', 'rich_homeworld', 'artifacts_homeworld',
    'cybernetic', 'lithovore', 'repulsive', 'charismatic',
    'uncreative', 'creative', 'tolerant', 'fantastic_traders',
    'telepathic', 'lucky', 'omniscient', 'stealthy_ships',
    'trans_dimensional', 'warlord',
)

VALID_GOVERNMENTS = frozenset(
    ('feudal', 'dictatorship', 'imperium', 'democracy', 'unification')
)


class Race:
    """A species defined by its government and racial trait picks."""

    def __init__(self, name, government='democracy', **traits):
        if not name:
            raise ValueError('Race name cannot be empty')
        if government not in VALID_GOVERNMENTS:
            raise ValueError(f'Unknown government "{government}"')

        self.name = name
        self.government = government

        for trait in _NUMERIC_TRAITS:
            setattr(self, trait, traits.get(trait, 0))
        for trait in _BOOL_TRAITS:
            setattr(self, trait, bool(traits.get(trait, False)))

        unknown = set(traits) - set(_NUMERIC_TRAITS) - set(_BOOL_TRAITS)
        if unknown:
            raise ValueError(f'Unknown traits: {unknown}')

    def __repr__(self):
        return f'Race({self.name!r}, government={self.government!r})'


# The 13 canonical MOO2 races with their default trait picks.
CANONICAL_RACES = {
    'Alkari': Race(
        'Alkari', government='feudal',
        ship_attack=1, ship_defense=1, low_g=True, repulsive=True,
    ),
    'Bulrathi': Race(
        'Bulrathi', government='feudal',
        ground_combat=10, large_homeworld=True,
    ),
    'Darlok': Race(
        'Darlok', government='dictatorship',
        spying=10, stealthy_ships=True, repulsive=True,
    ),
    'Elerian': Race(
        'Elerian', government='dictatorship',
        telepathic=True, trans_dimensional=True, low_g=True, farming=-1,
    ),
    'Gnolam': Race(
        'Gnolam', government='feudal',
        money=1, fantastic_traders=True, lucky=True, low_g=True,
    ),
    'Human': Race(
        'Human', government='democracy',
        spying=1, charismatic=True, fantastic_traders=True,
    ),
    'Klackon': Race(
        'Klackon', government='unification',
        farming=1, industry=1, uncreative=True,
    ),
    'Meklar': Race(
        'Meklar', government='dictatorship',
        industry=2, cybernetic=True, uncreative=True,
    ),
    'Mrrshan': Race(
        'Mrrshan', government='feudal',
        ship_attack=2, warlord=True,
    ),
    'Psilon': Race(
        'Psilon', government='democracy',
        science=1, creative=True,
    ),
    'Sakkra': Race(
        'Sakkra', government='dictatorship',
        population=100, farming=1, subterranean=True,  # +100 growth bonus (double rate)
    ),
    'Silicoid': Race(
        'Silicoid', government='feudal',
        lithovore=True, tolerant=True, population=-20,  # slow-growing rock creatures
    ),
    'Trilarian': Race(
        'Trilarian', government='democracy',
        aquatic=True, trans_dimensional=True,
    ),
}
