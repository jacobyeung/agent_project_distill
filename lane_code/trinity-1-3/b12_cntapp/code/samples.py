"""SAMPLES_30.md: 30 rows per family for RGB review. Usage: samples.py ROWS_DIR [PREV_SAMPLES_30.md]
Keeps the qids of the previous sample that still exist (so earlier probes stay valid) and fills the rest by qid hash."""
import sys, os, json, re, hashlib
D = sys.argv[1]; prev = set(re.findall(r'^### (\S+)', open(sys.argv[2]).read(), re.M)) if len(sys.argv) > 2 else set()
h = lambda s: hashlib.sha256(s.encode()).hexdigest()
CIT = {'count_single': ('instances',), 'count_total': ('total_categories',), 'appearance': ('first_seen', 'gap_min'), 'first_seen': ('first_seen', 'n_instances')}
out = []; kept = 0
for fam in ('count_single', 'count_total', 'appearance', 'first_seen'):
    rows = [json.loads(l) for l in open(os.path.join(D, fam + '.jsonl'))]
    keep = [r for r in rows if r['qid'] in prev]; kept += len(keep)
    rest = sorted((r for r in rows if r['qid'] not in prev), key=lambda r: h(r['qid'] + 'sample'))
    out.append(f'## {fam}')
    for r in (keep + rest)[:30]:
        si = r['student_input']; pv = r['provenance']
        out.append(f"### {r['qid']} {r['dataset']}/{r['scene']} {pv['canonical']}\nQ: {si['question']}")
        if si['options']: out.append(f"OPTS: {si['options']}")
        out.append('TARGET:\n' + r['target'] + '\nCITED: ' + json.dumps({k: pv[k] for k in CIT[fam] if k in pv}) + '\n')
open(os.path.join(D, 'SAMPLES_30.md'), 'w').write('\n'.join(out) + '\n'); print('kept from previous sample', kept)
