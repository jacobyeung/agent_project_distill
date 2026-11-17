"""Smoke comparison of the first tower-arm distance reads (read 0 = null slot kept).
Usage: smoke_cmp.py ITEMS.jsonl [N_PAIRS=20] [RULE=null_argmax|candidates_argmax]
Compares per (item, name) ground status with (a) the CPU replay on tower geometry, kept rule (replay_out2, geo tower, null_argmax),
(b) job 170056's native tower statuses (n2r_calls.json), (c) H1-0 own arm (170706). Prints errors and finish reasons."""
import json, re, sys
RP = '/scratch/jjyeung/orch_n30/reader_r1/work/b1/in/replay/'
OWN = '/scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/h10own/170706/items.jsonl'
def st(resp):
    return 'not seen' if resp.strip().endswith(': not seen') else ('seen' if ': frames' in resp else 'other:' + resp[:40])
def pairs_of(rows):
    out = {}
    for x in rows:
        if x.get('mode', 'none') != 'none': continue
        o = x.get('output', x)
        for c in o['calls']['records']:
            if c.get('family') == 'ground':
                n = re.search(r'obj="([^"]*)"', c['call'])[1]
                out.setdefault((x['id'].split(':')[-1], n), st(c.get('response') or ''))
    return out
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 20
RULE = sys.argv[3] if len(sys.argv) > 3 else 'null_argmax'
mine = pairs_of(rows)
rep = {}
for l in open(RP + 'replay_out2.jsonl'):
    r = json.loads(l)
    if r.get('geo') == 'tower' and r.get('rule') == RULE and 'ground' in r:
        for n, s in r['ground'].items(): rep[(r['id'], n)] = st(s)
nat = {}
for i, v in json.load(open(RP + 'n2r_calls.json'))['unflagged'].items():
    for c in v['calls']:
        if c['kind'] == 'ground': nat.setdefault((i, c['name']), c['st'])
own = pairs_of(json.loads(l) for l in open(OWN))
b04 = pairs_of(json.loads(l) for l in open('/scratch/jjyeung/orch_n30/reader_r1/work/b1/work/b04full/out/proofs/PARITY_own_depth_p0_51rows.jsonl'))
print('reads', len(rows), 'finish', {f: sum(1 for x in rows if x['output'].get('finish') == f) for f in {x['output'].get('finish') for x in rows}}, 'mean s', round(sum(x['seconds'] for x in rows) / max(1, len(rows)), 1))
def errs_of(x):
    return [c['response'][:80] for c in x['output']['calls']['records'] if 'error' in str(c.get('response', '')).lower()[:80]]
mal = [x['id'] for x in rows if any('malformed' in e for e in errs_of(x))]
other = [(x['id'], [e for e in errs_of(x) if 'malformed' not in e]) for x in rows if any('malformed' not in e for e in errs_of(x))]
print('reads with model-side malformed calls', len(mal), '| reads with OTHER error responses (tower path; stop if any)', len(other), other[:5])
for name, ref in (('replay_tower_kept', rep), ('job170056_native', nat), ('h1_0_own', own), ('b04_parity_owndepth_scale', b04)):
    shared = [k for k in mine if k in ref][:N]
    dis = [(k, mine[k], ref[k]) for k in shared if mine[k] != ref[k]]
    print(name, 'shared', len(shared), 'disagree', len(dis), dis[:6])
print('not seen share (mine)', sum(v == 'not seen' for v in mine.values()), '/', len(mine))
