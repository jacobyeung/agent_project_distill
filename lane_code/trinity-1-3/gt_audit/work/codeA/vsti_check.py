"""Independent per-box check of the VSTI relative dev rasters with rows_r1's audit tool (read-only copy)."""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', CUDA_VISIBLE_DEVICES='')
import collections, importlib.util, json, pathlib
import numpy as np
LANE = pathlib.Path('/scratch/jjyeung/orch_n30/gt_audit')
spec = importlib.util.spec_from_file_location('audit_tool', str(LANE / 'work/codeA/audit.py'))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
A.CODE = LANE / 'work/vsti_check'; A.ROOTS = ['/scratch/jjyeung/orch_n30/rows_r1/work/codeB/rasters']
D = pathlib.Path('/scratch/jjyeung/orch_n30/rows_r1/out/vsti_rel_dev_r0')
rooms = [l.strip().split('/')[-1] for l in open(D / 'ROOMS_USED.txt') if l.strip()]
items = [json.loads(l) for l in open(D / 'items.jsonl')]
R = json.load(open(D / 'RASTERS.json'))
boxes = {}
for room in rooms:
    p = R[room]['path']
    with np.load(p, allow_pickle=False) as z:
        for j, iid in enumerate(z['ids']):
            b = dict(name=str(z['labels'][j]), instance_id=int(iid), centroid=[float(x) for x in z['obb_centroid'][j]],
                     axesLengths=[float(x) for x in z['obb_lengths'][j]], normalizedAxes=[float(x) for x in z['obb_axes'][j]])
            boxes[A.boxkey(room, b)] = dict(canonical=room, box=b)
cache, checks = A.measure_rasters(boxes)
c = collections.Counter(cache[k]['status'] for k in boxes)
per_room = collections.defaultdict(collections.Counter)
for k in boxes: per_room[boxes[k]['canonical']][cache[k]['status']] += 1
out = dict(rooms=len(rooms), boxes=len(boxes), status=dict(c), rooms_with_half=sorted(r for r, x in per_room.items() if x['half']),
           rooms_all_decided_full=sum(1 for x in per_room.values() if x['full'] and not x['half']), item_types=dict(collections.Counter(i['question_type'] for i in items)))
json.dump(out, open(LANE / 'work/vsti_check/VSTI_BOX_CHECK.json', 'w'), indent=1); print(json.dumps(out))
