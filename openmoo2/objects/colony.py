# vim: set ts=4 sw=4 et: coding=UTF-8

import math

# Environment → food produced per farmer (MOO2 formula base)
_FOOD_BASE = {
    'toxic': 0, 'radiated': 0, 'barren': 0,
    'desert': 2, 'tundra': 2, 'ocean': 2, 'swamp': 2,
    'arid': 4, 'terran': 4, 'gaia': 6,
}

# Planet size → max-pop size multiplier
_SIZE_MULT = {'tiny': 5, 'small': 10, 'medium': 15, 'large': 20, 'huge': 25}

# Environment → terrain multiplier (%) for standard races
_TERRAIN_MULT_DEFAULT = {
    'toxic': 25, 'radiated': 25, 'barren': 25, 'desert': 25, 'tundra': 25,
    'ocean': 25, 'swamp': 40, 'arid': 60, 'terran': 80, 'gaia': 100,
}
# Aquatic races treat water worlds much more favourably
_TERRAIN_MULT_AQUATIC = {
    'toxic': 25, 'radiated': 25, 'barren': 25, 'desert': 25, 'tundra': 80,
    'ocean': 100, 'swamp': 80, 'arid': 60, 'terran': 100, 'gaia': 100,
}

# Mineral richness → base industry per worker
_MINERAL_BASE = {
    'ultrapoor': 1, 'poor': 2, 'average': 3, 'rich': 5, 'ultrarich': 8,
}

# Subterranean bonus pop per size class
_SUBTERRANEAN_BONUS = {'tiny': 2, 'small': 4, 'medium': 6, 'large': 8, 'huge': 10}

ROLES = ('farmer', 'worker', 'scientist')
RESEARCH_BASE = 3   # RP per scientist before racepick modifier


