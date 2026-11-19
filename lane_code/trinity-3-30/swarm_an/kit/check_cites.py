"""Verbatim check of a report's cited items: every quoted fragment (>= 20 chars) on a line that names an item id must occur
in that item's question or generated text at the step. usage: check_cites.py <final_message.md> [step] [max_items]
Run with /scratch/jjyeung/envs/planner_local_v1/bin/python so routed items resolve."""
import sys, re; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
p = sys.argv[1]; step = int(sys.argv[2]) if len(sys.argv) > 2 else 200; mx = int(sys.argv[3]) if len(sys.argv) > 3 else 12
run = 'R1'
rows = {}
def add(rs):
    for r in rs: rows.setdefault(r['id'], []).append(r)
for s in ('dev-S1', 'R0-dev'): add(K.direct(run, step, s))
for tw in ('away', 'forward'):
    try: add(K.facing(run, step, tw))
    except Exception: pass
try: add(K.vsti(run, step))
except Exception: pass
try:
    add(K.routed(step, part='A')); add(K.routed(step, part='B'))
except Exception as e: print('routed unavailable', repr(e)[:80])
old = {}
try:
    for s in ('dev-S1', 'R0-dev'):
        for r in K.direct('S1', 544, s): old.setdefault(r['id'], []).append(r)
    for r in K.vsti('S1', 544): old.setdefault(r['id'], []).append(r)
    for part in ('A', 'B'):
        for r in K.routed(544, part=part): old.setdefault(r['id'], []).append(r)
except Exception: pass
norm = lambda s: re.sub(r'\s+', ' ', s.replace('’', "'").replace('‘', "'")).strip().lower()
ID = re.compile(r'`((?:vsi590k_|q|r0_|devs1cam-|room_|backdir_|fwddir_)?[0-9a-z_]{6,}(?:_[a-z]+)?)`')
seen = 0; ok = 0; bad = []; items = 0; missing = []
for line in open(p):
    ids = [i for i in ID.findall(line)]
    quotes = [q for q in re.findall(r'[“"]([^”"]{20,})[”"]', line)]
    if not ids or not quotes: continue
    cands = [r for i in ids for r in rows.get(i, [])] + [r for i in ids for r in old.get(i, [])]
    if not cands:
        missing.append(ids[0]); continue
    items += 1
    hay = norm(' '.join((r['question'] or '') + ' ' + (r['text'] or '') + ' ' + ' '.join(r.get('options') or []) for r in cands))
    for q in quotes:
        seen += 1
        frag = [norm(x) for x in re.split(r'…|\.\.\.', q) if len(x.strip()) >= 12]
        if all(f.rstrip('.,;:') in hay for f in frag): ok += 1
        else: bad.append((ids[0], q[:110]))
    if items >= mx: break
print('cited lines checked: %d items, %d quoted fragments, %d verbatim, %d not found; ids not in any set: %s' % (items, seen, ok, len(bad), missing[:5]))
for b in bad[:6]: print('  NOT FOUND', b)
