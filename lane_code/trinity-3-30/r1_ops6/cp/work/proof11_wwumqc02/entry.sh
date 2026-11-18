set -euo pipefail
umask 077
/usr/bin/python3() { /scratch/jjyeung/envs/p1cpu/bin/python "$@"; }
ROOT=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_wwumqc02/kit
export TK_KIT_HOME="$ROOT"
source "$ROOT/b/c.sh"
S=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_wwumqc02/tmp/jjyeung/a_05b8ac69/root
U=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_wwumqc02/tmp/jjyeung/a_05b8ac69/root/aws/u
NX=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_wwumqc02/mount
NR=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_wwumqc02/mount/runs
X=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_wwumqc02/mount
AS=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_wwumqc02/as
AL=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_wwumqc02/al
P=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_wwumqc02/tmp/jjyeung/a_05b8ac69/root/c7d31ddd
EPOCHS=/scratch/jjyeung/orch_n30/r1_pkt/work/proof11_wwumqc02/tmp/jjyeung/a_05b8ac69/root/epochs
export TK_RUNS_DIR="$NR"
export TK_JOBDIR="${S%/root}/jobs/${SLURM_JOB_ID:?}.proof"
umask 077
mkdir -p -m 700 "${TK_JOBDIR%/*}"
mkdir -m 700 "$TK_JOBDIR"
read -r proof_record proof_record_sha < <(tk_current record)
sha_is "$S/c7d31ddd/anyhost/$proof_record_sha.json" "$proof_record_sha"
export R1_RUNTIME_RECORD="$P/anyhost/$proof_record_sha.json"
tk_nx
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

steps = dict(namespace='PASS', environment='PASS', pythonpath='PASS', trainer_tree='PASS', loader_import='PASS')
root = Path(sys.argv[1])
launch = json.loads((root/'k/launch.json').read_text())
cfg = json.loads((root/launch['config']['file']).read_text())
from student_pilot.p3_provenance import pinned, load
store = load(pinned(cfg['streams']['vqa']))
import sqlite3
database = Path(store['database']['path'])
with sqlite3.connect(database.as_uri()+'?mode=ro&immutable=1', uri=True) as connection:
    if not connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rows'").fetchone():
        raise ValueError('Staged store lacks rows')
steps['staged_store_startup'] = 'PASS'
expected = Path(launch['in_job_admission']['directory'])/'data_receipt.json'
if expected.exists():
    raise ValueError('Rehearsal must have no admission outputs')
try:
    main(sys.argv[1])
except FileNotFoundError as exc:
    if Path(exc.filename) != expected:
        raise
    steps['loader_main_startup'] = 'PASS'
    steps['admission_output_boundary'] = 'EXPECTED_MISSING'
else:
    raise ValueError('Loader did not stop at the admission output boundary')
receipt = dict(status='REHEARSAL_OK', steps=steps, production_authorized=False, admission_executed=False)
Path(os.environ['TK_JOBDIR'], 'tail.json').write_text(json.dumps(receipt, sort_keys=True)+'\n')
print(json.dumps(receipt, sort_keys=True), flush=True)
P
