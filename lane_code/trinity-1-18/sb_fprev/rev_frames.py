"""Reviewer's frame-level check: do full camera routing rows carry any frame of a target capture?"""
import gzip, json, collections
from pathlib import Path
ORCH = Path('/scratch/jjyeung/orch_n30')
AWS = ORCH / 'sb_evidence/aws_sources'
P = 'ap__8865619b__runs__469ddece__inputs__prepare_dd26bb95f37a43789206c6e4d4cd94bd__'
targets = {tuple(l.split('\t')[0].split('/')) for l in open(ORCH / 'sb_framepool/out/CAPTURES.tsv').read().splitlines()[1:]}
fr = {}; dup = 0
with gzip.open(ORCH / 'sb_framepool/work/frame_map.jsonl.gz', 'rt') as f:
    for l in f:
        r = json.loads(l); k = (r['d'], r['s'])
        if r['sha256'] in fr and fr[r['sha256']] != k: dup += 1
        fr[r['sha256']] = k
tf = {h for h, k in fr.items() if k in targets}
n = frames = own = other = tgt = unknown = 0
with gzip.open(AWS / (P + 'routing__rows.camera_rows.jsonl.gz'), 'rt') as f:
    for l in f:
        x = json.loads(l); r = json.loads(x['row']); n += 1
        for fm in r['student_input']['frames']:
            frames += 1; h = fm['sha256']; k = fr.get(h)
            if h in tf: tgt += 1
            if k is None: unknown += 1
            elif k == (r['dataset'], r['scene']): own += 1
            else: other += 1
out = dict(frame_map_frames=len(fr), cross_scene_duplicate_hashes=dup, target_frames=len(tf), camera_rows=n,
           frames=frames, own_scene=own, other_scene=other, not_in_frame_map=unknown, target_capture_frames=tgt)
(Path(__file__).resolve().parent / 'rev_frames.json').write_text(json.dumps(out, indent=1) + '\n')
print(out)
