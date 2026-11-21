# usage: sed s/JOB/<job>/ fspell.sh | ossh 'bash -s'  — reads frames.json roots on the job's node (ORCH ANSWER 1928Z item 4)
export TZ=UTC; date -u +%TZ
timeout 120 srun --overlap --jobid JOB -N1 -n1 bash -s <<'EOS'
/usr/bin/python3 -B -I - <<'PY'
import json, glob
for p in sorted(glob.glob('/tmp/q_22c714e1_JOB/p/q/p/frames_*/frames.json')) + sorted(glob.glob('/tmp/q_22c714e1_JOB/p/q/p/request.json')):
    d = json.load(open(p)); roots = d.get('roots') or d.get('frame_roots') or []
    print(p, 'second' if roots and all(r.startswith('/tmp/jjyeung/q_22c714e1/') for r in roots) else 'first' if roots and all(r.startswith('/tmp/q_22c714e1/') for r in roots) else 'mixed/other', roots)
PY
EOS
date -u +%TZ
