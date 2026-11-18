set -euo pipefail
umask 077
ROOT=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_v81k89l8/kit

/bin/bash "$ROOT/b/r.sh" p 0
export TK_KIT_HOME="$ROOT"
source "$ROOT/b/c.sh"
S=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_v81k89l8/tmp/jjyeung/a_673bc60f/root
U=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_v81k89l8/tmp/jjyeung/a_673bc60f/root/aws/u
NX=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_v81k89l8/tmp/jjyeung/a_673bc60f/x_170956
NR=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_v81k89l8/tmp/jjyeung/a_673bc60f/runs
X=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_v81k89l8/mount
AS=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_v81k89l8/as
AL=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_v81k89l8/al
P=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_v81k89l8/tmp/jjyeung/a_673bc60f/root/c7d31ddd
EPOCHS=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_v81k89l8/tmp/jjyeung/a_673bc60f/root/epochs
export TK_RUNS_DIR="$NR"
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
