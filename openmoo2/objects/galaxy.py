# vim: set ts=4 sw=4 et: coding=UTF-8

import math
import random

from .planet import Planet
from .system import StarSystem


# Star class: (spawn_weight, min_planets, max_planets, possible_environments)
_STAR_CONFIGS = {
    'blue':   (5,  1, 3, ['toxic', 'radiated']),
    'white':  (10, 1, 4, ['radiated', 'barren', 'desert']),
    'yellow': (25, 2, 5, ['desert', 'tundra', 'arid', 'terran', 'ocean', 'swamp', 'gaia']),
    'orange': (20, 1, 4, ['tundra', 'arid', 'desert', 'barren']),
    'red':    (25, 0, 3, ['radiated', 'barren', 'desert', 'tundra']),
    'gray':   (10, 0, 2, ['toxic', 'radiated', 'barren']),
    'black':  (5,  0, 0, []),
}

# Environment -> approximate organic richness
_ENV_ORGANICS = {
    'gaia':     'ultrarich',
    'terran':   'rich',
    'swamp':    'rich',
    'ocean':    'rich',
    'arid':     'average',
    'tundra':   'average',
    'desert':   'poor',
    'barren':   'poor',
    'radiated': 'ultrapoor',
    'toxic':    'ultrapoor',
}

_PLANET_SIZES = ['tiny', 'small', 'medium', 'large', 'huge']
_PLANET_MINERALS = ['ultrapoor', 'poor', 'average', 'rich', 'ultrarich']

_STAR_NAMES = [
    'Antares', 'Arcturus', 'Aldebaran', 'Altair', 'Algol', 'Alnitak', 'Alnilam', 'Alphard',
    'Alpheratz', 'Ankaa', 'Arneb', 'Ascella', 'Asellus', 'Atik', 'Atlas', 'Atria',
    'Avior', 'Barnard', 'Becrux', 'Bellatrix', 'Biham', 'Botein', 'Canopus', 'Capella',
    'Caph', 'Castor', 'Celaeno', 'Chara', 'Cursa', 'Dabih', 'Deneb', 'Denebola',
    'Diphda', 'Dschubba', 'Dubhe', 'Electra', 'Elnath', 'Eltanin', 'Enif', 'Errai',
    'Fomalhaut', 'Furud', 'Gacrux', 'Gienah', 'Gliese', 'Gomeisa', 'Groombridge',
    'Hadar', 'Hamal', 'Heze', 'Homam', 'Izar', 'Keid', 'Kochab', 'Kornephoros',
    'Lalande', 'Lesath', 'Maia', 'Markab', 'Menkent', 'Menkib', 'Merak', 'Merope',
    'Mimosa', 'Mintaka', 'Mira', 'Mirach', 'Mirfak', 'Mirzam', 'Mizar', 'Naos',
    'Nashira', 'Nekkar', 'Nihal', 'Nunki', 'Nusakan', 'Peacock', 'Phad', 'Pherkad',
    'Pleione', 'Polaris', 'Pollux', 'Porrima', 'Procyon', 'Proxima', 'Rasalas',
    'Rasalgethi', 'Rasalhague', 'Rastaban', 'Regulus', 'Rigel', 'Ross', 'Ruchbah',
    'Rukbat', 'Sabik', 'Sadr', 'Saiph', 'Sargas', 'Scheat', 'Schedar', 'Segin',
    'Shaula', 'Sheliak', 'Sheratan', 'Sirius', 'Sol', 'Spica', 'Suhail', 'Sulafat',
    'Tau Ceti', 'Taygeta', 'Tejat', 'Thuban', 'Toliman', 'Unukalhai', 'Vega',
    'Vindemiatrix', 'Wasat', 'Wolf', 'Xi Bootis', 'Zeta Puppis', 'Zosma',
    'Zubenelgenubi', 'Zubeneschamali', 'Epsilon Eridani', 'Mu Herculis',
]

_GALAXY_SIZES = {
    'tiny':   {'stars': 24,  'width': 100, 'height': 100},
    'small':  {'stars': 36,  'width': 150, 'height': 150},
    'medium': {'stars': 54,  'width': 200, 'height': 200},
    'large':  {'stars': 72,  'width': 250, 'height': 250},
    'huge':   {'stars': 108, 'width': 300, 'height': 300},
}


