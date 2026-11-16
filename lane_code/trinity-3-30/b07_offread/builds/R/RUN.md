# Operator commands

This kit prepares one direct-only read per benchmark and selected export. Run these commands on `trinity-3-30`. The builder has submitted nothing. The submitted stdin batch is the only new input sent to Orchard; the package archives and `BINDING.json` stay on Trinity.

The init-selection owner must supply the final JSON decision under item 7 of `NEXT_LEG_INIT_RULE_20261116.md`. Its `selected_sha256` must equal the whole-tar SHA256 in the selected plain-text `.done` file. Its `selected_step` must be one of 200, 400, 600, 800 or 1000 and match the object `q8/8865619b/359fcc3c_m<step>.tar`. Its `init_rule_sha256` must be `d53f9c1ac74c4c9e7a3d3bbdbcf74a0853ca529d62bb1d3afe1c03f121e260ba`. Its `d0_ended` object must contain a nonempty `event` reference and a `reason` of `completed_step_1000`, `stopped_under_rule` or `no_further_allocation`. The launcher checks these fields and the reviewed completion-record parser; it does not choose a milestone or evaluate the owner's selection decision. Use the same decision and export for both benchmarks. Do not infer the decision from an official benchmark result.

Every launcher import and action verifies all six offkit source hashes against `out/OFFKIT_PINS.json`. Keep that manifest with the extracted packages. A missing manifest or changed module refuses before preparation, reporting or any other action. Production binding requires the ledger. The binding hash covers the accepted 32-duplicate frame layout, and reports take their identity and mode from the verified binding.

Set the two input paths to the owner's actual records. The example deliberately requires existing environment variables rather than inventing a selected export.

```bash
cd /scratch/jjyeung/orch_n30/b07_offread/builds/R
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
LAUNCHER=$PWD/kit/rebind.py
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
LEDGER=/scratch/jjyeung/orch_n30/b07_offread/out/OFFICIAL_READ_LEDGER.jsonl
: "${SELECTED_DONE:?Set SELECTED_DONE to the selected export completion record}"
: "${INIT_SELECTION:?Set INIT_SELECTION to the final init-selection JSON}"
EXPORT="done:$SELECTED_DONE"
```

For an explicit step544 reproduction, use `EXPORT=step544` and omit `--init-selection`. Do not submit both step544 and D0 by default. The accepted step544 returns already provide the reference scores.

Prepare VSI-Bench with this command.

```bash
TOKEN=a$("$PY" -B -c 'import secrets; print(secrets.token_hex(6))')
DEST=$PWD/work/$TOKEN
"$PY" -B "$LAUNCHER" prepare --benchmark vsibench5130 --export "$EXPORT" \
  --init-selection "$INIT_SELECTION" --ledger "$LEDGER" --mode production \
  --token "$TOKEN" --destination "$DEST"
```

Prepare ReVSI with this command, using a fresh token and the same export selection. Finish and record the first submission before preparing or submitting the second.

```bash
TOKEN=a$("$PY" -B -c 'import secrets; print(secrets.token_hex(6))')
DEST=$PWD/work/$TOKEN
"$PY" -B "$LAUNCHER" prepare --benchmark revsi999t32 --export "$EXPORT" \
  --init-selection "$INIT_SELECTION" --ledger "$LEDGER" --mode production \
  --token "$TOKEN" --destination "$DEST"
```

Use the following submission block once for each prepared destination. Coordinate the general queue allocation with its owner before submitting. The generated command performs `sbatch --test-only` and then submits the same stdin batch. It requests one H100 through `general`, with `--gres=gpu:1 --cpus-per-task=16 --mem=200G --time=06:00:00` on the command line. The batch contains no `#SBATCH` directives. Record the response immediately. An uncertain response must be reconciled by token before any further submission.

