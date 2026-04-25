# vim: set ts=4 sw=4 et: coding=UTF-8

import pytest
from openmoo2.objects.race import Race, CANONICAL_RACES, VALID_GOVERNMENTS, _NUMERIC_TRAITS, _BOOL_TRAITS


class TestRaceInit:

    def test_minimal_race(self):
        r = Race('TestRace')
        assert r.name == 'TestRace'
        assert r.government == 'democracy'

    def test_all_numeric_traits_default_zero(self):
        r = Race('Foo')
        for trait in _NUMERIC_TRAITS:
            assert getattr(r, trait) == 0, f'{trait} should default to 0'

    def test_all_bool_traits_default_false(self):
        r = Race('Foo')
        for trait in _BOOL_TRAITS:
            assert getattr(r, trait) is False, f'{trait} should default to False'

    def test_custom_government(self):
        for gov in VALID_GOVERNMENTS:
            r = Race('X', government=gov)
            assert r.government == gov

    def test_invalid_government(self):
        with pytest.raises(ValueError):
            Race('X', government='monarchy')

    def test_empty_name_rejected(self):
        with pytest.raises(ValueError):
            Race('')

    def test_unknown_trait_rejected(self):
        with pytest.raises(ValueError):
            Race('X', fire_breath=True)

    def test_numeric_trait_set(self):
        r = Race('X', farming=2, industry=-1, science=1)
        assert r.farming == 2
        assert r.industry == -1
        assert r.science == 1

    def test_bool_trait_set(self):
        r = Race('X', creative=True, repulsive=True)
        assert r.creative is True
        assert r.repulsive is True

    def test_bool_trait_coerced(self):
        r = Race('X', aquatic=1)
        assert r.aquatic is True

    def test_repr(self):
        r = Race('Human', government='democracy')
        assert 'Human' in repr(r)
        assert 'democracy' in repr(r)


class TestCanonicalRaces:

    def test_all_thirteen_races_present(self):
        expected = {
            'Alkari', 'Bulrathi', 'Darlok', 'Elerian', 'Gnolam', 'Human',
            'Klackon', 'Meklar', 'Mrrshan', 'Psilon', 'Sakkra', 'Silicoid', 'Trilarian'
        }
        assert set(CANONICAL_RACES.keys()) == expected

    def test_all_canonical_races_are_race_instances(self):
        for name, race in CANONICAL_RACES.items():
            assert isinstance(race, Race), f'{name} is not a Race'

    def test_human_is_democracy(self):
        assert CANONICAL_RACES['Human'].government == 'democracy'

    def test_klackon_is_unification(self):
        assert CANONICAL_RACES['Klackon'].government == 'unification'

    def test_psilon_is_creative(self):
        assert CANONICAL_RACES['Psilon'].creative is True

    def test_silicoid_is_lithovore(self):
        assert CANONICAL_RACES['Silicoid'].lithovore is True

    def test_silicoid_is_tolerant(self):
        assert CANONICAL_RACES['Silicoid'].tolerant is True

    def test_trilarian_is_aquatic(self):
        assert CANONICAL_RACES['Trilarian'].aquatic is True

    def test_meklar_is_cybernetic(self):
        assert CANONICAL_RACES['Meklar'].cybernetic is True

    def test_darlok_stealthy(self):
        assert CANONICAL_RACES['Darlok'].stealthy_ships is True

    def test_bulrathi_ground_combat(self):
        assert CANONICAL_RACES['Bulrathi'].ground_combat == 10

    def test_mrrshan_ship_attack(self):
        assert CANONICAL_RACES['Mrrshan'].ship_attack == 2

    def test_creative_and_uncreative_not_both_set(self):
        for name, race in CANONICAL_RACES.items():
            assert not (race.creative and race.uncreative), \
                f'{name} cannot be both creative and uncreative'
