#!/bin/bash
#SBATCH -p preempt
#SBATCH --job-name=a15_cot_apf07280187950
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:TERM@600
#SBATCH --output=/tmp/q_22c714e1_%j.log
#SBATCH --error=/tmp/q_22c714e1_%j.err
set -euo pipefail
if [[ "${J7_NICE:-0}" != 1 ]]; then export J7_NICE=1; exec nice -n 10 /bin/bash "$0" "$@"; fi
umask 077
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TK_JOB_START="$(date +%s)"
X="/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z15/work/build24m4z15/shell/normal/x"
ROOT="$X/qp_11386117"
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
O="$X/o/${SLURM_JOB_ID}"
if [[ "${J7_INNER:-0}" == 1 ]]; then O="$N/ev"; fi
# The batch shell owns this mirror, outside the work namespace.
j8_snapshot() {
    timeout -k 1 30 python3 -B -I -s - "$N" "$X/o/${SLURM_JOB_ID}_live" "$SLURM_JOB_ID" "${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID}.err" "$1" <<'PYJ8' || true
import fcntl,json,os,stat,subprocess,sys,time
from pathlib import Path
node,target,job,err,phase=sys.argv[1:]
node,target=Path(node),Path(target)
lock=None
try:
    lock=os.open(node/"j8.lock",os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
    fcntl.flock(lock,fcntl.LOCK_EX)
    if any(p.is_symlink() for p in (target,*target.parents)):raise ValueError("E01")
    target.mkdir(parents=True,exist_ok=True,mode=0o700);target.chmod(0o700)
    status=target/"live.json"
    state=json.loads(status.read_bytes()) if status.is_file() else {"once":{}}
    state.update(phase=phase,time_ns=time.time_ns(),notes=[])
    def size():
        return sum(p.stat().st_size for p in target.rglob("*") if p.is_file())
    def put(name,raw,limit=3_980_000):
        dest=target/name;temp=target/(name+".part")
        if dest.is_symlink() or temp.is_symlink():raise ValueError("E02")
        # Count both the old destination and the full .part during replacement.
        if size()+len(raw)>=limit:
            state["notes"].append({"name":name,"bytes":len(raw),"reason":"budget"});return False
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,"wb") as f:f.write(raw)
        subprocess.run(["timeout","-k","1","30","mv","-f","--",str(temp),str(dest)],check=True)
        return True
    def read(path,cap=65536):
        with Path(path).open("rb") as f:return f.read(cap)
    def tail(path):
        with Path(path).open("rb") as f:
            f.seek(max(0,os.fstat(f.fileno()).st_size-65536));return f.read(65536)
    mem=["time_ns "+str(state["time_ns"]),"phase "+phase]
    try:
        entry=next(s.split(":",2)[2] for s in Path("/proc/self/cgroup").read_text().splitlines() if s.startswith("0::"))
        leaf=Path("/sys/fs/cgroup")/entry.lstrip("/")
        chain=[leaf,*leaf.parents]
        parent=next((p for p in chain if p.name=="job_"+job),None)
        step=next((p for p in chain if p.name.startswith("step_")),leaf)
        for label,path in (("job",parent),("step",step),("leaf",leaf)):
            mem.append(label+" "+(str(path) if path else "missing"))
            if path is None:continue
            for name in ("memory.current","memory.max","memory.peak","memory.events","memory.stat"):
                try:
                    raw=read(path/name,8192).decode("ascii","replace")
                    if name=="memory.stat":raw="\n".join(s for s in raw.splitlines() if s.split()[0] in ("anon","file","shmem","file_dirty","file_writeback","kernel"))+"\n"
                    mem.append(name+"\n"+raw.rstrip())
                except OSError as e:mem.append(name+" E"+str(e.errno))
    except (OSError,StopIteration,ValueError) as e:mem.append("E03 "+type(e).__name__)
    put("mem.txt",("\n".join(mem)+"\n").encode())
    result=subprocess.run(["timeout","-k","1","30","df","-Pk",str(node),"/dev/shm"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    put("df.txt",result.stdout[-65536:])
    for name,path in (("q.log",node/"ev/q.log"),("q.steps",node/"ev/q.steps"),("s.err",Path(err))):
        try:
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):continue
            put(name,tail(path))
        except OSError as e:state["notes"].append({"name":name,"errno":e.errno})
    for name in ("v.json","WAITING_REVIEW.json","f1.json"):
        if name in state["once"]:continue
        path=node/"ev/live"/name
        try:
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):continue
            n=path.stat().st_size
            if n>=1_500_000:state["once"][name]={"bytes":n,"copied":False,"reason":"size"};continue
            raw=read(path,1_500_000)
            if len(raw)>=1_500_000:state["once"][name]={"bytes":path.stat().st_size,"copied":False,"reason":"size"};continue
            state["once"][name]={"bytes":len(raw),"copied":put(name,raw)}
            if not state["once"][name]["copied"]:state["once"][name]["reason"]="budget"
        except OSError as e:state["notes"].append({"name":name,"errno":e.errno})
    put("live.json",(json.dumps(state,sort_keys=True)+"\n").encode(),4_000_000)
except Exception:
    pass
finally:
    if lock is not None:os.close(lock)
PYJ8
    return 0
}
j8_loop() (
    set +e
    trap 'exit 0' TERM INT
    while [[ ! -e "$N/j7.done" && ! -e "$N/j8.stop" ]]; do
        j8_snapshot live
        for ((j8_i=0; j8_i<6; j8_i++)); do
            [[ ! -e "$N/j7.done" && ! -e "$N/j8.stop" ]] || exit 0
            timeout -k 1 30 sleep 20 &
            wait "$!" || true
        done
    done
)
mkdir -p "$N"
if [[ "${J7_INNER:-0}" != 1 ]]; then j8_loop & J8_LIVE=$!; fi
exec >>"$N/j2.log" 2>>"$N/j2.err"
cat > "$N/j2.py" <<'PYJ2'
import os,sys,time
from pathlib import Path
kit,node,target,job,parent=sys.argv[1:6]
node=Path(node);target=Path(target)/'o'/job
sys.path.insert(0,str(Path(kit)/'b'))
from z import load,screen
words=load(Path(kit)/'k/g.json');hashes=load(Path(kit)/'b/wh.json')
interval=float(sys.argv[6]) if len(sys.argv)>6 else 600
# This process owns no training pipe; failed publication cannot close one.
def publish():
    try:
        target.mkdir(parents=True,exist_ok=True,mode=0o700)
        for name in ('j2.log','j2.err'):
            with (node/name).open('rb') as f:
                f.seek(max(0,os.fstat(f.fileno()).st_size-300000))
                raw=screen(f.read().decode('utf-8','replace'),words,hashes).encode()[-300000:]
            temp=target/(name+'.part')
            with temp.open('wb') as f:f.write(raw)
            os.replace(temp,target/name)
    except OSError as e:
        with (node/'j2.retry.log').open('a') as f:
            f.write(str(int(time.time()))+' E'+str(e.errno)+'\n')
