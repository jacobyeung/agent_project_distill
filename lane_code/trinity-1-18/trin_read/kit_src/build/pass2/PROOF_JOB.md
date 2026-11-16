# Slurm proof and production commands

Run these commands from `/scratch/jjyeung/orch_n30/evalx27/work` on Trinity. They are operator commands; the builder has submitted nothing. Use a fresh token and destination for every job. Neither batch stages files on the Orchard login node. Both unpack from stdin into Slurm-private `/tmp`; only the bounded result packet reaches the home pool.

The subtype requirement selects **16 items**: two for each of the three direction subtypes and two for each of the other five tasks. `proof/selection.py` fixes the choice deterministically and covers all three dataset labels. Proof scores are synthetic.

## Prepare and submit the proof

```bash
export PYTHONDONTWRITEBYTECODE=1
PY="$PWD/kit/.venv/bin/python"
LAUNCHER="$PWD/kit/launcher/orchard_launcher.py"
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
TOKEN=$(python3 -c 'import secrets;print("p"+secrets.token_hex(5))')
DEST="$PWD/kit/build/$TOKEN"
"$PY" "$LAUNCHER" prepare --mode proof --token "$TOKEN" --destination "$DEST"
SUBMIT_COMMAND=$("$PY" "$LAUNCHER" submit-command --destination "$DEST")
printf '%s\n' "$SUBMIT_COMMAND"
timeout 300 bash "$OSSH" "$SUBMIT_COMMAND" < "$DEST/BATCH.sh" > "$DEST/SUBMIT.out" 2> "$DEST/SUBMIT.err"
"$PY" "$LAUNCHER" record-submission --destination "$DEST"
JOB=$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1]))["job"])' "$DEST/SUBMISSION.json")
```

`SUBMIT_COMMAND` runs `sbatch --test-only`, then submits the same batch through stdin. Its proof argv uses `general`, no `--gres`, 16 CPUs, 128G, and 02:00:00. The name is `a15_cot_ap<TOKEN>`. If submission times out or returns an ambiguous response, inspect the queue using the token; do not repeat submission.

Poll manually, at most once a minute, using the wrapper's existing ControlMaster connection:

```bash
timeout 300 bash "$OSSH" "TZ=UTC squeue -j $JOB -o '%.18i %.32j %.10T %.10M %.20S'"
timeout 300 bash "$OSSH" "TZ=UTC sacct -j $JOB --format=JobID,JobName,State,ExitCode,Elapsed,Start,End -P"
```

After the job exits, fetch from `/home/jjyeung/okit/evalx_results/$TOKEN/` through the same wrapper. The fetcher checks the receipt, archive SHA256, final trace SHA256, token, job, and plan. It writes only under `DEST` on Trinity.

```bash
"$PY" "$LAUNCHER" fetch --destination "$DEST"
"$PY" - "$DEST" <<'PY'
import json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);out=p/'packet';out.mkdir()
with tarfile.open(p/'fetched/result.tar.gz') as archive:
    archive.extractall(out,filter='data')
exit=json.loads((p/'fetched/EXIT.json').read_text())
assert exit['status']=='COMPLETE',exit
print((out/'COMPLETE.json').read_text())
print((out/'PARITY.json').read_text())
PY
"$PY" kit/proof/lines_report.py "$DEST/fetched/TRACE.json.gz" --json "$DEST/LINES.json" > "$DEST/LINES.txt"
```

Read `LINES.txt`, `packet/metadata/CHECKS.json`, `packet/FRAME_PLAN.json`, `packet/PARITY.json`, `packet/STEPS.jsonl`, logs, and staging receipts. Packet/decode equality is recorded separately for every video; a mismatch is evidence, not a substituted frame count. The decoded plan controls the frame gate. Do not infer GPU-engine correctness from fake generation or from line coverage.

The packet consists of `result.tar.gz`, `EXIT.json`, `JOB.log`, `TRACE.json.gz`, and `TRACE.pin.json`, together below 20,000,000 bytes. The archive includes a trace snapshot before publishing. The separate final trace includes the real publisher and archive writer, which cannot be added retroactively to the archive they just wrote. Fetch the final sidecar for `lines_report.py`.

## Prepare and submit production

Use the same kit bytes, commands, and return pool. Choose a fresh token. Production processes all 4,008 items and requires an H100. Its argv remains 1 GPU, 16 CPUs, 200G, 06:00:00.

```bash
TOKEN=$(python3 -c 'import secrets;print("a"+secrets.token_hex(5))')
DEST="$PWD/kit/build/$TOKEN"
"$PY" "$LAUNCHER" prepare --mode production --token "$TOKEN" --destination "$DEST"
SUBMIT_COMMAND=$("$PY" "$LAUNCHER" submit-command --destination "$DEST")
timeout 300 bash "$OSSH" "$SUBMIT_COMMAND" < "$DEST/BATCH.sh" > "$DEST/SUBMIT.out" 2> "$DEST/SUBMIT.err"
"$PY" "$LAUNCHER" record-submission --destination "$DEST"
JOB=$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1]))["job"])' "$DEST/SUBMISSION.json")
timeout 300 bash "$OSSH" "TZ=UTC squeue -j $JOB -o '%.18i %.32j %.10T %.10M %.20S'"
timeout 300 bash "$OSSH" "TZ=UTC sacct -j $JOB --format=JobID,JobName,State,ExitCode,Elapsed,Start,End -P"
# Run after completion:
"$PY" "$LAUNCHER" fetch --destination "$DEST"
```

For the same token and optional input plan, the two prepared packages differ only in CONFIG mode; tests compare every embedded member. Fresh tokens also change CONFIG paths and derived hashes, payload member paths, and the bootstrap directory. Source bytes remain identical. Both modes compute the 288-video plan in the job, so no login-node planning or upload is needed. An optional `--frame-plan` must be the exact returned decoded plan and must be supplied to both preparations for a byte-comparison audit.

The production archive limit remains below 200 MB. The pool currently has under 100 MB free: the operator must make enough space in the result pool before production. The kit does not delete pool contents. Proof remains below 20 MB regardless of the production limit.
