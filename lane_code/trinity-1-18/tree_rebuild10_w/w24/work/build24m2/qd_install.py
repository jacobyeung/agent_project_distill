import sys;from pathlib import Path;sys.path.insert(0,str(Path(__file__).resolve().parent))
from buildlib import *
import shutil
k=kit('qd');shutil.copytree(kit('q'),k)
c=J.load(k/'k/a.json');c.update(GO=False,discovery=True,claims='nothing');cap(k,'k/a.json',c)
b=J.load(k/'BUILD.json');b.update(GO=False,discovery=True,claims='nothing');cap(k,'BUILD.json',b)
p=k/'b/pl.py';s=p.read_text()
s=s.replace('def selection_pin(kit):', '''def selection_pin(kit, local=None):
    if local is not None:
        source=Path(local)
        if source.is_symlink() or not source.is_file():raise ValueError('R1_ROUTING_SELECTION_PIN_MISSING')
        pin=dict(path='u/'+sha(source),sha256=sha(source))
        value=load(checked(source,pin['sha256']))
        h=value.get('regenerated_sha256')
        if not isinstance(h,str) or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):
            raise ValueError('R1_ROUTING_SELECTION_PIN_INVALID')
        return pin,source''')
s=s.replace('selected = None if regeneration else selection_pin(kit)',"selected = None if regeneration else selection_pin(kit, root.parent/'routing_selection.json')")
replace(p,s)
p=k/'b/rv.py';s=p.read_text();s=s.replace('        while True:\n','        return 0\n        while True:\n',1);replace(p,s)
p=k/'b/o.py';s=p.read_text().replace('GO=False,submitted_by_build=False','GO=False,submitted_by_build=False,discovery=True,claims="nothing"');replace(p,s)
p=k/'b/a.py';s=p.read_text();needle="    r=run(request,root/'q',stage=stage)";s=s.replace(needle,needle+"\n    r.update(discovery=True,claims='nothing')\n    write(root/'q/RESULT.json',r)");replace(p,s)
s=base64.b64decode(json.loads((k/'k/j.json').read_text())['payload']).decode()
a=s.index('if [[ "${Q_MODE:-q}" != r ]]; then\n"${BW[@]}"');b=s.index('"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/d.py"',a)
s=s[:a]+'''# Both invocations use the same logical namespace and separate physical roots.
mkdir -p "$Q_ROOT/dr"
cp "$Q_ROOT/r.json" "$Q_ROOT/dr/r.json"
set +e
"${BW[@]}" --bind "$Q_ROOT/dr" "$Q_NS" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/a.py" r "$Q_NS/p" "$Q_NS/r.json" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/dr/q.log"
rc=${PIPESTATUS[0]}
if [[ "$rc" != 0 ]]; then exit "$rc"; fi
cp "$Q_ROOT/dr/p/routing_selection.json" "$Q_ROOT/routing_selection.json"
/usr/bin/python3 -B -I -s "$Q_KIT/b/ep.py" "$Q_KIT" "$Q_ROOT" "${SLURM_JOB_ID:?}" 0
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/g.py"
rc=$?
if [[ "$rc" != 0 ]]; then exit "$rc"; fi
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/a.py" q "$Q_NS/p" "$Q_NS/r.json" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/q.log"
rc=${PIPESTATUS[0]}
'''+s[b:]
needle='/usr/bin/python3 -B "$Q_KIT/b/o.py" "$Q_ROOT" "$rc" "$rr"'
review='''if [[ "$rc" == 0 && "$rr" == 0 ]]; then
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/h.py" "$Q_NS/p" "$Q_NS/v.json" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/h.log"
rc=${PIPESTATUS[0]}
if [[ "$rc" == 0 ]]; then
"${BW[@]}" nice -n 10 "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/rv.py" "$Q_NS" "$Q_NS/v.json" "${SLURM_JOB_ID:?}" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/rv.log"
rc=${PIPESTATUS[0]}
fi
fi
'''
s=s.replace(needle,review+needle);cap(k,'k/j.json',s.encode())
# The kit entry remains compatible with an already resolved request. jd resolves
# its own request before invoking this verified entry in the same allocation.
p=k/'job.sh';s=p.read_text().replace('--partition=general','--partition=preempt').replace('--cpus-per-task=8','--cpus-per-task=48').replace('--mem=192G','--mem=800G').replace('--time=12:00:00','--time=04:00:00')
replace(p,s,0o755)
pool=J.load(k/'k/p.json')['pool'];nroot=J.load(k/'k/p.json')['n_root']
s='''#!/bin/bash
#SBATCH -p preempt
#SBATCH --job-name=a15_cot_ap24d9b8e2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:TERM@600
#SBATCH --output=ROOT/j/a15_cot_ap24d9b8e2_%j.log
#SBATCH --error=ROOT/j/a15_cot_ap24d9b8e2_%j.err
set -euo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TK_JOB_START="$(date +%s)"
ROOT="ROOT/qd"
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
python3 -B -I -s "$ROOT/b/v.py" "$ROOT"
source "$ROOT/b/ep.sh"
python3 -B -I -s "$ROOT/b/resolve.py" --pool "POOL" --output "$N/r0.json" 2>&1 | python3 -B -I -s "$ROOT/b/l.py" "$ROOT" > "$N/q.log"
setsid bash -c 'set -o pipefail; python3 -B -I -s "$1/b/x.py" "$1" "$2" "$3" 2>&1 | python3 -B -I -s "$1/b/l.py" "$1"' bash "$ROOT" "$N/r0.json" "$N" &
TK_WORK_PID=$!
wait "$TK_WORK_PID"
'''.replace('ROOT/j',nroot+'/j').replace('ROOT/qd',nroot+'/qd').replace('"POOL"','"'+pool+'"')
replace(L/'out/jd.sh',s,0o755)
print('qd',reseal(k))
