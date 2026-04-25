# vim: set ts=4 sw=4 et: coding=UTF-8

import math
import pytest

from openmoo2.objects.galaxy import Galaxy, _STAR_CONFIGS, _GALAXY_SIZES
from openmoo2.objects.system import StarSystem


@pytest.fixture(autouse=True)
def clear_star_registry():
    """Ensure StarSystem name registry is clean before and after each test."""
    StarSystem._systems.clear()
    yield
    StarSystem._systems.clear()


@pytest.fixture
def small_galaxy():
    return Galaxy(size='tiny', seed=42).generate()


class TestGalaxyInit:

    def test_valid_sizes(self):
        for size in ('tiny', 'small', 'medium', 'large', 'huge'):
            g = Galaxy(size=size)
            assert g.size == size

    def test_invalid_size(self):
        with pytest.raises(ValueError):
            Galaxy(size='gargantuan')

    def test_num_players_bounds(self):
        Galaxy(num_players=1)
        Galaxy(num_players=8)
        with pytest.raises(ValueError):
            Galaxy(num_players=0)
        with pytest.raises(ValueError):
            Galaxy(num_players=9)

    def test_star_count_matches_size(self):
        for size, cfg in _GALAXY_SIZES.items():
            g = Galaxy(size=size)
            assert g.star_count == cfg['stars']


class TestGalaxyGenerate:

    def test_returns_correct_star_count(self):
        for size, cfg in _GALAXY_SIZES.items():
            systems = Galaxy(size=size, seed=1).generate()
            assert len(systems) == cfg['stars'], f'Wrong star count for {size}'

    def test_all_systems_have_coordinates(self, small_galaxy):
        for system in small_galaxy:
            assert system.x is not None
            assert system.y is not None

    def test_stars_within_galaxy_bounds(self, small_galaxy):
        g = Galaxy(size='tiny')
        for system in small_galaxy:
            assert 0 <= system.x <= g.width
            assert 0 <= system.y <= g.height

    def test_no_two_stars_overlap(self, small_galaxy):
        min_dist = Galaxy(size='tiny')._min_star_distance
        for i, a in enumerate(small_galaxy):
            for b in small_galaxy[i + 1:]:
                dist = math.hypot(a.x - b.x, a.y - b.y)
                assert dist >= min_dist - 0.01, (
                    f'{a.name} and {b.name} are too close: {dist:.2f} < {min_dist:.2f}'
                )

    def test_all_systems_have_unique_names(self, small_galaxy):
        names = [s.name for s in small_galaxy]
        assert len(names) == len(set(names))

    def test_seeded_galaxy_is_reproducible(self):
        StarSystem._systems.clear()
        g1 = Galaxy(size='tiny', seed=99).generate()
        StarSystem._systems.clear()
        g2 = Galaxy(size='tiny', seed=99).generate()
        assert [s.name for s in g1] == [s.name for s in g2]
        assert [(s.x, s.y) for s in g1] == [(s.x, s.y) for s in g2]

    def test_different_seeds_differ(self):
        StarSystem._systems.clear()
        g1 = Galaxy(size='tiny', seed=1).generate()
        StarSystem._systems.clear()
        g2 = Galaxy(size='tiny', seed=2).generate()
        names1 = [s.name for s in g1]
        names2 = [s.name for s in g2]
        assert names1 != names2


class TestStarClasses:

    def test_all_star_classes_are_valid(self, small_galaxy):
        valid = set(_STAR_CONFIGS.keys())
        for system in small_galaxy:
            assert system.color in valid, f'Unknown star class: {system.color}'

    def test_black_hole_has_no_planets(self, small_galaxy):
        for system in small_galaxy:
            if system.color == 'black':
                assert system.planets == {x + 1: None for x in range(StarSystem.max_planets)}


class TestPlanetGeneration:

    def test_planet_counts_within_range(self, small_galaxy):
        for system in small_galaxy:
            if system.color == 'black':
                continue
            _, min_p, max_p, _ = _STAR_CONFIGS[system.color]
            count = len(system.planets)
            assert min_p <= count <= max_p, (
                f'{system.name} ({system.color}): {count} planets, expected {min_p}-{max_p}'
            )

    def test_planet_environments_match_star_class(self, small_galaxy):
        for system in small_galaxy:
            if system.color in ('black', 'gray', 'red'):
                continue
            _, _, _, valid_envs = _STAR_CONFIGS[system.color]
            for planet in system.planets.values():
                if planet is not None and planet.kind == 'planet':
                    assert planet.environment in valid_envs, (
                        f'{system.name} ({system.color}): '
                        f'unexpected environment {planet.environment}'
                    )

    def test_planet_sizes_are_valid(self, small_galaxy):
        valid_sizes = {'tiny', 'small', 'medium', 'large', 'huge'}
        for system in small_galaxy:
            for planet in system.planets.values():
                if planet is not None and planet.kind == 'planet':
                    assert planet.size in valid_sizes

    def test_planet_minerals_are_valid(self, small_galaxy):
        valid_minerals = {'ultrapoor', 'poor', 'average', 'rich', 'ultrarich'}
        for system in small_galaxy:
            for planet in system.planets.values():
                if planet is not None and planet.kind == 'planet':
                    assert planet.mineral in valid_minerals


class TestOrionPlacement:

    def test_exactly_one_orion(self, small_galaxy):
        orion_systems = [s for s in small_galaxy if s.special == 'orion']
        assert len(orion_systems) == 1

    def test_orion_is_not_black_hole(self, small_galaxy):
        orion = next(s for s in small_galaxy if s.special == 'orion')
        assert orion.color != 'black'

    def test_orion_is_near_center(self, small_galaxy):
        g = Galaxy(size='tiny')
        cx, cy = g.width / 2, g.height / 2
        orion = next(s for s in small_galaxy if s.special == 'orion')
        dist_to_center = math.hypot(orion.x - cx, orion.y - cy)
        # Orion should be closer to center than 40% of galaxy radius
        assert dist_to_center < min(g.width, g.height) * 0.4
