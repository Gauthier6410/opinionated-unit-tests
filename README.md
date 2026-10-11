# opinionated-unit-tests

Convert measurements across distance, weight, and heat scales with a single
`convert(value, from_unit, to_unit)` call. Categories are inferred from the
unit names, so you do not pass a category string for built-in units.

```python
from opinionated_unit_tests import (
    convert,
    convert_distance,
    convert_weight,
    convert_heat,
    register_unit,
    list_units,
    UnknownUnitError,
)

# 1 metre -> 100 centimetres
convert(1, "metre", "centimetre")          # 100.0

# 1 kilometre -> miles
convert(1, "kilometre", "mile")             # 0.621371192...

# Heat is affine, not multiplicative
convert(100, "celsius", "fahrenheit")       # 212.0
convert(32, "fahrenheit", "kelvin")          # 273.15

# Typed shortcuts if you prefer them
convert_distance(1, "yard", "metre")        # 0.9144
convert_weight(1, "pound", "ounce")         # 16.0
convert_heat(25, "celsius", "fahrenheit")    # 77.0

# Register your own unit at runtime
register_unit(
    "distance",
    "smoot",
    to_base=lambda v: v * 1.7018,
    from_base=lambda v: v / 1.7018,
)
convert(1, "smoot", "metre")                 # 1.7018

list_units("distance")                       # [..., 'smoot', ...]
```

## Why this exists

The problem is narrow: a small, dependency-free converter for the three
measurement families that show up constantly in exercises and small tools —
distance, weight, and heat. The trade-off is that the unit table is fixed and
hand-curated rather than loaded from a data file; you get a tiny, auditable
module instead of a comprehensive units database.

## Edge cases you will hit

- **Cross-category conversion is rejected.** `convert(1, "metre",
  "kilogram")` raises `ValueError`, not a silent zero or `None`. If you need
  to convert across categories, write your own caller — this library will not
  guess.

- **`bool` is rejected as a value.** Python's `bool` is a subclass of `int`, so
  without an explicit check `convert(True, ...)` would silently treat `True`
  as `1.0`. That is almost never what a caller means, so it raises
  `TypeError`.

- **Floats are returned, even for integer inputs.** Every conversion returns
  `float`; do not expect `int` back even when the result is a whole number.

- **Heat is affine.** Celsius and Fahrenheit offsets are handled with affine
  converter pairs, not plain multiplication, so `0 celsius -> 273.15 kelvin`
  rather than `0`. Do not add new heat units with a single multiplicative
  factor; supply both `to_base` and `from_base` callables to `register_unit`.
