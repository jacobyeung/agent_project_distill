set -euo pipefail
umask 077
/usr/bin/python3() { /data2/jjyeung/envs/planner/bin/python "$@"; }
ROOT=/scratch/jjyeung/orch_n30/review_r1c3/copy/work/proof11_o083nei3/kit

/bin/bash "$ROOT/b/r.sh" p 0
export TK_KIT_HOME="$ROOT"
source "$ROOT/b/c.sh"
S=/scratch/jjyeung/orch_n30/review_r1c3/copy/work/proof11_o083nei3/tmp/jjyeung/a_05b8ac69/root
U=/scratch/jjyeung/orch_n30/review_r1c3/copy/work/proof11_o083nei3/tmp/jjyeung/a_05b8ac69/root/aws/u
NX=/scratch/jjyeung/orch_n30/review_r1c3/copy/work/proof11_o083nei3/tmp/jjyeung/a_05b8ac69/x_170956
NR=/scratch/jjyeung/orch_n30/review_r1c3/copy/work/proof11_o083nei3/tmp/jjyeung/a_05b8ac69/runs
X=/scratch/jjyeung/orch_n30/review_r1c3/copy/work/proof11_o083nei3/mount
AS=/scratch/jjyeung/orch_n30/review_r1c3/copy/work/proof11_o083nei3/as
AL=/scratch/jjyeung/orch_n30/review_r1c3/copy/work/proof11_o083nei3/al
P=/scratch/jjyeung/orch_n30/review_r1c3/copy/work/proof11_o083nei3/tmp/jjyeung/a_05b8ac69/root/c7d31ddd
EPOCHS=/scratch/jjyeung/orch_n30/review_r1c3/copy/work/proof11_o083nei3/tmp/jjyeung/a_05b8ac69/root/epochs
export TK_RUNS_DIR="$NR"
export TK_JOBDIR="${S%/root}/jobs/${SLURM_JOB_ID:?}.proof"
umask 077
mkdir -p -m 700 "${TK_JOBDIR%/*}"
mkdir -m 700 "$TK_JOBDIR"
mkdir -m 700 "$TK_JOBDIR"
read -r proof_record proof_record_sha < <(tk_current record)
sha_is "$S/c7d31ddd/anyhost/$proof_record_sha.json" "$proof_record_sha"
export R1_RUNTIME_RECORD="$P/anyhost/$proof_record_sha.json"
tk_bwrap
tk_env
tk_pythonpath p
"${BW[@]}" "$PILOT_VENV/bin/python" -B - "$X" <<P
import json, os, sys
from pathlib import Path
from v import tree
cur = json.loads((Path(sys.argv[1])/"k/0.json").read_text())
tree({"path": cur["record"]["file"], "sha256": cur["record"]["sha256"]}, os.environ["TRAINER"], cur["commit"])
sys.path.insert(0, os.environ["TRAINER"])
from student_pilot.loader_audit import main
main(sys.argv[1])
P
