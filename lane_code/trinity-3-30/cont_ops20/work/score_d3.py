"""cont_ops20: merge three disjoint D@544 segments (parent partial, remainder-1 partial, remainder-2) with dresume's authenticators.
Spec JSON (absolute paths): {"current": {"items","p0","a0","e0","r0","items1","p1","a1","e1","r1","items2","p2","a2","e2","r2"},
 optional "compare": {"items","package","archive","exit","receipt"} (a single complete return of the same 580 items, e.g. D@200)}.
Usage: python3 score_d3.py --spec S.json --work FRESH --out OUT.json"""
import argparse, hashlib, json, sys, tarfile
from pathlib import Path
sys.path[:0] = ['/scratch/jjyeung/orch_n30/cont_ops18/dresume']
import score_base as base
from score_d import records
from return_tools import read, unpack, load, validate_manifest
from fetch_validation import digest
from dbuild.make_items_d import subset

KEYS = {'items', 'p0', 'a0', 'e0', 'r0', 'items1', 'p1', 'a1', 'e1', 'r1', 'items2', 'p2', 'a2', 'e2', 'r2'}


def need(ok, msg):
    if not ok:
        raise ValueError(msg)


def code_py(package):
    # Every .py of the package code tree except the subset validator; the artifact manifest hashes these code roots.
    with tarfile.open(str(Path(package) / '0.tgz')) as t:
        return {m.name: hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t
                if m.isfile() and m.name.endswith('.py') and m.name != 'h1eval/dist580.py' and '__pycache__' not in m.name}


def staged_inputs(root, token):
    # INPUTS.json binds every staged archive part, file and root (sha256 + bytes); only the segment's own package path may differ.
    raw = (Path(root) / 'metadata/INPUTS.json').read_text().replace('/a15_cot_ap%s/' % token, '/PKG/')
    need('/a15_cot_ap' not in raw, 'INPUTS name a foreign package')
    return {k: v for k, v in json.loads(raw).items() if k != 'resume'}


def merge3(s, work):
    need(set(s) == KEYS, 'spec keys differ: %r' % sorted(KEYS))
    ex = [unpack(s['a%d' % i], s['e%d' % i], s['r%d' % i], s['p%d' % i], work / ('s%d' % i)) for i in range(3)]
    man, par = validate_manifest(s['items'], s['p0'])
    rem1, c1 = validate_manifest(s['items1'], s['p1'])
    rem2, c2 = validate_manifest(s['items2'], s['p2'])
    a, am = load(work / 's0', s['items'], s['p0'])
    b, bm = load(work / 's1', s['items1'], s['p1'])
    c, cm = load(work / 's2', s['items2'], s['p2'])
    p1 = rem1['remainder']
    need(p1['partial_archive_sha256'] == digest(s['a0']) and p1['partial_return_token'] == ex[0]['token'], 'remainder 1 selected from another partial')
    need(rem1 == subset(man, sorted(a), p1), 'remainder 1 does not complement the parent partial')
    need(sorted(p1['completed_ids']) == sorted(a), 'remainder 1 completed_ids differ from parent partial rows')
    p2 = rem2['remainder']
    need(rem2 == subset(man, sorted(set(a) | set(b)), p2), 'remainder 2 does not complement parent + remainder-1 partials')
    sp = p2['second_partial']
    need(sp == dict(plan=c1['plan'], token=c1['token'], items_sha256=digest(s['items1']), partial_archive_sha256=digest(s['a1']),
                    partial_return_token=ex[1]['token'], completed=len(b)), 'remainder 2 second_partial provenance differs')
    for k in ('parent_plan', 'parent_token', 'parent_items_sha256', 'export_binding', 'partial_archive_sha256', 'partial_return_token'):
        need(p2.get(k) == p1.get(k), 'remainder 2 provenance field differs: ' + k)
    need(p1['parent_plan'] == par['plan'] and p1['parent_token'] == par['token'] and p1['parent_items_sha256'] == digest(s['items'])
         and p1['export_binding'] == par['export_binding'], 'parent provenance differs')
    need(c1['export_binding'] == par['export_binding'] == c2['export_binding'], 'export binding differs')
    need(len({par['token'], c1['token'], c2['token']}) == 3 and len({par['plan'], c1['plan'], c2['plan']}) == 3, 'segments are not fresh identities')
    ev = [{k: v for k, v in x['evaluator_files'].items() if k != 'dist580.py'} for x in (par, c1, c2)]
    need(ev[0] == ev[1] == ev[2], 'evaluator changed beyond the subset validator')
    cp = [code_py(s['p%d' % i]) for i in range(3)]
    need(cp[0] == cp[1] == cp[2], 'package code differs beyond the subset validator')
    si = [staged_inputs(work / ('s%d' % i), x['token']) for i, x in enumerate((par, c1, c2))]
    need(si[0] == si[1] == si[2], 'staged inputs (weights, export parts, preparation, frames, SAM source) differ between segments')
    # artifact_manifest_sha256 hashes the staged components and every code-root .py, so it follows the dist580.py change; staged inputs and the other code are checked equal above.
    bd = [{k: v for k, v in m['binding'].items() if k not in ('evaluator_code_sha256', 'artifact_manifest_sha256')} for m in (am, bm, cm)]
    need(bd[0] == bd[1] == bd[2], 'serving, export or settings differ between segments')
    need(not (set(a) & set(b) or set(a) & set(c) or set(b) & set(c)), 'overlapping completed IDs')
    merged = dict(a); merged.update(b); merged.update(c)
    res = dict(groups={n: base.metrics(merged, ks, records) for n, ks in base.groups(man).items()},
               reworded_minus_twin=base.paired(merged, man), sources=[am, bm, cm],
               segment_counts=[len(a), len(b), len(c)], completed=len(merged), complete=len(merged) == man['count'])
    return merged, res, man


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec', required=True); p.add_argument('--work', required=True); p.add_argument('--out', required=True)
    a = p.parse_args()
    spec = read(a.spec); need(set(spec) in ({'current'}, {'current', 'compare'}), 'expected current and optional compare')
    work = Path(a.work); work.mkdir(parents=True, exist_ok=False)
    rows, cur, man = merge3(spec['current'], work / 'current')
    out = dict(current=cur, bootstrap=dict(draws=10000, seed=17, unit='room_key'),
               call_rate_denominator='all 580 planned items', difference_units='MRA fraction')
    if 'compare' in spec:
        k = spec['compare']; need(digest(k['items']) == digest(spec['current']['items']), 'comparison manifests differ')
        unpack(k['archive'], k['exit'], k['receipt'], k['package'], work / 'compare')
        other, om = load(work / 'compare', k['items'], k['package'])
        out.update(baseline=dict(groups={n: base.metrics(other, ks, records) for n, ks in base.groups(man).items()},
                                 reworded_minus_twin=base.paired(other, man), source=om, completed=len(other)),
                   step_difference=base.comparison(rows, other, man))
    with Path(a.out).open('x') as f:
        json.dump(out, f, indent=2, sort_keys=True, allow_nan=False); f.write('\n')
    print(json.dumps(dict(out=a.out, complete=cur['complete'], completed=cur['completed'], segments=cur['segment_counts'])))


if __name__ == '__main__':
    main()
