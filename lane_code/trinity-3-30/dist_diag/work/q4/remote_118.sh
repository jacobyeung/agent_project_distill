#!/bin/bash
# dist_diag Q4 (read-only, trinity-1-18): build16 proof traces for N's distance/units/recovery cells + wording/unit counts of N's slices.
set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
M=/scratch/jjyeung/n30_mirror
echo "== host $(hostname -s) $(date -u +%FT%TZ)"
ls -la $W/w16b/work/build16/proofs 2>&1 | head -30
ls -la $W/w16b/work/build16/proofs/traces 2>&1 | head -40
echo "== jsonl >1MB under w16b (maxdepth 6)"
timeout 60 find $W/w16b -maxdepth 6 -name '*.jsonl' -size +1M -printf '%s %p\n' 2>/dev/null | head -40
echo "== mirror files"
ls -la $M/rows_r1/out/vehN_units/repaired $M/rows_r1/out/recovery_v3 $M/rows_r2/out/vehN_pool_abs_distance_full 2>&1 | head -30
nice -n 10 /usr/bin/python3 - <<'PY'
import json, re, os, glob, hashlib
from collections import Counter
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; M='/scratch/jjyeung/n30_mirror'
T=W+'/w16b/work/build16/proofs/traces'
def strip(t): return re.sub(r'<tool_response>(.*?)</tool_response>', lambda m: '<tool_response>'+m.group(1).strip().split('\n')[0][:60]+' ...</tool_response>', t, flags=re.S)
for cell in ('units','recovery','absolute_distance'):
    p=T+'/'+cell+'.jsonl'
    if not os.path.exists(p): print('== MISSING', p); continue
    R=[json.loads(l) for l in open(p)]
    print('== PROOF', cell, len(R), 'keys', sorted(R[0].keys())[:20])
    for r in R:
        q=r.get('prompt','')[-170:].replace('\n',' ')
        print('Q:', q); print('T:', strip(r.get('target_text','')).replace('\n',' | ')[:900])
def tmpl(q):
    s=re.sub(r'\b(meters?|centimeters?|feet|inches)\b','U',q)
    return re.sub(r'between the .*', 'between ...', s)[:90]
def unit(q):
    q=q.lower()
    for u,pat in (('cm',r'\b(?:centimeters?|centimetres?|cm)\b'),('ft',r'\b(?:feet|foot|ft)\b'),('in',r'\b(?:inches|inch)\b'),('m',r'\b(?:meters?|metres?|m)\b')):
        if re.search(pat,q): return u
    return '?'
cands=[M+'/rows_r1/out/vehN_units/repaired/rows_slice.jsonl', M+'/rows_r1/out/recovery_v3/rows.jsonl']
cands+=sorted(glob.glob(M+'/rows_r2/out/vehN_pool_abs_distance_full/*.jsonl'))+sorted(glob.glob(M+'/rows_r2/out/vehN_pool_abs_distance_full/*/*.jsonl'))
for p in cands:
    if not os.path.exists(p): print('== MISSING', p); continue
    n=0; tc=Counter(); uc=Counter(); calls=Counter(); forms=Counter()
    for l in open(p):
        if not l.strip(): continue
        r=json.loads(l); n+=1
        q=r.get('question') or (r.get('student_input') or {}).get('question','')
        tg=r.get('target') or ''
        if not tg and r.get('events'): tg=''.join(e.get('text','') or e.get('token','') for e in r['events'])
        tc[tmpl(q)]+=1; uc[unit(q)]+=1
        calls['has_ground']+=('<ground' in tg); calls['has_gap']+=('<gap' in tg); calls['not_seen']+=('not seen' in tg); calls['box_unavailable']+=('unavailable' in tg)
        calls['conversion_line']+=bool(re.search(r'\d\s*x\s*(?:3\.28084|39\.3701|100)\s*=', tg)); calls['no_call']+=('<ground' not in tg and '<gap' not in tg)
        calls['answer_from_frames']+=('In the frames themselves' in tg or 'do not call it again' in tg)
    print('== SLICE', p, 'rows', n, 'sha', hashlib.sha256(open(p,'rb').read()).hexdigest()[:8])
    print('  units', dict(uc)); print('  calls', dict(calls)); print('  templates', tc.most_common(8))
PY
echo "== done $(date -u +%FT%TZ)"
