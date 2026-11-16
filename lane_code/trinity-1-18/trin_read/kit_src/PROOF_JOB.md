# Slurm proof and production commands

Run from `/scratch/jjyeung/orch_n30/evalx27/work` on Trinity. The builder has not contacted Orchard or submitted a job. Both modes use one H100, partition general, 16 CPUs and 200G. Proof has a two-hour limit; production has six hours. Staging uses Slurm-private `/tmp`.

The default return pool is `/project/community/jjyeung/okh7/x27ret`. The job tests it before staging with a 4 MiB write, fsync and SHA256 readback in a subprocess with a 60-second deadline. Only `.wtest` is removed. A failure refuses the run. Pool operations hold a lock and enforce total use below 100 MB. No old return is cleaned automatically.

## Prepare and submit

```bash
export PYTHONDONTWRITEBYTECODE=1
PY="$PWD/kit/.venv/bin/python"
LAUNCHER="$PWD/kit/launcher/orchard_launcher.py"
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
POOL=/project/community/jjyeung/okh7/x27ret
TOKEN=$(python3 -c 'import secrets;print("p"+secrets.token_hex(5))')
DEST="$PWD/kit/build/$TOKEN"
"$PY" "$LAUNCHER" prepare --mode proof --pool "$POOL" --token "$TOKEN" --destination "$DEST"
SUBMIT_COMMAND=$("$PY" "$LAUNCHER" submit-command --destination "$DEST")
printf '%s\n' "$SUBMIT_COMMAND"
timeout 300 bash "$OSSH" "$SUBMIT_COMMAND" < "$DEST/BATCH.sh" > "$DEST/SUBMIT.out" 2> "$DEST/SUBMIT.err"
"$PY" "$LAUNCHER" record-submission --destination "$DEST"
JOB=$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1]))["job"])' "$DEST/SUBMISSION.json")
```

The submission command runs `sbatch --test-only`, then submits the same stdin batch. Its argv includes `--gres=gpu:1 --cpus-per-task=16 --mem=200G --time=02:00:00 --partition=general`; the job checks the assigned H100 before and after staging. Reconcile any ambiguous submission using its token before taking another action.

Poll manually at most once per minute through the existing ossh connection:

```bash
timeout 300 bash "$OSSH" "TZ=UTC squeue -j $JOB -o '%.18i %.32j %.10T %.10M %.20S'"
timeout 300 bash "$OSSH" "TZ=UTC sacct -j $JOB --format=JobID,JobName,State,ExitCode,Elapsed,Start,End -P"
```

## Proof phases

Phase A stages all runtimes, the base, the step-544 export, and all 288 SHA-verified videos. It decodes the full frame plan, compares first-20 dev prompt bytes with the real processor, and runs 14 official items through the fake engine. No official item enters a real model. The deterministic allocation is two per non-direction task plus two easy, one medium and one hard direction item. This retains all eight subtypes within the explicitly requested 14-item total; two per subtype would require 16. All frame, budget, merge and scorer checks must pass.

Phase B starts in a fresh interpreter only after Phase A passes. It uses the unchanged accepted `direct.py`/r3/r5 bind and launch path and runtime_2 kit, verifies the step-544 export, and sets only `smoke_items=20` among reader settings. It verifies the worker's exact sort order against accepted job 169526. The full payload stays pinned; the public frame builder realizes only the selected captures. The accepted `pull.py` reads 576 unique PNGs from `/project/community/jjyeung/cp4tk_fr/k6tk`. Each selected receipt was reconstructed from the unchanged adapter and accepted media audits and verified against the accepted `frames/0.json` hash.

Phase B runs real vLLM, budget derivation and merges. `b0/PHASE_B.json` gives item-level comparisons and exact counts for prompt bytes, ON16k token IDs/raw text, and each budget's answers/scores. It compares the 16 recorded accepted prompt-ID hashes; full prompt-ID arrays are absent from the accepted journals. Its internal parity probe requires 16 ID checks and two pixel checks. Generation differences are reported with actual and accepted mean scores on the same 20 items; they do not automatically fail the job. Prompt or parity differences do fail it. Smoke summaries retain the kit's smoke designation.