class Colony:
    """
    A colony on a planet.

    kind = 'colony' satisfies the Planet.colony setter's type check.

    Population is divided into farmers, workers, and scientists.
    Call process_turn() each game turn to advance growth and cache outputs.

    Growth uses the canonical MOO2 formula:
      b = floor(sqrt(2000 * pop * (max_pop - pop) / max_pop))
      a = 100 + race.population   (Sakkra: 100, most: 0)
      growth_increment = (a * b) / 100
    A new colonist appears when _growth_reserve reaches 1000.
    """

    kind = 'colony'   # satisfies Planet.colony type check

    def __init__(self, planet, race, name='Colony'):
        if planet.kind != 'planet':
            raise ValueError('Colony can only be placed on a planet, not asteroids/giant')
        self.planet = planet
        self.race = race
        self.name = name

        self._pop = {'farmer': 0, 'worker': 0, 'scientist': 0}
        self._growth_reserve = 0

        # Cached outputs, updated each turn
        self.food = 0
        self.industry = 0
        self.research = 0
        self.bc = 0

    # ------------------------------------------------------------------
    # Population
    # ------------------------------------------------------------------

    @property
    def population(self):
        return sum(self._pop.values())

    @property
    def farmers(self):
        return self._pop['farmer']

    @property
    def workers(self):
        return self._pop['worker']

    @property
    def scientists(self):
        return self._pop['scientist']

    def max_population(self):
        """Maximum colonists this planet can support for this race."""
        size = self.planet.size
        env = self.planet.environment

        size_mult = _SIZE_MULT[size]

        terrain_mult = (
            _TERRAIN_MULT_AQUATIC[env] if self.race.aquatic
            else _TERRAIN_MULT_DEFAULT[env]
        )
        if self.race.tolerant:
            terrain_mult = min(terrain_mult + 25, 100)

        bonus = _SUBTERRANEAN_BONUS[size] if self.race.subterranean else 0

        return round((size_mult * terrain_mult) / 100) + bonus

    def set_population(self, farmers, workers, scientists):
        """Assign the full population distribution at once."""
        if any(v < 0 for v in (farmers, workers, scientists)):
            raise ValueError('Colonist counts cannot be negative')
        total = farmers + workers + scientists
        if total > self.max_population():
            raise ValueError(
                f'Total {total} exceeds max population {self.max_population()}'
            )
        self._pop = {'farmer': farmers, 'worker': workers, 'scientist': scientists}

    def reassign(self, from_role, to_role, count=1):
        """Move `count` colonists between roles."""
        if from_role not in ROLES or to_role not in ROLES:
            raise ValueError(f'Roles must be one of {ROLES}')
        if from_role == to_role:
            return
        if self._pop[from_role] < count:
            raise ValueError(
                f'Only {self._pop[from_role]} {from_role}s available, '
                f'cannot move {count}'
            )
        self._pop[from_role] -= count
        self._pop[to_role] += count

    # ------------------------------------------------------------------
    # Per-turn calculations (pure, no side effects)
    # ------------------------------------------------------------------

    def calculate_food(self):
        """Food units produced this turn (before consumption)."""
        base = _FOOD_BASE[self.planet.environment]
        per_farmer = base + self.race.farming

        if self.race.aquatic and self.planet.environment in ('ocean', 'terran'):
            per_farmer += 1

        total = self._pop['farmer'] * per_farmer

        if self.race.government == 'unification':
            total = int(total * 1.5)

        return max(0, total)

    def calculate_industry(self):
        """Production points generated this turn (before pollution)."""
        base = _MINERAL_BASE[self.planet.mineral]
        per_worker = base + self.race.industry

        gravity = self.planet.gravity
        if gravity == 'heavy' and not self.race.high_g:
            per_worker = max(1, int(per_worker * 0.75))
        elif gravity == 'low' and not self.race.low_g:
            per_worker = max(1, int(per_worker * 0.75))

        return self._pop['worker'] * per_worker

    def calculate_research(self):
        """Research points generated this turn."""
        per_scientist = RESEARCH_BASE + self.race.science
        return self._pop['scientist'] * per_scientist

    def calculate_bc(self):
        """Trade income (BC) this turn. 1 BC per 2 colonists + money racepick."""
        return max(0, self.population // 2 + self.race.money)

    def calculate_food_balance(self):
        """Net food surplus (positive) or deficit (negative) this turn."""
        return self.calculate_food() - self.population

    def calculate_growth(self):
        """
        Growth increment to add to the reserve this turn.
        Reserve hits 1000 → one new colonist (placed as a farmer).
        """
        pop = self.population
        max_pop = self.max_population()
        if pop <= 0 or pop >= max_pop:
            return 0
        b = math.floor(math.sqrt(2000 * pop * (max_pop - pop) / max_pop))
        # race.population is the raw MOO2 bonus (0 for most races, 100 for Sakkra)
        a = 100 + self.race.population
        return int((a * b) / 100)

    # ------------------------------------------------------------------
    # Turn processing (has side effects)
    # ------------------------------------------------------------------

    def process_turn(self):
        """
        Advance the colony one turn.

        Recalculates all outputs, applies population growth, and returns a
        summary dict with the turn's results.
        """
        self.food = self.calculate_food()
        self.industry = self.calculate_industry()
        self.research = self.calculate_research()
        self.bc = self.calculate_bc()
        food_balance = self.food - self.population

        new_colonists = 0
        if self.population < self.max_population():
            self._growth_reserve += self.calculate_growth()
            while self._growth_reserve >= 1000 and self.population < self.max_population():
                self._growth_reserve -= 1000
                self._pop['farmer'] += 1
                new_colonists += 1
        else:
            self._growth_reserve = 0

        return {
            'food': self.food,
            'food_balance': food_balance,
            'industry': self.industry,
            'research': self.research,
            'bc': self.bc,
            'new_colonists': new_colonists,
            'population': self.population,
        }

    def __repr__(self):
        return (
            f'Colony({self.name!r}, pop={self.population}/{self.max_population()}, '
            f'f={self.farmers} w={self.workers} s={self.scientists})'
        )