class Galaxy:
    """Procedurally generated MOO2-style galaxy."""

    VALID_SIZES = tuple(_GALAXY_SIZES.keys())

    def __init__(self, size='medium', num_players=2, seed=None):
        if size not in _GALAXY_SIZES:
            raise ValueError(f'Unknown galaxy size "{size}". Choose from: {self.VALID_SIZES}')
        if not (1 <= num_players <= 8):
            raise ValueError(f'num_players must be 1-8, got {num_players}')

        cfg = _GALAXY_SIZES[size]
        self.size = size
        self.num_players = num_players
        self.width = cfg['width']
        self.height = cfg['height']
        self.star_count = cfg['stars']
        self.systems = []

        if seed is not None:
            random.seed(seed)

    @property
    def _min_star_distance(self):
        """Minimum distance between stars, scaled to the galaxy's star density."""
        radius = min(self.width, self.height) / 2 * 0.9
        return math.sqrt(math.pi * radius ** 2 / self.star_count) * 0.55

    def generate(self):
        """Generate a complete galaxy and return the list of StarSystems."""
        StarSystem._systems.clear()
        self.systems = []

        positions = self._place_stars()
        star_classes = self._assign_star_classes()
        names = self._pick_names()

        for i, (x, y) in enumerate(positions):
            cls = star_classes[i]
            system = StarSystem(names[i], cls, x=x, y=y)
            self._generate_planets(system, cls)
            self.systems.append(system)

        self._place_orion()
        return self.systems

    # ------------------------------------------------------------------
    # Internal generation steps
    # ------------------------------------------------------------------

    def _place_stars(self):
        """Place stars in a circle using rejection sampling."""
        positions = []
        cx, cy = self.width / 2, self.height / 2
        radius = min(self.width, self.height) / 2 * 0.9
        min_dist = self._min_star_distance
        max_attempts = self.star_count * 200

        for _ in range(max_attempts):
            if len(positions) == self.star_count:
                break
            angle = random.uniform(0, 2 * math.pi)
            r = radius * math.sqrt(random.uniform(0, 1))
            x = round(cx + r * math.cos(angle), 1)
            y = round(cy + r * math.sin(angle), 1)
            if all(math.hypot(x - px, y - py) >= min_dist for px, py in positions):
                positions.append((x, y))

        if len(positions) < self.star_count:
            raise RuntimeError(
                f'Placed only {len(positions)}/{self.star_count} stars '
                f'(min distance {min_dist:.1f}). Try a larger galaxy or fewer players.'
            )
        return positions

    def _assign_star_classes(self):
        classes = list(_STAR_CONFIGS.keys())
        weights = [_STAR_CONFIGS[c][0] for c in classes]
        return random.choices(classes, weights=weights, k=self.star_count)

    def _pick_names(self):
        pool = list(_STAR_NAMES)
        if len(pool) < self.star_count:
            pool += [f'Star {i}' for i in range(1, self.star_count - len(pool) + 2)]
        random.shuffle(pool)
        return pool[:self.star_count]

    def _generate_planets(self, system, star_class):
        if star_class == 'black':
            return

        _, min_p, max_p, envs = _STAR_CONFIGS[star_class]
        count = random.randint(min_p, max_p)

        for _ in range(count):
            kind = self._random_planet_kind()
            if kind == 'asteroids':
                planet = Planet('asteroids')
            elif kind == 'giant':
                planet = Planet('giant')
            else:
                env = random.choice(envs)
                planet = Planet(
                    'planet',
                    size=random.choice(_PLANET_SIZES),
                    mineral=random.choice(_PLANET_MINERALS),
                    organic=_ENV_ORGANICS[env],
                    environment=env,
                )
            system.planets = planet

    def _random_planet_kind(self):
        """70% regular planet, 20% asteroids, 10% gas giant."""
        roll = random.random()
        if roll < 0.70:
            return 'planet'
        if roll < 0.90:
            return 'asteroids'
        return 'giant'

    def _place_orion(self):
        """Mark the most central non-black-hole system as the Orion special."""
        cx, cy = self.width / 2, self.height / 2
        candidates = [s for s in self.systems if s.color != 'black']
        if not candidates:
            return
        orion = min(candidates, key=lambda s: math.hypot(s.x - cx, s.y - cy))
        orion.special = 'orion'
