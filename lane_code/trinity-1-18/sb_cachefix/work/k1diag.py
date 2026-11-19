"""Diagnostic A0 reruns of sb_kbox4's K1 box ladder: today's cache_for/lift against the patched copy.

usage: k1diag.py VARIANT SHARD NSHARDS
  today        unpatched A4 modules, sb_kbox4 cache_detect (raw-name pool, one presence per frame)
  fixed        patched modules, raw-name pool with each entry's own source_presence (no guard)
  alias_today  unpatched modules, raw+alias merged pool, each entry's own source_presence
  alias_fixed  patched modules, the same merged pool
sb_kbox4 code and data are imported read-only; outputs go to work/k1diag/VARIANT/.
"""
import gzip, hashlib, importlib.util, json, sys, time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
KBOX = Path('/scratch/jjyeung/orch_n30/sb_kbox4')
PATCHED = HERE/'patched/src/tree/student_pilot'
VARIANTS = {'today': (False, 'kbox'), 'fixed': (True, 'raw'), 'alias_today': (False, 'merged'),
            'alias_fixed': (True, 'merged')}
variant, shard, nshards = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
patched, pool = VARIANTS[variant]

sys.path.insert(0, str(KBOX))
import adapters  # noqa: E402,F401  (puts the sb_kbox4 tree and vendor on sys.path)
import student_pilot  # noqa: E402
if patched:
    for module in ('routed_candidates', 'routed_features'):
        spec = importlib.util.spec_from_file_location(f'student_pilot.{module}', PATCHED/f'{module}.py')
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        setattr(student_pilot, module, mod)
import torch  # noqa: E402
import serving_reference as R  # noqa: E402
import train_pricing as T  # noqa: E402
import predicted  # noqa: E402

F = R.F
assert Path(F.__file__).resolve().parent == (PATCHED if patched else Path(R.TREE)/'student_pilot').resolve()
assert Path(F.candidates.__file__).resolve().parent == Path(F.__file__).resolve().parent


def decode(rle):
    h, w = rle['size']
    counts = np.asarray(rle['counts'], np.int64)
    if np.any(counts < 0) or counts.sum() != h*w:
        raise ValueError('invalid_rle')
    return np.repeat(np.arange(len(counts)) % 2 == 1, counts).reshape((h, w), order='F')


def per_instance_detect(cache, stats):
    """K1 retention (joint >= .05 on the entry's own presence, cap 30) with one presence per entry."""
    def detect(name):
        frames = []
        for slot in range(32):
            record = cache['frames'][str(slot)]['phrases'].get(name)
            if record is None:
                frames.append([])
                continue
            pres = float(record['presence'])
            entries = [p for p in record.get('instances', []) if pool == 'merged' or p.get('source_prompt', name) == name]
            values = [(p, float(p.get('source_presence', pres))) for p in sorted(entries, key=lambda p: -float(p['score']))]
            values = [(p, q) for p, q in values if float(p['score'])*q >= .05][:30]
            if len({q for _, q in values}) > 1:
                stats['mixed_frames'] += 1
            frames.append([dict(mask=F.resize(decode(p['mask']), F.SHAPE), score=float(p['score']), presence=q)
                           for p, q in values])
        return frames
    return detect


def digest(arrays):
    h = hashlib.sha256()
    for a in arrays:
        h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


def main():
    caps, labels, rowids, tableids, folds, truth, head = T.setup()
    torch.set_num_threads(1)
    common = dict(R.PINS)
    from selector_inputs import FIELDS
    ip, lo, hi = (FIELDS.index(k) for k in ('sam_presence_members', 'presence_min', 'presence_max'))
    out = HERE/'k1diag'/variant
    out.mkdir(parents=True, exist_ok=True)
    for c in sorted(caps, key=lambda c: c['canonical'])[shard::nshards]:
        dest = out/(c['canonical'].replace('/', '__')+'.json')
        if dest.exists():
            continue
        start = time.monotonic()
        R.PINS.clear(); R.PINS.update(common)
        rows = [r for r in c['rows'] if r['id'] in rowids]
        geo, cache, meta, _, _ = R.geometry(c)
        gt, gt_raw = R.gt_arrays(c)
        gt['raster'] = gt_raw.get('inst', gt_raw.get('instances')); gt['valid'] = gt_raw['valid'].astype(bool)
        stats = dict(mixed_frames=0)
        if pool == 'kbox':
            T.cache_detect = predicted.cache_detect
        else:
            T.cache_detect = lambda cache: per_instance_detect(cache, stats)
        if pool == 'merged':
            ref = dict(rows=[], same_geometry=False)
        else:
            ref = json.loads(gzip.decompress(R.read(R.TABLES/(c['canonical'].replace('/', '__')+'.json.gz'))))
        names = sorted({n for r in rows for n in r['operands']})
        objects = T.Objects(c, cache, geo, head, gt, ref)
        seen, features = {}, objects.stage.features

        def record_features(name):
            seen[name] = features(name)
            return seen[name]
        objects.stage.features = record_features
        values = {n: objects.get(n, 'A0') for n in names}
        items = T.evaluate(c, rows, geo, {n: v[0] for n, v in values.items()}, variant, 'best1', labels, folds,
                           truth, gt, {n: v[1] for n, v in values.items()}, meta)
        detail = {}
        for n in names:
            d = objects.data[n]
            accepted = [a['candidate_id'] for a in d['accepted']]
            props = [p for t in d['tracks'] for p in t.proposals]
            vectors = np.asarray(seen[n][1], float).reshape(-1, len(FIELDS))
            outside = int(np.sum(~((vectors[:, lo]-1e-9 <= vectors[:, ip]) & (vectors[:, ip] <= vectors[:, hi]+1e-9)))) if len(vectors) else 0
            detail[n] = dict(accepted=accepted, A0=d['A0'], selected=accepted[d['A0']] if d['A0'] >= 0 else None,
                             x_sha256=digest([vectors]),
                             proposals_sha256=digest([np.array([(p.frame, p.index, p.score, p.presence) for p in props], float)]
                                                     + [p.mask for p in props]),
                             presence_outside_lift_range=outside, candidates=len(accepted))
        record = dict(capture=c['canonical'], variant=variant, patched=patched, pool=pool,
                      module_sha256={m: hashlib.sha256(Path(sys.modules[f'student_pilot.{m}'].__file__).read_bytes()).hexdigest()
                                     for m in ('routed_features', 'routed_candidates')},
                      mixed_frames=stats['mixed_frames'], names=detail,
                      rows=[dict(row_id=r['row_id'], room=r['room'], label=r['label'], prediction=r['prediction'],
                                 refusal_code=r['refusal_code'], box=r['box'], member_frames=r['member_frames'])
                            for r in items],
                      seconds=time.monotonic()-start)
        dest.write_text(json.dumps(R.clean(record), allow_nan=False)+'\n')
        print(json.dumps(dict(capture=c['canonical'], variant=variant, seconds=record['seconds'])), flush=True)


if __name__ == '__main__':
    main()
