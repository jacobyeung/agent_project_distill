"""Reviewer harness: wrap real rows_rebuild slices in r2-family-manifest-v1 envelopes (metadata only)."""
import base64, hashlib, json, sys, os
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/review_tree/work')
KIT = W/'p/build3/kits/5c2ca33ca02a'
sys.path.insert(0, str(W/'stage3/5c2ca33ca02a_t/o/ee000001'))
from student_pilot.p3_provenance import digest, file_pin
from student_pilot.r2_exclusions import ROLES, SEALED
OUT = W/'h/env'; OUT.mkdir(parents=True, exist_ok=True)
cfg = json.load(open(KIT/'k/879c00848a1267ffdaeb814ae48afb6d7875bb952dccd80a8618ebb51f625098.json'))
recs = cfg['r2_build2']['records']
excl = {}
for role in ROLES:
    cap = json.load(open(KIT/recs[role]['path']))
    raw = base64.b64decode(cap['payload'])
    assert hashlib.sha256(raw).hexdigest() == SEALED[role], role
    p = OUT/('excl_'+role); p.write_bytes(raw); excl[role] = file_pin(p)
wh = file_pin(W/'rows/WITHHELD_ROOMS_80.json')
STREAM = {'a0_units':'routing','a0_recovery':'routing','pool_abs_distance':'routing','pool_room':'routing'}
def key_of(r):
    if r.get('dataset') and r.get('scene'): return r['dataset']+'/'+r['scene']
    pr = r.get('provenance', {})
    return pr.get('alias')
def frames_for(r):
    si = r.get('student_input') or {}
    idx = si.get('frame_indices') or r.get('frame_indices') or (r.get('provenance') or {}).get('frame_indices')
    return idx, si.get('fps', 30.0)
def build(name, rows_path, stream, out):
    rows = [json.loads(l) for l in open(rows_path)]
    rp = out/(name+'.rows.jsonl')
    with open(rp, 'w') as f:
        for r in rows: f.write(json.dumps(r)+'\n')
    cov_rows, fmap, bind = {}, {}, {}
    for r in rows:
        k = key_of(r)
        cn = [x for x in ((r.get('provenance') or {}).get('canonical'), r.get('canonical')) if x]
        cov_rows[r['qid']] = dict(names=([k] if k else [])+cn, status='known')
        idx, fps = frames_for(r)
        if idx:
            fmap[r['qid']] = dict(fps=fps, total_num_frames=(r.get('student_input') or {}).get('total_num_frames', idx[-1]+1),
                frames=[dict(path='/fh/%s/%d.jpg' % (str(k).replace('/','_'), i), sha256=hashlib.sha256(('%s/%d' % (k, i)).encode()).hexdigest(), source_index=i) for i in idx])
        bind[r['qid']] = digest(r)
    rows_pin = file_pin(rp)
    cp = out/(name+'.coverage.json'); cp.write_text(json.dumps(dict(exclusions=excl, rows_sha256=rows_pin['sha256'], rows=cov_rows)))
    fp = out/(name+'.framemap.json'); fp.write_text(json.dumps(fmap))
    man = dict(schema='r2-family-manifest-v1', family=name, stream=stream, count=len(rows), rows=rows_pin,
               row_bindings=bind, scene_coverage=file_pin(cp), exclusions=excl, upstream_receipts=[],
               withheld_rooms=wh, frame_map=file_pin(fp))
    mp = out/(name+'.manifest.json'); mp.write_text(json.dumps(man))
    return mp
if __name__ == '__main__':
    src = Path(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.glob('*.jsonl')):
        n = f.stem
        print(build(n, f, STREAM.get(n, 'vqa'), out))
