#!/bin/bash
# dist_diag Q4/Q5 (read-only, trinity-1-18): question wording of the A0 pool distance programs and A0 unit slice; N card cells.
set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
echo "== host $(hostname -s) $(date -u +%FT%TZ)"
timeout 30 find $W/w16b -maxdepth 4 -name 'CARD.md' -printf '%s %p\n' 2>/dev/null | head -5
C=$(timeout 30 find $W/w16b -maxdepth 4 -name 'CARD.md' 2>/dev/null | head -1)
[ -n "$C" ] && grep -n -i "units\|distance\|recovery\|routing\|relative" "$C" | cut -c1-400 | head -40
nice -n 10 /usr/bin/python3 - <<'PY'
import json, re, hashlib
from collections import Counter
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16b/work/rows_slices/slices_final/'
def unit(q):
    q=q.lower()
    for u,pat in (('cm',r'\b(?:centimeters?|centimetres?|cm)\b'),('ft',r'\b(?:feet|foot|ft)\b'),('in',r'\b(?:inches|inch)\b'),('m',r'\b(?:meters?|metres?|m)\b')):
        if re.search(pat,q): return u
    return '?'
def tmpl(q):
    s=re.sub(r'\b(meters?|centimeters?|feet|inches)\b','U',q)
    s=re.sub(r'the [a-z][a-z ]*?(?= and | to | from |,| using| in U| measured| expressed| U\b|\?|\))', 'the X', s)
    return s[:100]
for name in ('a0_pool_abs_distance_reworded.jsonl','a0_units.jsonl','a0_recovery.jsonl'):
    p=W+name; n=0; uc=Counter(); tc=Counter(); keys=Counter()
    try:
        for l in open(p):
            if not l.strip(): continue
            r=json.loads(l); n+=1
            q=r.get('question') or (r.get('student_input') or {}).get('question','') or ''
            if n==1: keys.update(r.keys())
            uc[unit(q)]+=1; tc[tmpl(q)]+=1
        print('== WORDING', name, 'rows', n, 'keys', sorted(keys)[:25])
        print('  units', dict(uc)); print('  templates', len(tc), tc.most_common(6))
    except Exception as e: print('== ERR', name, e)
PY
echo "== done $(date -u +%FT%TZ)"
