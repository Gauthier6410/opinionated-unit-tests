"""Unit conversion engine for distance, weight, and heat.

All conversions flow through a single :func:`convert` function. The engine
stores every unit as a pair (to_base, from_base) where ``to_base`` converts a
value in that unit to the category's base unit and ``from_base`` converts back.
For most units these are plain multiplicative factors and ``from_base`` is
``1 / to_base``. For heat we use affine functions (Kelvin offset from Celsius)
so the pair is stored explicitly and neither member is the reciprocal of the
other.

Zero third-party dependencies: only the standard library is used.
"""

from __future__ import annotations

import numbers
from typing import Callable, Dict, List, Tuple


Category = str
UnitName = str
# A converter pair: (to_base, from_base). Each callable maps a number to a
# number. Storing both explicitly means affine conversions (e.g. Celsius)
# cost one extra closure but the hot path stays uniform and branch-free.
Converter = Tuple[Callable[[float], float], Callable[[float], float]]


_BASE_UNITS: Dict[Category, UnitName] = {
    "distance": "metre",
    "weight": "kilogram",
    "heat": "kelvin",
}


def _make_linear(factor: float) -> Converter:
    """Build a (to_base, from_base) pair for a multiplicative unit.

    Multiplicative units share the same code path regardless of category, so a
    small factory avoids duplicating the reciprocal while keeping the stored
    pair explicit (see module docstring for why we do not derive one from the
    other at call time).
    """
    return (lambda v: v * factor, lambda v: v / factor)


# Each unit maps to its category's base unit. Values for multiplicative units
# are stored as the factor to reach the base; the real converter pair is built
# lazily below so the table stays readable.
_RAW_UNITS: Dict[Category, Dict[UnitName, object]] = {
    "distance": {
        "metre": 1.0,
        "kilometre": 1000.0,
        "centimetre": 0.01,
        "millimetre": 0.001,
        "inch": 0.0254,
        "foot": 0.3048,
        "yard": 0.9144,
        "mile": 1609.344,
    },
    "weight": {
        "kilogram": 1.0,
        "gram": 0.001,
        "milligram": 0.000001,
        "tonne": 1000.0,
        "pound": 0.45359237,
        "ounce": 0.028349523125,
    },
    "heat": {
        # Heat is affine, not linear, so we store converter pairs directly.
        "kelvin": (lambda v: float(v), lambda v: float(v)),
        "celsius": (lambda v: v + 273.15, lambda v: v - 273.15),
        "fahrenheit": (
            lambda v: (v - 32.0) * 5.0 / 9.0 + 273.15,
            lambda v: (v - 273.15) * 9.0 / 5.0 + 32.0,
        ),
    },
}


def _build_table() -> Dict[Category, Dict[UnitName, Converter]]:
    table: Dict[Category, Dict[UnitName, Converter]] = {}
    for category, units in _RAW_UNITS.items():
        table[category] = {}
        for name, spec in units.items():
            if category == "heat":
                # spec is already a (to_base, from_base) converter pair.
                table[category][name] = spec  # type: ignore[assignment]
            else:
                table[category][name] = _make_linear(float(spec))  # type: ignore[arg-type]
    return table


_UNITS: Dict[Category, Dict[UnitName, Converter]] = _build_table()


class UnknownUnitError(KeyError):
    """Raised when a unit name is not registered.

    Subclasses :class:`KeyError` so callers using ``except KeyError`` still
    catch it, while giving a dedicated type for those who want to handle
    only unit lookup failures.
    """


def _resolve(category: Category, unit: UnitName) -> Converter:
    try:
        units = _UNITS[category]
    except KeyError as exc:
        raise UnknownUnitError(
            f"Unknown category: {category!r}"
        ) from exc
    try:
        return units[unit]
    except KeyError as exc:
        raise UnknownUnitError(
            f"Unknown {category} unit: {unit!r}"
        ) from exc


def _validate_value(value: object) -> float:
    """Accept any real number; reject bool, complex, and non-numbers.

    ``bool`` is a subclass of ``int`` in Python, which is almost never what a
    unit conversion caller intends. We reject it explicitly so that
    ``convert(True, ...)`` fails loudly rather than silently treating ``True``
    as 1.0. ``complex`` is rejected because there is no meaningful notion of
    ordering or scale comparison for imaginary measurements here.
    """
    if isinstance(value, bool):
        raise TypeError("value must be a real number, not bool")
    if isinstance(value, complex):
        raise TypeError("value must be a real number, not complex")
    if isinstance(value, numbers.Real):
        return float(value)
    raise TypeError(
        f"value must be a real number, got {type(value).__name__}"
    )


def _do_convert(value: float, from_unit: UnitName, to_unit: UnitName,
                category: Category) -> float:
    to_base, _ = _resolve(category, from_unit)
    _, from_base = _resolve(category, to_unit)
    return from_base(to_base(value))


def convert(value, from_unit: UnitName, to_unit: UnitName) -> float:
    """Convert ``value`` from one unit to another within the same category.

    The category is inferred from the units; both must belong to the same
    category. Mixing categories raises :class:`ValueError`.

    >>> convert(1, "metre", "centimetre")
    100.0
    """
    v = _validate_value(value)
    cat_from = _category_of(from_unit)
    cat_to = _category_of(to_unit)
    if cat_from is None:
        raise UnknownUnitError(f"Unknown unit: {from_unit!r}")
    if cat_to is None:
        raise UnknownUnitError(f"Unknown unit: {to_unit!r}")
    if cat_from != cat_to:
        raise ValueError(
            f"Cannot convert between categories: "
            f"{from_unit!r} ({cat_from}) -> {to_unit!r} ({cat_to})"
        )
    return _do_convert(v, from_unit, to_unit, cat_from)


def _category_of(unit: UnitName):
    for category, units in _UNITS.items():
        if unit in units:
            return category
    return None


def convert_distance(value, from_unit: UnitName, to_unit: UnitName) -> float:
    """Convert a distance measurement (e.g. metre, foot, mile)."""
    v = _validate_value(value)
    return _do_convert(v, from_unit, to_unit, "distance")


def convert_weight(value, from_unit: UnitName, to_unit: UnitName) -> float:
    """Convert a weight measurement (e.g. kilogram, pound, ounce)."""
    v = _validate_value(value)
    return _do_convert(v, from_unit, to_unit, "weight")


def convert_heat(value, from_unit: UnitName, to_unit: UnitName) -> float:
    """Convert a heat measurement between kelvin, celsius, and fahrenheit."""
    v = _validate_value(value)
    return _do_convert(v, from_unit, to_unit, "heat")


def register_unit(category: Category, unit: UnitName, *, to_base: Callable[[float], float],
                  from_base: Callable[[float], float]) -> None:
    """Register a custom unit at runtime.

    Both converters must be supplied explicitly because the library never
    assumes a unit is purely multiplicative (heat is affine). This keeps the
    storage shape identical for built-in and user units.
    """
    if category not in _UNITS:
        _UNITS[category] = {}
        _BASE_UNITS[category] = unit
    _UNITS[category][unit] = (to_base, from_base)


def list_units(category: Category = None) -> List[UnitName]:
    """Return sorted unit names.

    If ``category`` is given, only that category's units are listed. Otherwise
    all units across all categories are returned in a single sorted list.
    """
    if category is not None:
        if category not in _UNITS:
            raise UnknownUnitError(f"Unknown category: {category!r}")
        return sorted(_UNITS[category])
    all_names: List[UnitName] = []
    for units in _UNITS.values():
        all_names.extend(units)
    return sorted(all_names)
