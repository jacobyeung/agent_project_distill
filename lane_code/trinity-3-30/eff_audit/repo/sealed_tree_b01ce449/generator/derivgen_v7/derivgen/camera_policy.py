"""Camera admission thresholds over exact GT and printed option scores."""
from decimal import Decimal

from .common import Refusal


def motion_reason(family, *, distance, horizontal, yaw):
    if family == 'camera_rotation' and abs(yaw) > 175:
        return 'near_wrap'
    if family == 'camera_displacement' and distance < .10:
        return 'tiny_motion'
    if family == 'camera_movement_direction' and horizontal < .15:
        return 'tiny_motion'
    return None


def direction_margins(scores):
    """Return the top-two gap in metres and as a fraction of the top score.

    Scores are printed to two decimals. Decimal arithmetic keeps the inclusive
    0.10 m and 10% boundaries independent of binary float subtraction.
    """
    ranked = sorted((Decimal(str(s)) for s in scores), reverse=True)
    if len(ranked) < 2:
        raise Refusal('unsupported_movement_option')
    top, second = ranked[:2]
    if top <= 0:
        raise Refusal('movement_no_positive_option')
    gap = top - second
    if gap < Decimal('.10') or gap < Decimal('.10') * top:
        raise Refusal('near_tie')
    return float(gap), float(gap / top)
