"""Tests for opinionated_unit_tests.core.

Conventions in this file:
- Float comparisons use ``math.isclose`` with relative tolerance 1e-9 and an
  absolute tolerance of 1e-12 so that very small and very large magnitudes
  both compare sensibly. ``==`` is never used on floats.
- Every test exercises behaviour the implementation genuinely claims to
  support; no test invents an unhandled edge case.
"""

import math
import unittest

from opinionated_unit_tests import (
    convert,
    convert_distance,
    convert_weight,
    convert_heat,
    register_unit,
    list_units,
    UnknownUnitError,
)


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)


class TestDistance(unittest.TestCase):
    def test_metre_to_centimetre(self):
        self.assertTrue(close(convert(1, "metre", "centimetre"), 100.0))

    def test_kilometre_to_mile(self):
        # 1 km = 1000 m; 1 mile = 1609.344 m  -> 0.621371192...
        self.assertTrue(close(convert(1, "kilometre", "mile"), 1000.0 / 1609.344))

    def test_roundtrip_idempotent(self):
        original = 42.195
        result = convert(convert(original, "kilometre", "inch"), "inch", "kilometre")
        self.assertTrue(close(result, original))

    def test_identity(self):
        self.assertTrue(close(convert(7.0, "metre", "metre"), 7.0))

    def test_negative_distance(self):
        # Distances are just real numbers here; sign is preserved.
        self.assertTrue(close(convert(-3, "foot", "inch"), -36.0))

    def test_int_input_returns_float(self):
        # Even when the result is a whole number, the return type is float.
        result = convert(2, "metre", "centimetre")
        self.assertIsInstance(result, float)
        self.assertTrue(close(result, 200.0))

    def test_convert_distance_direct(self):
        self.assertTrue(close(convert_distance(1, "yard", "metre"), 0.9144))


class TestWeight(unittest.TestCase):
    def test_kg_to_gram(self):
        self.assertTrue(close(convert(1, "kilogram", "gram"), 1000.0))

    def test_pound_to_ounce(self):
        # 1 lb = 0.45359237 kg; 1 oz = 0.028349523125 kg.
        self.assertTrue(close(convert(1, "pound", "ounce"),
                               0.45359237 / 0.028349523125))

    def test_tonne_to_kilogram(self):
        self.assertTrue(close(convert(2.5, "tonne", "kilogram"), 2500.0))

    def test_convert_weight_direct(self):
        self.assertTrue(close(convert_weight(500, "gram", "kilogram"), 0.5))


class TestHeat(unittest.TestCase):
    def test_celsius_to_kelvin(self):
        self.assertTrue(close(convert(0, "celsius", "kelvin"), 273.15))

    def test_kelvin_to_celsius(self):
        self.assertTrue(close(convert(300, "kelvin", "celsius"), 26.85))

    def test_fahrenheit_to_celsius_freeze(self):
        self.assertTrue(close(convert(32, "fahrenheit", "celsius"), 0.0))

    def test_celsius_to_fahrenheit_boil(self):
        self.assertTrue(close(convert(100, "celsius", "fahrenheit"), 212.0))

    def test_fahrenheit_to_kelvin(self):
        self.assertTrue(close(convert(32, "fahrenheit", "kelvin"), 273.15))

    def test_roundtrip_heat(self):
        original = 36.6
        result = convert(convert(original, "celsius", "fahrenheit"),
                         "fahrenheit", "celsius")
        self.assertTrue(close(result, original))

    def test_convert_heat_direct(self):
        self.assertTrue(close(convert_heat(25, "celsius", "fahrenheit"), 77.0))


class TestErrors(unittest.TestCase):
    def test_unknown_from_unit(self):
        with self.assertRaises(UnknownUnitError):
            convert(1, "smoot", "metre")

    def test_unknown_to_unit(self):
        with self.assertRaises(UnknownUnitError):
            convert(1, "metre", "parsec")

    def test_cross_category_rejected(self):
        with self.assertRaises(ValueError):
            convert(1, "metre", "kilogram")

    def test_bool_rejected(self):
        with self.assertRaises(TypeError):
            convert(True, "metre", "centimetre")

    def test_complex_rejected(self):
        with self.assertRaises(TypeError):
            convert(1 + 2j, "metre", "centimetre")

    def test_string_rejected(self):
        with self.assertRaises(TypeError):
            convert("1", "metre", "centimetre")

    def test_unknown_category_list_units(self):
        with self.assertRaises(UnknownUnitError):
            list_units("bogus")

    def test_convert_distance_unknown_unit(self):
        with self.assertRaises(UnknownUnitError):
            convert_distance(1, "metre", "furlong")


class TestRegistration(unittest.TestCase):
    def test_register_and_use_custom_unit(self):
        # Use the custom unit's own base to keep the test self-contained.
        register_unit(
            "distance",
            "smoot",
            to_base=lambda v: v * 1.7018,  # smoots to metres
            from_base=lambda v: v / 1.7018,  # metres to smoots
        )
        self.assertTrue(close(convert(1, "smoot", "metre"), 1.7018))
        self.assertTrue(close(convert(1.7018, "metre", "smoot"), 1.0))
        self.assertIn("smoot", list_units("distance"))

    def test_register_unit_in_new_category(self):
        register_unit(
            "volume",
            "cup",
            to_base=lambda v: v * 0.24,  # cups to litres
            from_base=lambda v: v / 0.24,
        )
        self.assertIn("cup", list_units("volume"))
        self.assertTrue(close(convert(2, "cup", "cup"), 2.0))


class TestListUnits(unittest.TestCase):
    def test_list_all_units_sorted(self):
        names = list_units()
        self.assertEqual(names, sorted(names))
        self.assertIn("metre", names)
        self.assertIn("kilogram", names)
        self.assertIn("kelvin", names)

    def test_list_distance_units(self):
        names = list_units("distance")
        self.assertIn("metre", names)
        self.assertIn("inch", names)
        self.assertNotIn("kilogram", names)


class TestFractionalInput(unittest.TestCase):
    def test_fraction_accepted_as_real(self):
        from fractions import Fraction
        result = convert(Fraction(1, 2), "metre", "centimetre")
        self.assertIsInstance(result, float)
        self.assertTrue(close(result, 50.0))


if __name__ == "__main__":
    unittest.main()
