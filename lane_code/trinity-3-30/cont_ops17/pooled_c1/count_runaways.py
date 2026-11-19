"""Single-count runaway counter for the amendment's repair test (ORCH AMENDMENT 1108Z, sha256 3be4aa05...; ORCH ANSWER 0059Z item 3).
runaway = the B2048 arm force-closed its think at the 2,048-token budget (row field forced_close) on an object_counting item,
lane count_diag's definition as used by cfix/derived_v3.py runaways() (byte-equal logic); single = question without '(s) and '
(one category). Population: dev-S1 (family main) 150 single items, R0-dev (family a7, ids decoded through ID_MAP.json) 287.
Repair bounds: single runaways <= 2 of 150 on dev-S1 and <= 8 of 287 on R0-dev (the step-544 counts).
usage: count_runaways.py --x <fetched/x of the direct read> [--output OUT.json]"""
import argparse, json, re
FAM = dict(main='dev-S1', a7='R0-dev')
IDMAP = '/scratch/jjyeung/orch_n30/cont_ops/work/h1read/evidence/ID_MAP.json'
BOUND = {'dev-S1': (2, 150), 'R0-dev': (8, 287)}


def runaways(x):
    idm = json.load(open(IDMAP)); out = {}
    for fam in FAM:
        rows = [json.loads(l) for l in open('%s/%s/a0/results/budget_2048/0/items_a0.jsonl' % (x, fam)) if l.strip()]
        c = [r for r in rows if r.get('question_type') == 'object_counting']
        dec = lambda i: idm[i]['id'] if fam == 'a7' and i in idm else i
        run = {dec(r['id']): int(bool(re.search(r'\(s\)\s+and\s+', r['question']))) for r in c if r.get('forced_close')}
        out[fam] = dict(ids=run, items=len(c), single_items=sum(1 for r in c if not re.search(r'\(s\)\s+and\s+', r['question'])))
    return out


def main():
    a = argparse.ArgumentParser(); a.add_argument('--x', required=True); a.add_argument('--output'); a = a.parse_args()
    rw = runaways(a.x); res = {}
    for fam, v in rw.items():
        s = FAM[fam]; single = sum(1 for m in v['ids'].values() if m == 0); lim, n = BOUND[s]
        if v['single_items'] != n: raise SystemExit('REFUSED: %s has %d single counting items, expected %d' % (s, v['single_items'], n))
        res[s] = dict(single=single, single_items=v['single_items'], multi=sum(1 for m in v['ids'].values() if m == 1),
                      multi_items=v['items'] - v['single_items'], bound=lim, within_bound=single <= lim,
                      single_ids=sorted(i for i, m in v['ids'].items() if m == 0))
    out = dict(rule='single-count runaway repair test (amendment 3be4aa05 item 3)', x=a.x, sets=res,
               repair_runaway_test_passes=all(r['within_bound'] for r in res.values()))
    if a.output: json.dump(out, open(a.output, 'w'), indent=1, sort_keys=True)
    for s, r in res.items():
        print('%-7s single runaways %3d/%d (bound %d) %s | multi %d/%d' % (s, r['single'], r['single_items'], r['bound'],
              'within' if r['within_bound'] else 'ABOVE', r['multi'], r['multi_items']))
    print('runaway part of the repair test:', 'PASSES' if out['repair_runaway_test_passes'] else 'FAILS',
          '(the pooled counting interval at the later-look level is the counting row of pooled_harm_rule_v3_c1.py)')


if __name__ == '__main__':
    main()
