"""Dump selected traces with the builder's per-item verdicts for manual review."""
import json, glob, sys, random
IN = '/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/'
OUT = '/scratch/jjyeung/orch_n30/sb_callrate/out/'
RETS = {'A4': IN + 'A4/ret/metadata/reads/0', 'B5': IN + 'B5/ret/metadata/reads/0',
        'b1r0': IN + 'bases/b1/work/ret/metadata/reads/0', 'b1r1': IN + 'bases/b1/work/ret/metadata/reads/1',
        'b2r0': IN + 'bases/b2/work/ret/metadata/reads/0'}


def rows(name):
    out = {}
    for p in sorted(glob.glob(RETS[name] + '/metadata/journals/*/*/items.jsonl')):
        for line in open(p):
            r = json.loads(line)
            out[r['id']] = r
    return out


def manifest(pkg):
    m = json.load(open(IN + pkg))
    return {i['id']: i for i in m['items']}


if __name__ == '__main__':
    side, ret, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
    verdict = json.load(open(OUT + ('room134' if ret in ('B5',) or side.startswith('room') else 'step200') + '/callrate.json'))['per_item']
    side = 'b' if side == 'roomb' else side
    items = {**manifest('A4/src/items/devs1_routed.json'), **manifest('B4/src/items/room134.json')}
    R = rows(ret)
    for k in ids:
        r = R[k]; o = r['output']; i = items[k]
        print('=' * 100)
        print(k, r['type'], '| finish', o.get('finish'), '| Q:', i['question'][:200])
        print('GT:', i.get('ground_truth', i.get('gt_answer')), '| options:', i.get('options'))
        for rec in o['calls'].get('records', []):
            print('  CALL', rec.get('call'), '| served', rec.get('served'), '| family', rec.get('family'), '| resp:', repr(rec.get('response', ''))[:300])
        t = o.get('text', '')
        print('  TEXT[-700:]:', repr(t[-700:]))
        print('  scores:', o.get('scores'))
        v = verdict['b' if side == 'b' else 'a'].get(k)
        print('  BUILDER:', json.dumps({x: v[x] for x in ('call', 'capped', 'answer', 'score', 'usage', 'usage_reason', 'response_decision', 'unit', 'finish')}) if v else None)
