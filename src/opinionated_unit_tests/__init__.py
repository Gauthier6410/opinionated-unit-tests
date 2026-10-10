"""opinionated-unit-tests: unit conversions for distance, weight, and heat."""

from .core import (
    convert,
    convert_distance,
    convert_weight,
    convert_heat,
    register_unit,
    list_units,
    UnknownUnitError,
)

__all__ = [
    "convert",
    "convert_distance",
    "convert_weight",
    "convert_heat",
    "register_unit",
    "list_units",
    "UnknownUnitError",
]

__version__ = "0.1.0"
