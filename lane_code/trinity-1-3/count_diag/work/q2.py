import json, re, numpy as np
from collections import Counter, defaultdict
from cd_load import load, load_on16k, as_num

D, _ = load(); O, SH = load_on16k()
EXPORTS = ['S544', 'D0m100', 'H1m100', 'R1m100', 'D0m200']
SETS = ['dev-S1', 'R0-dev']

def form(g):
    h = g[:600]
    tags = []
    if re.search(r'at its first appearance|by the frame where it first appears|first appears?:|first seen:', h): tags.append('FS_LIST')
    if re.search(r'across the frames, and count it once|count each once across the frames', h): tags.append('V5_PROC')
    if re.search(r'find the frames that show|detections across those frames', h): tags.append('S544_DETECT_MATCH')
    if re.search(r'add them|in total|\d+ \+ \d+ =', g): tags.append('TOTALS')
    if re.search(r'frame \d+ \((left|middle|right)\)', h): tags.append('REGION')
    if re.search(r'\d+(\.\d+)? s[;.,]', h): tags.append('SECONDS')
    if not tags: tags.append('OTHER')
    return tags

def primary(tags):
    for t in ['TOTALS', 'FS_LIST', 'V5_PROC', 'S544_DETECT_MATCH', 'OTHER']:
        if t in tags: return t
    return tags[0]

def list_stats(g):
    # entries of the first list after a colon in step 1
    m = re.search(r'(?:first appearance|first appears|frame where it first appears|first seen in)\s*:?\s*(.*?)(?:\n|$)', g)
    if not m: return None
    ents = [e.strip(' .') for e in re.split(r';|,', m.group(1)) if e.strip(' .')]
    if not ents: return None
    run = best = 1
    for a, b in zip(ents, ents[1:]):
        run = run + 1 if a == b else 1; best = max(best, run)
    return dict(n=len(ents), distinct=len(set(ents)), maxrun=best, dup=len(ents) - len(set(ents)))

out = {}
L = ['Trace forms at ON16k (full generation) for counting items; outcome columns use the scored B2048 read.']
for s in SETS:
    for ex in EXPORTS:
        if s not in O[ex]: continue
        rows = []
        for i, r in O[ex][s].items():
            b = D[ex][s][i]
            g = r['raw_generation'] or ''
            tags = form(g); pf = primary(tags); ls = list_stats(g)
            gt = as_num(b['ground_truth']); p = as_num(b['extracted_answer'])
            rows.append(dict(id=i, room=b['room'], gt=gt, p=p, score=float(b['score']), forced=bool(b['forced_close']), cap16=bool(r['hit_token_cap']),
                             pf=pf, tags=tags, ls=ls, multi=bool(re.search(r'\(s\)\s+and\s+', b['question']))))
        out[f'{ex}|{s}'] = rows
        L.append(f'\n== {ex} {s}: n={len(rows)}')
        c = Counter(x['pf'] for x in rows)
        for f_, n in c.most_common():
            it = [x for x in rows if x['pf'] == f_]
            err = [x['p'] - x['gt'] for x in it if x['p'] is not None]
            L.append(f"  {f_:18} n={n:>3}  MRA {100*np.mean([x['score'] for x in it]):5.1f}  exact {sum(1 for x in it if x['p']==x['gt']):>3}  meanErr {np.mean(err) if err else float('nan'):+7.2f}  over {sum(1 for e in err if e>0):>3} under {sum(1 for e in err if e<0):>3}  B2048forced {sum(x['forced'] for x in it):>3}  cap16k {sum(x['cap16'] for x in it):>3}  multi {sum(x['multi'] for x in it)}")
        tc = Counter(t for x in rows for t in x['tags'])
        L.append('  tags: ' + ', '.join(f'{k} {v}' for k, v in tc.most_common()))
        lsr = [x for x in rows if x['ls']]
        if lsr:
            dup = [x for x in lsr if x['ls']['dup'] > 0]
            run = [x for x in lsr if x['ls']['maxrun'] >= 10]
            L.append(f"  lists parsed {len(lsr)}: with a repeated entry {len(dup)}; runaway (same entry >=10 in a row) {len(run)}; list length == answer {sum(1 for x in lsr if x['p'] is not None and x['ls']['n']==x['p'])}")
            # MRA by duplicate presence
            for nm, grp in [('no dup', [x for x in lsr if x['ls']['dup']==0]), ('dup', dup)]:
                if grp:
                    err = [x['p'] - x['gt'] for x in grp if x['p'] is not None]
                    L.append(f"    {nm:7} n={len(grp):>3} MRA {100*np.mean([x['score'] for x in grp]):5.1f} meanErr {np.mean(err) if err else float('nan'):+7.2f} over {sum(1 for e in err if e>0)} under {sum(1 for e in err if e<0)}")
json.dump({k: [{kk: vv for kk, vv in x.items()} for x in v] for k, v in out.items()}, open('Q2_FORMS.json', 'w'))
open('Q2_REPORT.txt', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
