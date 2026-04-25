# vim: set ts=4 sw=4 et: coding=UTF-8

import pytest
from openmoo2.objects.colony import Colony, RESEARCH_BASE, _FOOD_BASE, _MINERAL_BASE
from openmoo2.objects.planet import Planet
from openmoo2.objects.race import Race, CANONICAL_RACES


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def terran_large():
    return Planet('planet', size='large', environment='terran',
                  mineral='average', organic='rich')

@pytest.fixture
def gaia_huge():
    return Planet('planet', size='huge', environment='gaia',
                  mineral='rich', organic='ultrarich')

@pytest.fixture
def toxic_tiny():
    return Planet('planet', size='tiny', environment='toxic',
                  mineral='ultrapoor', organic='ultrapoor')

@pytest.fixture
def human():
    return CANONICAL_RACES['Human']

@pytest.fixture
def sakkra():
    return CANONICAL_RACES['Sakkra']

@pytest.fixture
def silicoid():
    return CANONICAL_RACES['Silicoid']

@pytest.fixture
def trilarian():
    return CANONICAL_RACES['Trilarian']

@pytest.fixture
def klackon():
    return CANONICAL_RACES['Klackon']

@pytest.fixture
def colony(terran_large, human):
    c = Colony(terran_large, human, name='Sol')
    c.set_population(farmers=2, workers=1, scientists=0)
    return c


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestColonyInit:

    def test_basic_creation(self, terran_large, human):
        c = Colony(terran_large, human, 'Sol')
        assert c.name == 'Sol'
        assert c.population == 0

    def test_default_name(self, terran_large, human):
        c = Colony(terran_large, human)
        assert c.name == 'Colony'

    def test_non_planet_raises(self, human):
        asteroid = Planet('asteroids')
        with pytest.raises(ValueError):
            Colony(asteroid, human)

    def test_giant_raises(self, human):
        giant = Planet('giant')
        with pytest.raises(ValueError):
            Colony(giant, human)

    def test_repr(self, colony):
        r = repr(colony)
        assert 'Sol' in r
        assert 'pop=' in r


# ---------------------------------------------------------------------------
# Max population
# ---------------------------------------------------------------------------

class TestMaxPopulation:

    def test_terran_large_human(self, terran_large, human):
        c = Colony(terran_large, human)
        # size_mult=20, terrain_mult=80 → round(1600/100)=16
        assert c.max_population() == 16

    def test_gaia_huge_human(self, gaia_huge, human):
        c = Colony(gaia_huge, human)
        # size_mult=25, terrain_mult=100 → 25
        assert c.max_population() == 25

    def test_toxic_tiny_human(self, toxic_tiny, human):
        c = Colony(toxic_tiny, human)
        # size_mult=5, terrain_mult=25 → round(125/100)=1
        assert c.max_population() == 1

    def test_aquatic_ocean_bonus(self, human, trilarian):
        ocean = Planet('planet', size='large', environment='ocean',
                       mineral='average', organic='rich')
        human_col = Colony(ocean, human)
        tril_col = Colony(ocean, trilarian)
        # Human: terrain_mult=25, Trilarian: terrain_mult=100
        assert tril_col.max_population() > human_col.max_population()

    def test_tolerant_bonus(self, toxic_tiny, human):
        silicoid = CANONICAL_RACES['Silicoid']
        human_col = Colony(toxic_tiny, human)
        sil_col = Colony(toxic_tiny, silicoid)
        # Silicoid is tolerant: +25 to terrain_mult (25+25=50 vs 25)
        assert sil_col.max_population() > human_col.max_population()

    def test_subterranean_bonus(self, terran_large, human, sakkra):
        human_col = Colony(terran_large, human)
        sakkra_col = Colony(terran_large, sakkra)
        # Sakkra subterranean: +8 for large
        assert sakkra_col.max_population() == human_col.max_population() + 8


# ---------------------------------------------------------------------------
# Population management
# ---------------------------------------------------------------------------

class TestPopulationManagement:

    def test_set_population(self, colony):
        colony.set_population(3, 2, 1)
        assert colony.farmers == 3
        assert colony.workers == 2
        assert colony.scientists == 1
        assert colony.population == 6

    def test_set_population_exceeds_max(self, colony):
        with pytest.raises(ValueError):
            colony.set_population(10, 10, 10)  # 30 >> max

    def test_set_population_negative(self, colony):
        with pytest.raises(ValueError):
            colony.set_population(-1, 0, 0)

    def test_reassign(self, colony):
        initial_farmers = colony.farmers
        colony.reassign('farmer', 'scientist', 1)
        assert colony.farmers == initial_farmers - 1
        assert colony.scientists == 1

    def test_reassign_too_many(self, colony):
        with pytest.raises(ValueError):
            colony.reassign('scientist', 'farmer', 99)

    def test_reassign_invalid_role(self, colony):
        with pytest.raises(ValueError):
            colony.reassign('farmer', 'soldier')

    def test_reassign_same_role_noop(self, colony):
        before = colony.farmers
        colony.reassign('farmer', 'farmer', 1)
        assert colony.farmers == before


