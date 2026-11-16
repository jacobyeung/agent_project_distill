"""Require final family retention after authenticated scene exclusions."""
from .p3_provenance import load, pinned
from .r2_exclusions import ROLES

FAMILIES = {'units': ('units', 'a0_units'), 'recovery': ('recovery', 'a0_recovery'),
            'room': ('room', 'a0_room'),
            'distance': ('absolute_distance', 'a0_pool_abs_distance_reworded')}


def family_admission(reports):
    totals = {name: dict(eligible=0, admitted=0) for name in FAMILIES}
    for report in reports:
        names = [name for name, aliases in FAMILIES.items() if report['family'] in aliases]
        if not names:
            continue
        if any(any(type(c[k]) is not int or c[k] < 0 for k in ('seen', 'admitted', 'refused'))
               or c['seen'] != c['admitted'] + c['refused'] for c in report['counts'].values()):
            raise ValueError('Invalid family admission counts')
        seen = sum(c['seen'] for c in report['counts'].values())
        admitted = sum(c['admitted'] for c in report['counts'].values())
        # Only explicit scene-rule refusals leave the denominator. Unknown
        # overlap, invalid traces and missing frames still count as losses.
        allowed = {*ROLES, 'withheld_room', 'merged_dev_or_benchmark'}
        exclusions = sum(r['reason'].startswith('excluded:') and
                         set(r['reason'].split(':', 1)[1].split(',')) <= allowed
                         for r in report['refusals'])
        eligible = seen - exclusions
        if not 0 <= admitted <= eligible <= seen:
            raise ValueError('Invalid family admission counts')
        totals[names[0]]['eligible'] += eligible
        totals[names[0]]['admitted'] += admitted
    for name, counts in totals.items():
        if counts['eligible'] <= 0 or counts['admitted'] * 10 < counts['eligible'] * 9:
            raise ValueError('Family admission below 90%: '+name)
    return totals


def check_family_receipt(pin):
    if not pin:
        raise ValueError('Missing final family admission receipt')
    value = load(pinned(pin))
    if value.get('schema') != 'r2-materialization-v1' or value.get('status') != 'ready':
        raise ValueError('Family receipt is not a final materialization')
    return family_admission(value['intake'])
