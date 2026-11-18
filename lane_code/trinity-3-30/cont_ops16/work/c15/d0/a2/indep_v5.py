"""Independent read of rows v5 (cont_ops4): (a) the sealed layout_inputs as run.prepare calls it (carrier_c1_run.py:525-532)
over every v5 row, (b) exact diff: v4 minus the 81 rows of cont_ops3's list (NULL_TOTAL_NUM_FRAMES_v4.json) equals v5 in
(row, target) text, in order. Read-only."""
import json, sqlite3, sys, hashlib
sys.path.insert(0, '/scratch/jjyeung/orch_n30/cont_ops/work/d0/src')
from student_pilot import carrier_c1_data as data
V4 = '/scratch/jjyeung/orch_n30/rows_rebuild/out/rows/d0_v4/vqa/rows.sqlite'
V5 = '/scratch/jjyeung/orch_n30/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite'
cfg = json.load(open('/scratch/jjyeung/orch_n30/cont_ops/work/d0/orch_r8/k/6224c536.json'))
ro = lambda p: sqlite3.connect('file:' + p + '?mode=ro', uri=True)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
out = dict(v4_sha256=sha(V4), v5_sha256=sha(V5), frame_layout=cfg.get('frame_layout'), layout_settings=list(data.layout_settings(cfg)))
lay = dict(checked=0, single_image=0, failed=[])
for (i, s) in ro(V5).execute('SELECT i, row FROM rows ORDER BY i'):
    row = json.loads(s)
    if data.single_image_row(row, 'vqa', training_mode=cfg.get('training_mode', 'mixed'), geometry_online=cfg.get('geometry_online')):
        lay['single_image'] += 1; continue
    try:
        data.layout_inputs(row, *data.layout_settings(cfg), verify_partners=True); lay['checked'] += 1
    except Exception as e:
        lay['failed'].append(dict(i=i, qid=row.get('qid'), error=type(e).__name__ + ': ' + str(e)[:120]))
out['layout'] = dict(lay, failed_count=len(lay['failed']), failed=lay['failed'][:20])
drop = json.load(open('/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/NULL_TOTAL_NUM_FRAMES_v4.json'))['rows']
di = {r['i'] for r in drop}; dq = {r['qid'] for r in drop}; assert len(di) == len(dq) == 81
a = ro(V4).execute('SELECT i, row, target FROM rows ORDER BY i'); b = ro(V5).execute('SELECT i, row, target FROM rows ORDER BY i')
n4 = dropped = equal = 0; mism = []; b_i = []
for (i, r, t) in a:
    n4 += 1
    if i in di:
        dropped += 1; assert json.loads(r)['qid'] in dq; continue
    nb = b.fetchone()
    if nb is None: mism.append(dict(v4_i=i, issue='v5 ended')); break
    b_i.append(nb[0])
    if nb[1] == r and nb[2] == t: equal += 1
    else: mism.append(dict(v4_i=i, v5_i=nb[0])) if len(mism) < 20 else None
extra = b.fetchall()
out['diff'] = dict(v4_rows=n4, dropped=dropped, v5_rows_compared=len(b_i), equal=equal, mismatches=len(mism), first_mismatches=mism[:20],
                   v5_extra_rows=len(extra), v5_indices_contiguous=b_i == list(range(len(b_i))))
out['verdict'] = 'AGREE' if (not lay['failed'] and not mism and not extra and dropped == 81 and equal == n4 - 81) else 'DISAGREE'
print(json.dumps(out, indent=1))
