# run on trinity-1-18 via tssh; MODELS set by the header line
set -u
S=/dev/shm/jjyeung/b14; M=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json
W=/scratch/jjyeung/orch_n30/geo_k1/stage; mkdir -p $W; cd /scratch/jjyeung; date -u
/scratch/jjyeung/envs/planner_local_v1/bin/python - <<PY
import json, glob
m = json.load(open('$M'))
fr = sorted({f['path'][len('/scratch/jjyeung/'):] for c in m['captures'] for f in c['dense_frames']})
assert all(p.startswith('k1_frames/') for p in fr)
tw = sorted(q[len('/scratch/jjyeung/'):] for d in glob.glob('/scratch/jjyeung/k1/run_tower_sam_2/*/PHASE_COMPLETE.json') for q in (d, d.replace('PHASE_COMPLETE.json', 'tower.npz')))
kit = ['geo_bakeoff_kit/' + x for x in ['KIT_SEAL.json', 'PAYLOAD.json', 'runtime', 'work', 'assets/downloads.jsonl']] + sorted(x[len('/scratch/jjyeung/'):] for x in glob.glob('/scratch/jjyeung/geo_bakeoff_kit/assets/*-src'))
kit += ['geo_bakeoff_kit/assets/' + m for m in "$MODELS".split()]
open('$W/files_$TAG.txt', 'w').write('\n'.join((kit if '$COMMON' == '1' else ['geo_bakeoff_kit/assets/' + m for m in "$MODELS".split()]) + ((fr + tw) if '$COMMON' == '1' else [])) + '\n')
print('files', sum(1 for _ in open('$W/files_$TAG.txt')))
PY
mkdir -p $W/code && cp -p /scratch/jjyeung/orch_n30/geo_k1/k1towers/*.py $W/code/ && cp -p $M $W/
time (tar cf - -T $W/files_$TAG.txt -C $W code K1_MANIFEST.arkit_timing.json | timeout 900 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-13.ib "mkdir -p $S && tar xf - -C $S && du -sh $S && du -sh /dev/shm/jjyeung") 2>&1 | tail -6