```bash
"$PY" -B -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); assert p.stat().st_size < 20000000' "$DEST/BATCH.sh"
CMD=$("$PY" -B "$LAUNCHER" submit-command --destination "$DEST" --ledger "$LEDGER")
timeout 300 bash "$OSSH" "$CMD" < "$DEST/BATCH.sh" > "$DEST/SUBMIT.out" 2> "$DEST/SUBMIT.err"
"$PY" -B "$LAUNCHER" record-submission --destination "$DEST" --ledger "$LEDGER"
JOB=$("$PY" -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["job"])' "$DEST/SUBMISSION.json")
```

No generated input exceeds 20 MB. The launcher additionally caps the embedded batch bundle at 3 MiB after base64 encoding. No bulk input upload is needed: the job uses the registered Orchard runtimes, base, media and four GCS export parts. If an operator adds a new input over 20 MB, stop this workflow and arrange its opaque, governed upload before submission; do not send the local package archives or binding records to Orchard.

Poll no more than once per minute. Each invocation below is a single observation.

```bash
sleep 60
timeout 300 bash "$OSSH" "TZ=UTC squeue -j $JOB -o '%.18i %.32j %.10T %.10M %.20S'"
sleep 60
timeout 300 bash "$OSSH" "TZ=UTC sacct -j $JOB --format=JobID,JobName,State,ExitCode,Elapsed,Start,End -P"
```

Fetch and report after completion.

```bash
"$PY" -B "$LAUNCHER" fetch --destination "$DEST"
"$PY" -B "$LAUNCHER" report --destination "$DEST"
```

The fetch command registers every archive transfer with the existing serial IO governor. It starts the source stopped, waits for the local `ratelimit.py` process, and registers the verified pipe through `/scratch/jjyeung/io_governor/register.py`. It uses tier 3, an 8 MB/s ceiling, and a 1000 B/s initial floor. It waits for admission, verifies the returned size and SHA256, and renames the completed stream record. The node agent must already be live. The kit neither starts a governor nor retries an interrupted transfer. Receipts and other bounded metadata use the accepted transport. The pool and GCS fallback remain available; an incomplete archive is never reported.

The proposed return pool is `/project/community/jjyeung/okh7/9e6b70a213c84fd0/`. GCS returns use `gs://cmu-gpucloud-jjyeung/q8/9e6b70a213c84fd0/<token>/`. The pool retains the readk write test, lock and 100 MB total cap. Production returns remain below 90 MB each. The pool can refuse a later return if its retained bytes exhaust the shared cap; the independent GCS channel can still return it. Token meanings reside only in `work/ORCHARD_LEDGER.jsonl`. Reports identify the export, reader, benchmark, primary arm and budget on Trinity.

Allow about 35 minutes for VSI-Bench and 13 minutes for ReVSI, based on accepted jobs 170008 and 170037. Add D0 staging and full export verification. For a 21.583 GB archive, the transfer term is `21,583 / throughput_MB_per_second` seconds; it is about 3.6 minutes at 100 MB/s or 12 minutes at 30 MB/s. Reserve another 5–15 minutes for extraction and full verification. These throughput figures are planning assumptions, not measurements. Plan approximately 44–62 minutes for VSI-Bench and 22–40 minutes for ReVSI, plus queue time and governed return time.

Reserve 220 GB of additional job-local disk for VSI-Bench and 180 GB for ReVSI. Start with at least 440 GB and 400 GB free, respectively, to retain the accepted 200 GiB floor. These conservative estimates cover retained runtime/export archives, extracted runtimes, base and export weights, reader model copies, frames and returns. Staging checks actual free space. ReVSI's pinned media total is 318,248,080 bytes. The VSI media inventory provides hashes but no byte counts, so its disk estimate remains conservative.

Use `--mode proof` only for an explicitly requested proof allocation. Proof uses the accepted small item selection and fake generation. A D0 proof omits the accepted step544-only Phase B token comparison; the accepted prompt proof and processor checks still run. Production has no Phase B.

The CPU tests use local stand-ins and never authorize a submission. Their fixture bindings say `EXPORT fixture`, and submit-command rejects their local bootstrap roots. Their reported values are not benchmark results.
