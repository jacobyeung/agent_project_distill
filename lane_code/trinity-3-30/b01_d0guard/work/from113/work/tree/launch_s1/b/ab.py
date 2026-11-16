"""Step 1's rows on CP1-R's trainer (e6456bc): usage ab.py OLD_TREE CFG_JSON OUT_STEM.
The old trainer runs its own first_batch_check at world 32 (no reference_world_size, recipe from its recipe_for) on the
receipt that the new trainer prepared, on the same device. ab.py then compares every (stream, index) row with the new
trainer's records in OUT_STEM.c0.json and writes OUT_STEM.abcmp.json. A failure is recorded there and exits 0."""
import copy, hashlib, json, math, sys, traceback
from pathlib import Path


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=1, sort_keys=True) + '\n')


def compare(new, old):
    def key(r): return (r['stream'], r['index'])
    a, b = {key(r): r for r in new}, {key(r): r for r in old}
    out = dict(rows_new=len(a), rows_old=len(b), same_rows=sorted(a) == sorted(b), streams={})
    for k in sorted(set(a) & set(b)):
        x, y = a[k], b[k]
        s = out['streams'].setdefault(k[0], dict(rows=0, both_finite=0, both_error=0, mismatch_status=0, tokens_equal=0,
                                                 loss_exact=0, max_abs_loss=0., max_rel_loss=0., components_equal_keys=0,
                                                 max_rel_component=0.,
                                                 errors_new=[], errors_old=[]))
        s['rows'] += 1
        if x.get('finite') and y.get('finite'):
            s['both_finite'] += 1
            s['tokens_equal'] += x['tokens'] == y['tokens']
            s['loss_exact'] += x['loss'] == y['loss']
            d = abs(x['loss'] - y['loss'])
            s['max_abs_loss'] = max(s['max_abs_loss'], d)
            s['max_rel_loss'] = max(s['max_rel_loss'], d / max(abs(x['loss']), 1e-12))
            s['components_equal_keys'] += sorted(x['components']) == sorted(y['components'])
            for c in set(x['components']) & set(y['components']):
                d = abs(x['components'][c] - y['components'][c])
                s['max_rel_component'] = max(s['max_rel_component'], d / max(abs(x['components'][c]), 1e-6))
        elif 'error' in x and 'error' in y:
            s['both_error'] += 1
        else:
            s['mismatch_status'] += 1
        for r, name in ((x, 'errors_new'), (y, 'errors_old')):
            if 'error' in r and len(s[name]) < 3:
                s[name].append(r['error'][:200])
    # A stream whose rows failed on both trainers proves nothing; it is listed as untested and never passes alone.
    out['untested_streams'] = sorted(k for k, s in out['streams'].items() if s['both_finite'] == 0)
    out['inert'] = bool(out['same_rows'] and len(out['untested_streams']) < len(out['streams']) and all(
        s['mismatch_status'] == 0 and s['tokens_equal'] == s['both_finite'] and s['max_rel_loss'] <= 1e-3
        and s['max_rel_component'] <= 1e-3 and s['components_equal_keys'] == s['both_finite']
        for s in out['streams'].values()))
    return out


def main(old_tree, cfg_path, stem):
    stem = Path(stem)
    result = dict(schema='c1-trainer-ab-v1', old_tree=old_tree)
    try:
        sys.path.insert(0, old_tree)
        from student_pilot import carrier_c1_run as run
        from student_pilot.carrier_c1_sweep import recipe_for
        if Path(run.__file__).resolve().parents[1] != Path(old_tree).resolve():
            raise RuntimeError('old trainer not imported: ' + run.__file__)
        cfg = json.loads(Path(cfg_path).read_text())
        old = copy.deepcopy(cfg)
        old.pop('reference_world_size', None)
        old['world_size'] = 32
        old.pop('recipe', None)
        old['recipe'] = recipe_for(old)
        if not old.get('preparation'):
            receipt = Path(old['preparation_output']) / 'receipt.json'
            old['preparation'] = {'path': str(receipt), 'sha256': hashlib.sha256(receipt.read_bytes()).hexdigest()}
        result.update(preparation=old['preparation'], old_recipe_world=old['recipe']['world_size'])
        device = 'cuda' if run.torch.cuda.is_available() else 'cpu'
        records = run.first_batch_check(old, list(range(32)), stem.with_suffix('.ab.json'), device=device)
        new = json.loads(stem.with_suffix('.c0.json').read_text())['records']
        result.update(status='DONE', device=device, **compare(new, records))
    except Exception as exc:
        result.update(status='ERROR', error=f'{type(exc).__name__}: {str(exc)[:600]}', trace=traceback.format_exc()[-3000:])
    write(stem.with_suffix('.abcmp.json'), result)
    print(json.dumps({'trainer_ab': {k: result.get(k) for k in ('status', 'inert', 'same_rows', 'error')}}), flush=True)


if __name__ == '__main__':
    main(*sys.argv[1:4])
