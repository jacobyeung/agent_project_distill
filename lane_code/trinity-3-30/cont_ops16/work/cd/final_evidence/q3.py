import json, re, numpy as np
from collections import Counter, defaultdict
rows = [json.loads(l) for l in open('v7_cf_compact.jsonl')]
REM = set()
for l in open('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/records/n.json'):
    l = l.strip()
    if l: REM.add(json.loads(l)['row_key'])
def think(t):
    m = re.search(r'<think>(.*?)</think>', t, re.S); return m.group(1).strip() if m else t
LIST_RE = re.compile(r'(?:at its first appearance|by the frame where it first appears|by first appearance|using its first-seen frame|first seen in)\s*:\s*([^\n]*)')
def form(r):
    t = think(r['target'])
    if r['fam'] == 'first_seen_frame': return 'FIRST_SEEN_TYPE'
    region = bool(re.search(r'frame \d+ \((left|middle|right)\)', t))
    if 'add them' in t: return 'TOTALS_LIST' + ('_REGION' if region else '')
    if LIST_RE.search(t): return 'FS_LIST' + ('_REGION' if region else '')
    if re.search(r'count (it|each) once|count each once', t): return 'PROC_ONLY'
    return 'OTHER'
def entries(t):
    out = []
    for m in LIST_RE.finditer(think(t)):
        ents = [e.strip(' .') for e in m.group(1).split(';') if e.strip(' .')]
        out.append(ents)
    return out
stats = defaultdict(lambda: dict(n=0, kept=0, ans=Counter(), lens=[], dup_rows=0, dup_entries=0, entries=0, maxrun=[], n15=0, sec=0, lists=0))
for r in rows:
    f = form(r); s = stats[(r['fam'], r['pool'] if not r['pool'].startswith('rows_rebuild_d0_') else 'd0_gaps', f)]
    s['n'] += 1; kept = r['qid'] not in REM; s['kept'] += kept
    s['ans'][r['a']] += 1
    if re.search(r'\d+(\.\d+)? s[;.]', think(r['target'])): s['sec'] += 1
    L = entries(r['target'])
    if L:
        dup_any = False
        for ents in L:
            s['lists'] += 1; s['entries'] += len(ents); d = len(ents) - len(set(ents)); s['dup_entries'] += d
            dup_any |= d > 0
            run = best = 1
            for a, b in zip(ents, ents[1:]):
                run = run + 1 if a == b else 1; best = max(best, run)
            s['maxrun'].append(best); s['lens'].append(len(ents))
            if len(ents) >= 15: s['n15'] += 1
        s['dup_rows'] += dup_any
CELL = {'object_counting': 10.87, 'totals': 3.39, 'first_seen_frame': 2.00}
elig = {'counting': 11295, 'totals': 9201, 'first_seen_frame': 6985}
L = ['Store v7 counting-family rows by target form (n = store rows; kept = after the 601-row REMOVE list).',
     'cell rows/step: counting 10.87 over 11,295 eligible; totals 3.39 over 9,201; first-seen 2.00 over 6,985 (type_mix.json of 171377).',
     f"{'family':16} {'pool':18} {'form':18} {'n':>6} {'kept':>6} {'perStep':>7} {'lists':>6} {'meanLen':>7} {'p95Len':>6} {'maxLen':>6} {'rowsWithDup':>11} {'dupEntryShare':>13} {'maxRun>=3':>9} {'len>=15':>7} {'ans=2':>6}"]
tot_step = Counter()
for (fam, pool, f), s in sorted(stats.items(), key=lambda t: (t[0][0], -t[1]['n'])):
    is_tot = f.startswith('TOTALS')
    cell = 'totals' if is_tot else ('first_seen_frame' if fam == 'first_seen_frame' else 'counting')
    per_step = s['kept'] * (CELL['totals'] if is_tot else CELL[fam]) / elig[cell]
    tot_step[f] += per_step
    lens = s['lens']
    L.append(f"{fam:16} {pool:18} {f:18} {s['n']:>6} {s['kept']:>6} {per_step:7.2f} {s['lists']:>6} {np.mean(lens) if lens else 0:7.2f} {np.quantile(lens,0.95) if lens else 0:6.0f} {max(lens) if lens else 0:>6} {s['dup_rows']:>11} {s['dup_entries']/max(1,s['entries']):13.3f} {sum(1 for m in s['maxrun'] if m>=3):>9} {s['n15']:>7} {s['ans'].get('2',0)/s['n']:6.2f}")
L.append('Rows per step by form: ' + ', '.join(f'{k} {v:.2f}' for k, v in tot_step.most_common()))
open('Q3_REPORT.txt', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
