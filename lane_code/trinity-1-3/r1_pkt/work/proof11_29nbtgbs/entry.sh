set -euo pipefail
umask 077
/usr/bin/python3() { /scratch/jjyeung/envs/p1cpu/bin/python "$@"; }
ROOT=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_29nbtgbs/kit

/bin/bash "$ROOT/b/r.sh" p 0
export TK_KIT_HOME="$ROOT"
source "$ROOT/b/c.sh"
S=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_29nbtgbs/tmp/jjyeung/a_05b8ac69/root
U=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_29nbtgbs/tmp/jjyeung/a_05b8ac69/root/aws/u
NX=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_29nbtgbs/tmp/jjyeung/a_05b8ac69/x_170956
NR=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_29nbtgbs/tmp/jjyeung/a_05b8ac69/runs
X=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_29nbtgbs/mount
AS=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_29nbtgbs/as
AL=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_29nbtgbs/al
P=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_29nbtgbs/tmp/jjyeung/a_05b8ac69/root/c7d31ddd
EPOCHS=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_29nbtgbs/tmp/jjyeung/a_05b8ac69/root/epochs
export TK_RUNS_DIR="$NR"
export TK_JOBDIR="${S%/root}/jobs/${SLURM_JOB_ID:?}.proof"
umask 077
mkdir -p -m 700 "${TK_JOBDIR%/*}"
mkdir -m 700 "$TK_JOBDIR"
read -r proof_record proof_record_sha < <(tk_current record)
sha_is "$S/c7d31ddd/anyhost/$proof_record_sha.json" "$proof_record_sha"
export R1_RUNTIME_RECORD="$P/anyhost/$proof_record_sha.json"
tk_bwrap
tk_env
tk_pythonpath p
"${BW[@]}" "$PILOT_VENV/bin/python" -B - "$X" <<P
from student_pilot.loader_audit import main
import sys
main(sys.argv[1])
P
