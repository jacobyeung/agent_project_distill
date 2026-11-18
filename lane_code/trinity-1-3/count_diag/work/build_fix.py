"""Build the proposed counting fix: REMOVE lists (sealed Removals format, match key row_key = qid) and the v5-target restore table.
Inputs (read-only): store v7 210b2534 (extract v7_count_fs_rows.jsonl), REMOVE n.json 02315a74, A2 v3 CHANGES.jsonl 56100b66, D0 v5 store 4af43b40."""
import json, re, hashlib, sqlite3
from collections import Counter
H = lambda s: hashlib.sha256(s.encode()).hexdigest()
N_JSON = '/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/records/n.json'
REM = {json.loads(l)['row_key'] for l in open(N_JSON) if l.strip()}
CH = {}
for l in open('/scratch/jjyeung/orch_n30/rows_a2/out/a2_vqa_v3/CHANGES.jsonl'):
    c = json.loads(l)
    if c['question_type'] == 'object_counting': CH[c['qid']] = c
assert len(CH) == 6552, len(CH)
LIST_RE = re.compile(r'(?:at its first appearance|by the frame where it first appears|by first appearance|using its first-seen frame|first seen in)\s*:')
rows = []
for l in open('v7_count_fs_rows.jsonl'):
    x = json.loads(l)
    if x['fam'] != 'object_counting': continue
    r = x['row']; t = r['target']
    pool = r['pool']; totals = 'count_kind' in r
    form = ('TOTALS' if totals else ('FS_LIST' if LIST_RE.search(t) else ('PROC' if re.search(r'count (it|each) once', t) else 'OTHER')))
    rows.append(dict(i=x['i'], qid=r['qid'], pool=pool, qt=r['question_type'], scene=f"{r['dataset']}/{r['scene']}", target=t, form=form,
                     retrace_a2=r.get('retrace_a2'), totals=totals))
print('forms', Counter((x['pool'] if not x['pool'].startswith('rows_rebuild_d0_') else 'd0_gaps', x['form']) for x in rows))
assert not any(x['form'] == 'OTHER' for x in rows)
# verify the restore table against A2 v3 CHANGES and the D0 v5 store
con = sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite?immutable=1', uri=True)
restore, bad = [], Counter()
for x in rows:
    if x['qid'] not in CH: continue
    c = CH[x['qid']]
    if x['target'] != c['new_target']: bad['v7 target != v3 new_target'] += 1
    if H(c['old_target']) != x['retrace_a2']['d0_v5_target_sha256']: bad['old_target sha != retrace_a2.d0_v5_target_sha256'] += 1
    i5, row5 = con.execute('select i,row from rows where i=?', (c['i'],)).fetchone()
    r5 = json.loads(row5)
    if r5['qid'] != x['qid'] or r5['target'] != c['old_target']: bad['D0 v5 store row differs'] += 1
    if not re.search(r'count (it|each) once', c['old_target']): bad['v5 target not procedure-only'] += 1
    restore.append(dict(i_v7=x['i'], i_d0v5=i5, qid=x['qid'], v7_target_sha256=H(x['target']), restore_target=c['old_target'], restore_target_sha256=H(c['old_target'])))
print('restore rows', len(restore), 'verification failures', dict(bad))
assert not bad and len(restore) == 6552
def rec(x, reason):
    return json.dumps({'pool': x['pool'], 'question_type': x['qt'], 'reason': reason, 'row_key': x['qid'], 'scene': x['scene']}, sort_keys=True, separators=(',', ':'))
def write(name, sel, reason):
    out = [x for x in rows if sel(x) and x['qid'] not in REM]
    out.sort(key=lambda x: x['i'])
    with open(name, 'w') as f:
        for x in out: f.write(rec(x, reason) + '\n')
    print(name, len(out), dict(Counter((x['pool'] if not x['pool'].startswith('rows_rebuild_d0_') else 'd0_gaps', x['form']) for x in out)))
    return out
REASON = 'count_diag_first_seen_list_form'
# B1: continuation from R1 step 200 (or relaunch without a store change): every first-seen list row (single and totals) out; procedure-only rows stay
write('COUNT_FIX_REMOVE_B1.jsonl', lambda x: x['form'] in ('FS_LIST', 'TOTALS'), REASON)
# B1 variant keeping D0's 1,239 totals rows (D0 parity on totals; totals cell 1.00)
write('COUNT_FIX_REMOVE_B1_keepD0totals.jsonl', lambda x: x['form'] == 'FS_LIST' or (x['form'] == 'TOTALS' and not x['pool'].startswith('rows_rebuild_d0_')), REASON)
# A: relaunch from step 544 with store v7 + restored v5 targets for the 6,552 retraced rows: remove the rest of the list form
write('COUNT_FIX_REMOVE_A.jsonl', lambda x: (x['form'] == 'FS_LIST' and x['qid'] not in CH) or x['form'] == 'TOTALS', REASON)
with open('COUNT_FIX_RESTORE_V5_TARGETS.jsonl', 'w') as f:
    for r in sorted(restore, key=lambda r: r['i_v7']): f.write(json.dumps(r, sort_keys=True, separators=(',', ':')) + '\n')
# eligible counts after each plan
kept = lambda sel: sum(1 for x in rows if x['qid'] not in REM and not sel(x))
pc = sum(1 for x in rows if x['qid'] not in REM and x['form'] == 'PROC')
print('procedure-only single rows kept (B1):', pc, '-> counting ceiling 4*n/1000 =', 4 * pc / 1000)
print('plan A procedure-only single rows:', pc + 6552, '-> ceiling', 4 * (pc + 6552) / 1000)
