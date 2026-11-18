set -e
export CUDA_VISIBLE_DEVICES=""
#!/bin/bash
# Conditional four-rank entry; a separate submission approval is required.
#SBATCH -A mt01 -p advanced -N1 --ntasks=1 --gres=gpu:4 -c 48 --mem=800G -t 13:00:00
#SBATCH --no-requeue --signal=B:USR1@3600
set -uo pipefail
umask 077
O=/project/community/jjyeung/okh7
private_dir() {
    [[ -d "$1" && ! -L "$1" && "$(stat -c %a -- "$1")" == 700 ]] || {
        printf 'Directory must be mode 0700; run: chmod 700 -- %q\n' "$1" >&2
        exit 3
    }
}
private_dir "$O"

export PATH=/usr/local/bin:/usr/bin:/bin
export TK_JOB_START="$(date +%s)"   # one wall clock for restore, staging, admission and training (job.sh must keep it)
KH=/project/community/jjyeung/okh7/x_c5f3847d RUN=/tmp/jjyeung/a_26cc98b7/runs/26cc98b7
RS=/project/community/jjyeung/okh7/r/26cc98b7 LOG=$KH/o/${SLURM_JOB_ID}.w.steps
step() { printf '%s | %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }
newest() {  # newest verified slot: prints "slot step" (empty if none)
    for s in A B; do [[ -f $RS/$s.json ]] && /usr/bin/python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["slot"], d["step"]) if d.get("verified") is True else None' "$RS/$s.json"; done | sort -k2,2n | tail -1
}
# BEGIN directory preflight
NL=/tmp/jjyeung/a_26cc98b7
private_dir "$KH"
for p in /tmp/jjyeung "$NL" "$NL/runs" "$RUN" "$O/r" "$RS"; do
    [[ ! -e "$p" && ! -L "$p" ]] || private_dir "$p"
done
for p in "$NL/runs"/* "$NL/runs"/.[!.]* "$NL/runs"/..?*; do
    [[ ! -e "$p" && ! -L "$p" ]] && continue
    [[ "${p##*/}" == 26cc98b7 && -d "$p" && ! -L "$p" ]] || { echo 'foreign run directory; refusing' >&2; exit 3; }
done
mkdir -p -m 700 /tmp/jjyeung "$NL" "$NL/runs" "$RUN" "$O/r" "$RS" "$KH/o" || exit 3
for p in "$NL" "$NL/runs" "$RUN" "$RS"; do private_dir "$p"; done
# END directory preflight
free_kib=$(df -Pk /tmp | awk 'NR==2 {print $4}')
step "wrapper start on $(hostname -s); /tmp free $(( free_kib / 1048576 )) GiB; TK_JOB_START=$TK_JOB_START ($(date -u -d @"$TK_JOB_START" +%FT%TZ))"
# Final review F4: a leg needs about 3.6 TB free at its first save; refuse below 3.8 TB (decimal) in the first minute.
(( free_kib * 1024 >= 3800000000000 )) || { step "refused: /tmp free $(( free_kib * 1024 )) B is below 3.8 TB"; exit 5; }
# Export sessions: every milestone of the plan has its four part sessions for this run, in a file only the account reads.
/usr/bin/python3 -I -c '
import json, os, stat, sys
p, run = sys.argv[1], sys.argv[2]
if stat.S_IMODE(os.stat(p).st_mode) != 0o600: sys.exit("sess.json mode is not 600")
d = json.load(open(p)); ms = ["m100", "m200", "mstop", "mstopB", "mstopC"]
want = {"q8/8865619b/%s_%s.tar.part%02d-of-04" % (run, m, i) for m in ms for i in range(4)}
miss = sorted(want - set(d))
sys.exit("sess.json lacks %d sessions, first %s" % (len(miss), miss[:1]) if miss else 0)' "$KH/sess.json" "${RUN##*/}" 2>> "$LOG" \
    || { step "refused: export sessions incomplete for run ${RUN##*/}"; exit 5; }
step "export sessions present for run ${RUN##*/}"
# Actual archive contents of every new staging entry, before c.sh extracts them (vt.py; sealed k/0.json pinned inside).
/usr/bin/python3 -I /project/community/jjyeung/okh7/i_c5f3847d/v.py "$KH" /project/community/jjyeung/okh7/i_c5f3847d/b0.json > "$KH/o/${SLURM_JOB_ID}.vt.json" 2>&1 \
    || { step "refused: staging entry check: $(tail -c 300 "$KH/o/${SLURM_JOB_ID}.vt.json")"; exit 5; }
step "staging entries verified"

set -e
#!/bin/bash
#SBATCH --partition=advanced
#SBATCH --nodes=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=13:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:USR1@3600
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
export TK_JOB_START="${TK_JOB_START:-$(date +%s)}"
ROOT="$KH"
/usr/bin/python3 -B "$ROOT/b/a.py" "$ROOT"
/bin/bash "$ROOT/b/p0.sh" "$ROOT"
/usr/bin/python3 -I "$ROOT/b/g.py" "$ROOT" p

/bin/bash "$ROOT/b/r.sh" p 0
export TK_KIT_HOME="$ROOT"
source "$ROOT/b/c.sh"
tk_bwrap
tk_env
tk_pythonpath p
"${BW[@]}" "$PILOT_VENV/bin/python" -B - "$X" <<P
from student_pilot.loader_audit import main
import sys
main(sys.argv[1])
P
