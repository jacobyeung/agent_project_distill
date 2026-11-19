set -euo pipefail
SECONDS=0
export PATH=/usr/local/bin:/usr/bin:/bin
HX="${1:?}"
export TK_KIT_HOME="$HX"
PYTHONPATH="$HX/b" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" \
    /usr/bin/python3 -B "$HX/b/p0.py" "$HX" p --metadata-only
source "$HX/b/c.sh"
export TK_JOBDIR=/tmp/jjyeung/a_6ed2c7aa/jobs/${SLURM_JOB_ID:?}.preflight
trap 'for report in "$NX/o/${SLURM_JOB_ID}".preflight.*.json; do [[ ! -f "$report" ]] || cp "$report" "$HX/o/"; done' EXIT
tk_stage preflight
/usr/bin/python3 -I - "$CUR" "$HX" "$NX" "$IN" "$SLURM_JOB_ID" <<'PYINPUTS'
import json, os, sys
current, home, node, cache, job = sys.argv[1:]
data = json.load(open(current))
prefix = "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/"
inputs = []
for key in ("venv", "closure", "trainer", "record", "np"):
    if key not in data:
        continue
    file = data[key]["file"]
    physical = node+"/"+file[len(prefix):] if file.startswith(prefix) else file
    inputs.append(dict(key=key, file=file, bytes=os.stat(physical).st_size, sha256=data[key]["sha256"]))
inputs.append(dict(key="d00", file=cache+"/d00", bytes=os.stat(cache+"/d00").st_size,
                   inventory_sha256=data["fla"]["sha256"]))
value = dict(schema="s1-import-preflight-inputs-v1", inputs=inputs,
             runtime_input_bytes=sum(row["bytes"] for row in inputs), model_or_data_staged=False)
with open(home+"/o/"+job+".preflight.inputs.json", "x") as output:
    json.dump(value, output, sort_keys=True); output.write("\n")
print(json.dumps(value, sort_keys=True), flush=True)
PYINPUTS
tk_bwrap
tk_env
export TK_STAGE_ROOT="$S"
for mode in p t u; do
    (
        tk_pythonpath "$mode"
        "${BW[@]}" "$PILOT_VENV/bin/python" -B "$X/b/p0.py" "$X" "$mode"
    )
done
tk_step "production import preflight PASS seconds=$SECONDS"
