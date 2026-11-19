"""Input-only checks for required training families; never convert an answer."""
from fractions import Fraction

UNITS = ('cm', 'ft', 'in')


def blockers(mix, counts):
    counts = counts if isinstance(counts, dict) else {}
    rates = {kind: sum((Fraction(cell['numerator'], cell['denominator'])
                       for cell in mix['cells'] if cell['stream'] == 'routing' and cell['type'] == kind), Fraction())
             for kind in ('recovery', 'units')}
    result = []
    recovery = counts.get('recovery')
    if rates['recovery'] <= 0 or type(recovery) is not int or recovery <= 0:
        result.append('RECOVERY_ROWS_ABSENT')
    units = counts.get('units')
    if (rates['units'] <= 0 or not isinstance(units, dict)
            or any(type(units.get(u)) is not int or units[u] <= 0 for u in UNITS)):
        result.append('UNIT_ROWS_ABSENT')
    return result


def require(mix, counts):
    missing = blockers(mix, counts)
    if missing:
        raise ValueError(','.join(missing))
    return counts