# ---------------------------------------------------------------------------
# Food calculation
# ---------------------------------------------------------------------------

class TestFoodCalculation:

    def test_food_base_terran(self, terran_large, human):
        c = Colony(terran_large, human)
        c.set_population(farmers=3, workers=0, scientists=0)
        # terran base=4, human farming=0 → 3*4=12
        assert c.calculate_food() == 12

    def test_food_base_gaia(self, gaia_huge, human):
        c = Colony(gaia_huge, human)
        c.set_population(farmers=2, workers=0, scientists=0)
        # gaia base=6 → 2*6=12
        assert c.calculate_food() == 12

    def test_food_zero_on_toxic(self, toxic_tiny, human):
        c = Colony(toxic_tiny, human)
        c.set_population(farmers=1, workers=0, scientists=0)
        assert c.calculate_food() == 0

    def test_klackon_farming_bonus(self, terran_large, klackon):
        c = Colony(terran_large, klackon)
        c.set_population(farmers=2, workers=0, scientists=0)
        # terran base=4, klackon farming=1 → 2*(4+1)=10, then Unification +50% → 15
        assert c.calculate_food() == 15

    def test_aquatic_ocean_bonus(self, trilarian):
        ocean = Planet('planet', size='large', environment='ocean',
                       mineral='average', organic='rich')
        c = Colony(ocean, trilarian)
        c.set_population(farmers=2, workers=0, scientists=0)
        # ocean base=2, trilarian aquatic on ocean → +1 → 2*(2+1)=6
        assert c.calculate_food() == 6

    def test_aquatic_no_bonus_on_desert(self, trilarian):
        desert = Planet('planet', size='large', environment='desert',
                        mineral='average', organic='poor')
        c = Colony(desert, trilarian)
        c.set_population(farmers=2, workers=0, scientists=0)
        # desert base=2, no aquatic bonus → 2*2=4
        assert c.calculate_food() == 4

    def test_unification_bonus(self, terran_large, klackon):
        c = Colony(terran_large, klackon)
        c.set_population(farmers=2, workers=0, scientists=0)
        # 10 base * 1.5 = 15
        assert c.calculate_food() == 15

    def test_food_balance_surplus(self, colony):
        # 2 farmers on terran: 2*4=8 food, pop=3 → surplus=5
        assert colony.calculate_food_balance() == 8 - 3

    def test_food_balance_deficit(self, terran_large, human):
        c = Colony(terran_large, human)
        c.set_population(farmers=0, workers=3, scientists=3)
        assert c.calculate_food_balance() < 0


# ---------------------------------------------------------------------------
# Industry calculation
# ---------------------------------------------------------------------------

class TestIndustryCalculation:

    def test_average_mineral(self, terran_large, human):
        c = Colony(terran_large, human)
        c.set_population(farmers=0, workers=3, scientists=0)
        # average mineral base=3, human industry=0 → 3*3=9
        assert c.calculate_industry() == 9

    def test_rich_mineral(self, human):
        # Explicit medium gravity: large+rich auto-computes heavy, which would penalise industry
        rich = Planet('planet', size='large', environment='terran',
                      mineral='rich', organic='rich', gravity='medium')
        c = Colony(rich, human)
        c.set_population(farmers=0, workers=2, scientists=0)
        # rich base=5, medium gravity no penalty → 2*5=10
        assert c.calculate_industry() == 10

    def test_meklar_industry_bonus(self):
        meklar = CANONICAL_RACES['Meklar']
        planet = Planet('planet', size='large', environment='terran',
                        mineral='average', organic='rich')
        c = Colony(planet, meklar)
        c.set_population(farmers=0, workers=2, scientists=0)
        # average base=3, meklar industry=2 → 2*(3+2)=10
        assert c.calculate_industry() == 10

    def test_heavy_gravity_penalty(self, human):
        heavy_planet = Planet('planet', size='huge', environment='terran',
                              mineral='rich', organic='rich', gravity='heavy')
        c = Colony(heavy_planet, human)
        c.set_population(farmers=0, workers=4, scientists=0)
        # rich base=5, heavy gravity non-high_g → int(5*0.75)=3 → 4*3=12
        assert c.calculate_industry() == 12

    def test_zero_workers_zero_industry(self, colony):
        assert colony.calculate_industry() == 3  # 1 worker * 3 (average mineral)