## Fetch and inspect

The publisher verifies both a pool copy and a GCS copy at `gs://cmu-gpucloud-jjyeung/q8/x27r/$TOKEN/`. Each upload has a timeout and a generation-pinned SHA256 readback. `RETURN_RECEIPT.json` and `JOB.log` record object generations, hashes and verified channels. Return transport succeeds if either copy verifies; computational failures remain failures. Proof return files stay below 20 MB; production compressed packets stay below 90 MB. A failed pool cannot prevent the independent GCS attempt.

```bash
"$PY" "$LAUNCHER" fetch --destination "$DEST"
"$PY" - "$DEST" <<'PY'
import json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]); out=p/'packet'; out.mkdir()
with tarfile.open(p/'fetched/result.tar.gz') as archive:
    archive.extractall(out,filter='data')
receipt=json.loads((p/'fetched/EXIT.json').read_text())
assert receipt['status']=='COMPLETE',receipt
for name in ('COMPLETE.json','PARITY.json','metadata/CHECKS.json','b0/PHASE_B.json'):
    print(name,(out/name).read_text())
print((p/'fetched/FETCH.json').read_text())
PY
"$PY" kit/proof/lines_report.py "$DEST/fetched/TRACE.json.gz" --json "$DEST/LINES.json" > "$DEST/LINES.txt"
```

Fetch tries the pool first and GCS second. GCS bytes stream through ossh stdout directly into `DEST/fetched` on Trinity; it never spools them on Orchard login or in the pool. `FETCH.json` identifies the channel and whether the final publisher trace or the archive's earlier snapshot was obtained. A failed final trace upload does not invalidate an already verified result packet; it leaves a coverage gap. Review `LINES.txt`, `FRAME_PLAN.json`, staging receipts, `STEPS.jsonl` and logs. Coverage does not establish model correctness.

For a packet of 20 MB or more, fetch stops **before the archive transfer**, writes the receipt locally, and prints the exact transfer command. The operator must register a governor stream before executing it. The printed command streams the selected source through ossh stdout, throttled to 8 MB/s, directly into the lane. Use that exact printed command after registration. For a small packet, the same `fetch --destination "$DEST"` command performs both pool and GCS paths automatically; no separate remote spool is needed.

Run the printed command once. Verify the registered transfer against the saved receipt:

```bash
"$PY" - "$DEST" <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path('kit/launcher').resolve()))
import orchard_results
p=Path(sys.argv[1]);c=json.loads((p/'CONFIG.json').read_text());r=json.loads((p/'fetched/EXIT.json').read_text())
orchard_results.verify(r,p/'fetched/result.tar.gz',c['plan_sha256'])
print('Return verified')
PY
```

## Production

Use the same kit bytes and operator commands, with a fresh token and destination:

```bash
TOKEN=$(python3 -c 'import secrets;print("a"+secrets.token_hex(5))')
DEST="$PWD/kit/build/$TOKEN"
"$PY" "$LAUNCHER" prepare --mode production --pool "$POOL" --token "$TOKEN" --destination "$DEST"
SUBMIT_COMMAND=$("$PY" "$LAUNCHER" submit-command --destination "$DEST")
timeout 300 bash "$OSSH" "$SUBMIT_COMMAND" < "$DEST/BATCH.sh" > "$DEST/SUBMIT.out" 2> "$DEST/SUBMIT.err"
"$PY" "$LAUNCHER" record-submission --destination "$DEST"
JOB=$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1]))["job"])' "$DEST/SUBMISSION.json")
timeout 300 bash "$OSSH" "TZ=UTC sacct -j $JOB --format=JobID,JobName,State,ExitCode,Elapsed,Start,End -P"
# After completion; packets >=20 MB require registration as described above.
"$PY" "$LAUNCHER" fetch --destination "$DEST"
```

Production runs only the 4,008-item official read. With the same token and pool, embedded files differ only in CONFIG `mode` and `phase_b`; submission time limits differ. Fresh tokens also change derived paths and hashes. Neither mode writes returns to `/home`.
