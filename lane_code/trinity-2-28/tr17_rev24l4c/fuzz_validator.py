"""Reviewer fuzz of r1_launch22.validate_removals (read-only on the tree)."""
import itertools
import sys
from unittest.mock import patch

sys.path.insert(0, sys.argv[1])
from student_pilot import r1_launch22 as L

R, N, P = L.REMOVAL_ORDER, L.NAMING_REMOVE, L.POINTING_K1_REMOVE
EXT = R[:-1] + (P, N)
OTHER = 'f' * 64


def run(order, spec=None, extra=None):
    order = list(order)
    cfg = dict(remove_files=[dict(path='/x/%d' % i, sha256=h) for i, h in enumerate(order)],
               r1_training=dict(launch22=dict(removal_order=list(order) if spec is None else spec)))
    if extra:
        cfg['remove_files'][extra[0]].update(extra[1])
    with patch('student_pilot.p3_provenance.pinned') as pinned:
        try:
            L.validate_removals(cfg)
            return 'ACCEPT', pinned.call_args
        except ValueError as e:
            return str(e), None
        except Exception as e:
            return type(e).__name__, None


candidates = set()
pool = list(dict.fromkeys(R + (P, OTHER, P.upper(), P + ' ')))
for base in (R, EXT):
    n = len(base)
    for i in range(n + 1):
        for h in pool:
            candidates.add(base[:i] + (h,) + base[i:])
    for i in range(n):
        candidates.add(base[:i] + base[i + 1:])
        for h in pool:
            candidates.add(base[:i] + (h,) + base[i + 1:])
    for i, j in itertools.combinations(range(n), 2):
        b = list(base); b[i], b[j] = b[j], b[i]; candidates.add(tuple(b))
    candidates.add(base + base[-1:])
    candidates.add(tuple(reversed(base)))
candidates.add(())
candidates.add(R[:-1] + (P,))
candidates.add(R[:-1] + (P, P, N))
candidates.add(R[:-2] + (P, R[-2], N))
candidates.add(R[:-1] + (N, P, N))

accepted = []
for c in candidates:
    verdict, call = run(c)
    if verdict == 'ACCEPT':
        accepted.append(c)
    elif verdict != 'R1_NAMING_REMOVAL_ORDER':
        print('OTHER_REFUSAL', verdict, len(c))
print('candidates', len(candidates), 'accepted', len(accepted))
print('accepted == {R, EXT}:', set(accepted) == {R, EXT})

# spec mismatches with an accepted actual order
for actual, spec in ((EXT, list(R)), (R, list(EXT)), (EXT, tuple(EXT)), (EXT, list(EXT)[:-1]), (EXT, 'missing')):
    v, _ = run(actual, spec=spec)
    print('spec', len(actual), type(spec).__name__, v)

# missing launch22 spec but bound via naming pin
cfg = dict(remove_files=[dict(path='/x', sha256=h) for h in EXT], r1_training=dict(other=1))
try:
    L.validate_removals(cfg); print('no-spec: ACCEPT')
except ValueError as e:
    print('no-spec:', e)

# unbound config: r1_training absent -> validator returns without checks (pre-existing)
cfg = dict(remove_files=[dict(path='/x', sha256=h) for h in (P, OTHER)])
print('unbound returns', L.validate_removals(cfg))

# naming pin authentication target is still the last pin
v, call = run(EXT)
print('pinned called with last pin:', call)

# extra keys on the pointing pin are not inspected by the validator
v, _ = run(EXT, extra=(11, dict(defects=['extent'])))
print('pointing pin with defects key:', v)