# ---------------------------------------------------------------------------
# Research calculation
# ---------------------------------------------------------------------------

class TestResearchCalculation:

    def test_base_research(self, terran_large, human):
        c = Colony(terran_large, human)
        c.set_population(farmers=0, workers=0, scientists=3)
        # base=3, human science=0 → 3*3=9
        assert c.calculate_research() == 9

    def test_psilon_science_bonus(self, terran_large):
        psilon = CANONICAL_RACES['Psilon']
        c = Colony(terran_large, psilon)
        c.set_population(farmers=0, workers=0, scientists=3)
        # base=3, psilon science=1 → 3*(3+1)=12
        assert c.calculate_research() == 12

    def test_zero_scientists_zero_research(self, colony):
        assert colony.calculate_research() == 0


# ---------------------------------------------------------------------------
# BC calculation
# ---------------------------------------------------------------------------

class TestBCCalculation:

    def test_basic_bc(self, colony):
        # pop=3 → 3//2=1, human money=0 → bc=1
        assert colony.calculate_bc() == 1

    def test_gnolam_money_bonus(self, terran_large):
        gnolam = CANONICAL_RACES['Gnolam']
        c = Colony(terran_large, gnolam)
        c.set_population(farmers=2, workers=2, scientists=2)
        # pop=6 → 6//2=3, gnolam money=1 → bc=4
        assert c.calculate_bc() == 4


# ---------------------------------------------------------------------------
# Population growth
# ---------------------------------------------------------------------------

class TestGrowth:

    def test_no_growth_at_max(self, terran_large, human):
        c = Colony(terran_large, human)
        max_pop = c.max_population()
        c.set_population(farmers=max_pop, workers=0, scientists=0)
        assert c.calculate_growth() == 0

    def test_no_growth_at_zero(self, terran_large, human):
        c = Colony(terran_large, human)
        assert c.calculate_growth() == 0

    def test_growth_positive_mid_population(self, terran_large, human):
        c = Colony(terran_large, human)
        c.set_population(farmers=4, workers=4, scientists=0)
        assert c.calculate_growth() > 0

    def test_sakkra_grows_faster(self, terran_large, human, sakkra):
        human_col = Colony(terran_large, human)
        sakkra_col = Colony(terran_large, sakkra)
        pop = 6
        # Both at same absolute population (sakkra has higher max, so set same count)
        human_col.set_population(farmers=pop, workers=0, scientists=0)
        sakkra_col.set_population(farmers=pop, workers=0, scientists=0)
        assert sakkra_col.calculate_growth() > human_col.calculate_growth()

    def test_growth_reserve_accumulates(self, terran_large, human):
        c = Colony(terran_large, human)
        c.set_population(farmers=3, workers=3, scientists=0)
        c.process_turn()
        assert c._growth_reserve > 0

    def test_new_colonist_appears(self, terran_large, human):
        c = Colony(terran_large, human)
        c.set_population(farmers=8, workers=0, scientists=0)
        # Force growth to trigger in one turn
        c._growth_reserve = 950
        result = c.process_turn()
        assert result['new_colonists'] >= 1
        assert c.population > 8

    def test_no_growth_beyond_max(self, terran_large, human):
        c = Colony(terran_large, human)
        max_pop = c.max_population()
        c.set_population(farmers=max_pop - 1, workers=0, scientists=0)
        # Force accumulation way over threshold
        c._growth_reserve = 9999
        c.process_turn()
        assert c.population <= max_pop


# ---------------------------------------------------------------------------
# process_turn integration
# ---------------------------------------------------------------------------

class TestProcessTurn:

    def test_turn_returns_expected_keys(self, colony):
        result = colony.process_turn()
        for key in ('food', 'food_balance', 'industry', 'research', 'bc',
                    'new_colonists', 'population'):
            assert key in result

    def test_outputs_match_calculations(self, colony):
        expected_food = colony.calculate_food()
        expected_industry = colony.calculate_industry()
        result = colony.process_turn()
        assert result['food'] == expected_food
        assert result['industry'] == expected_industry

    def test_multiple_turns_grow_population(self, terran_large, human):
        c = Colony(terran_large, human)
        c.set_population(farmers=8, workers=0, scientists=0)
        initial_pop = c.population
        for _ in range(20):
            c.process_turn()
        assert c.population > initial_pop