while True:
    publish()
    try:os.kill(int(parent),0)
    except ProcessLookupError:break
    time.sleep(interval)
PYJ2
if [[ "${J7_INNER:-0}" != 1 ]]; then
setsid python3 -B -I -s "$N/j2.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" "$$" >>"$N/j2.retry.log" 2>&1 &
mkdir -p "$N/ev" "$O"
BW=$(python3 -B -I -s "$X/j8.py" b "$ROOT")
rc=0
J7_INNER=1 "$BW" --bind / / --dev-bind /dev /dev --proc /proc --bind "$N/ev" "$O" /bin/bash "$0" || rc=$?
timeout -k 1 30 touch "$N/j8.stop" || true
wait "$J8_LIVE" || true
j8_snapshot final
python3 -B -I -s "$X/j8.py" p "$N" "$O" "$ROOT" "$rc" "${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID}.log" "${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID}.err" || rc=1
python3 -B -I -s "$N/j2.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" 999999999 >>"$N/j2.retry.log" 2>&1 || true
exit "$rc"
fi
export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME" "$O"
cp "$X/rdiff.py" "$O/rdiff.py"
python3 -B -I -s "$ROOT/b/v.py" "$ROOT"
source "$ROOT/b/ep.sh"
python3 -B -I -s "$ROOT/b/resolve.py" --pool "/project/community/jjyeung/okh7" --output "$N/r0.json" 2>&1 | python3 -B -I -s "$ROOT/b/l.py" "$ROOT" > "$N/q.log"
setsid bash -c 'set -o pipefail; python3 -B -I -s "$1/b/x.py" "$1" "$2" "$3" 2>&1 | python3 -B -I -s "$1/b/l.py" "$1"' bash "$ROOT" "$N/r0.json" "$N" &
TK_WORK_PID=$!
( for i in $(seq 1 240); do sleep 60; test -e "$O/db_bytes.json" && break; if test -s "$O/routing_selection.json"; then nice -n 10 python3 -B -I -s "$X/dbb3.py" "$N" "$O" "$X/u" >> "$O/dbb.log" 2>&1 && break; fi; test ! -e "$N/j7.done" || break; done ) &
J7_DBB=$!
( for i in $(seq 1 240); do sleep 60; if test -s "$O/routing_selection.json" && test -s "$N/dr/p/q/selection/rows.sqlite" && test -s "$N/dr/p/q/base/rows.sqlite" && test ! -e "$O/rd0"; then python3 -B -I -s "$X/j8.py" m "$N/dr/p/q/n.json" "$N/dr" "$N/rdm.json" && nice -n 10 python3 -I -s -B "$X/rdiff.py" "$N/dr/p/q/selection/rows.sqlite" "$N/dr/p/q/base/rows.sqlite" --tree "$N/dr/p/s" --removal-manifest "$N/rdm.json" --base "$N/dr/p/q" --out "$O/rd0" > "$O/rdiff.log" 2>&1; echo "rdiff exit $?" >> "$O/rdiff.log"; break; fi; test ! -e "$N/j7.done" || break; done ) &
J7_RD=$!
rc=0; wait "$TK_WORK_PID" || rc=$?
touch "$N/j7.done"
echo "$(date -u +%FT%TZ) work exit $rc"
wait "$J7_DBB" || true
wait "$J7_RD" || true
test -e "$O/db_bytes.json" || nice -n 10 python3 -B -I -s "$X/dbb3.py" "$N" "$O" "$X/u" >> "$O/dbb.log" 2>&1 || echo "dbb none"
for f in $(find "$N" -maxdepth 7 \( -name materialization.json -o -name receipt.json -o -name r.json \) -size -20M 2>/dev/null); do g=$(echo "${f#$N/}" | tr / _); cp "$f" "$O/k_$g" 2>/dev/null || true; done
python3 -B -I -s "$N/j2.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" 999999999 >>"$N/j2.retry.log" 2>&1 || true
exit "$rc"
