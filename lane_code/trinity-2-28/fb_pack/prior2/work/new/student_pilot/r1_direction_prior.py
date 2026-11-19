"""Pinned toward-hard balance; preserve every other native draw and its position."""
from collections import Counter
from fractions import Fraction
import random
from .p3_provenance import digest, file_pin, load, pinned, write

CELLS = ('direction', 'facing_pairs')
WEIGHTS = {'direction': {'back': '10251/3676', 'front': '10251/16826'},
           'facing_pairs': {'back': '2180/651', 'front': '2180/3709'}}


class Prior:
    """Bind source row identities to offsets only after native reader filtering."""
    def __init__(self, pin):
        self.pin = pin
        value = load(pinned(pin))
        if (value.get('schema') != 'r1-direction-prior-v1'
                or value.get('policy') != 'toward_hard_equal_mass_v1'
                or set(value.get('cells', {})) != set(CELLS)
                or not value.get('inputs')):
            raise ValueError('R1_DIRECTION_PRIOR_INVALID')
        self.rows = {}
        self.cells = {k: {'front': [], 'back': []} for k in CELLS}
        self.seen = set()
        for kind in CELLS:
            cell = value['cells'][kind]
            if cell.get('weights') != WEIGHTS[kind]:
                raise ValueError('R1_DIRECTION_PRIOR_WEIGHTS')
            counts = Counter()
            for row in cell['rows']:
                qid, sha, side = row['qid'], row['row_sha256'], row['side']
                if (not isinstance(qid, str) or not qid or qid in self.rows
                        or side not in ('front', 'back') or not isinstance(sha, str)
                        or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha)):
                    raise ValueError('R1_DIRECTION_PRIOR_ROW')
                self.rows[qid] = (kind, sha, side)
                counts[side] += 1
            mass = sum(counts.values())
            if any(counts[side]*Fraction(WEIGHTS[kind][side]) != Fraction(mass, 2)
                   for side in ('front', 'back')) or not mass:
                raise ValueError('R1_DIRECTION_PRIOR_MASS')

    def observe(self, row, stream, kind, offset):
        from .r1_direction_twins import direction_details
        if stream != 'vqa':
            return
        entry = self.rows.get(row.get('qid'))
        if kind not in CELLS:
            if entry is not None:
                raise ValueError('R1_DIRECTION_PRIOR_CELL')
            return
        clause, difficulty, side, relation = direction_details(row)
        target = (clause, difficulty) == ('toward', 'hard')
        if not target:
            if entry is not None:
                raise ValueError('R1_DIRECTION_PRIOR_CLAUSE')
            return
        if (entry != (kind, digest(row), side) or side not in ('front', 'back')
                or relation != {'front': 'front', 'back': 'behind'}[side]):
            raise ValueError('R1_DIRECTION_PRIOR_IDENTITY')
        if row['qid'] in self.seen:
            raise ValueError('R1_DIRECTION_PRIOR_DUPLICATE')
        self.seen.add(row['qid'])
        self.cells[kind][side].append(offset)

    def bind(self, binding, output):
        if self.seen != set(self.rows):
            raise ValueError('R1_DIRECTION_PRIOR_POPULATION_DIFFERS')
        inputs = [self.pin, binding['card'], binding['population'], binding['indices']]
        write(output, dict(schema='r1-direction-prior-offsets-v1', policy=self.pin,
                          card_sha256=binding['card']['sha256'],
                          population_sha256=binding['population']['sha256'],
                          indices_sha256=binding['indices']['sha256'],
                          cells=self.cells, inputs=inputs))
        return file_pin(output)


def schedules(binding, card, indices, proof, pools):
    """Alternate the two equal weighted masses inside the existing toward-hard slots."""
    value = load(pinned(binding['direction_prior']))
    if (value.get('schema') != 'r1-direction-prior-offsets-v1'
            or any(value.get(k+'_sha256') != binding[k]['sha256']
                   for k in ('card', 'population', 'indices'))
            or set(value.get('cells', {})) != set(CELLS)):
        raise ValueError('R1_DIRECTION_PRIOR_BINDING')
    policy = Prior(value['policy'])  # Re-authenticate the source weight file on every plan.
    result = {}
    for kind in CELLS:
        cell = value['cells'][kind]
        if set(cell) != {'front', 'back'}:
            raise ValueError('R1_DIRECTION_PRIOR_OFFSETS')
        all_values = [i for side in ('front', 'back') for i in cell[side]]
        expected = Counter(side for k, sha, side in policy.rows.values() if k == kind)
        if (any(type(i) is not int for i in all_values)
                or len(set(all_values)) != len(all_values)
                or not set(all_values) <= set(indices['cells'].get(kind, []))
                or any(len(cell[side]) != expected[side] for side in ('front', 'back'))
                or next(c['stream'] for c in card['cells'] if c['type'] == kind) != 'vqa'):
            raise ValueError('R1_DIRECTION_PRIOR_OFFSETS')
        pool = pools[kind]
        original = [pool[i % len(pool)] for i in range(proof['draws'][kind])]
        targets = set(all_values)
        slots = [i for i, offset in enumerate(original) if offset in targets]
        # Independent RNGs cannot perturb a cell's native shuffle or another cell.
        sides = ['front', 'back']
        random.Random(digest([card['seed'], kind, 'phase'])).shuffle(sides)
        selected = {}
        for side in sides:
            selected[side] = list(cell[side])
            random.Random(digest([card['seed'], kind, side])).shuffle(selected[side])
        used = Counter()
        for j, slot in enumerate(slots):
            side = sides[j % 2]
            candidates = selected[side]
            if not candidates or used[side] >= 4*len(candidates):
                raise ValueError('R1_DIRECTION_PRIOR_CAPACITY')
            original[slot] = candidates[used[side] % len(candidates)]
            used[side] += 1
        if max(Counter(original).values(), default=0) > 4:
            raise ValueError('R1_REPEAT_LIMIT_EXCEEDED')
        result[kind] = original
    return result
