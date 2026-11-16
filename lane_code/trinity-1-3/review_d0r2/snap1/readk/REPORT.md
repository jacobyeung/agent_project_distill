The kit builds one-H100 `general` reads for steps 100, 200 and 400: main 1,525, away 150, and forward 150. `--camera` adds 450 items; it is off by default. The accepted duplicate layout, 32 anchors, timing, ON16k/B2048/B4096 budgets, and answer policy remain pinned. B2048 is primary.

The job accepts the uploader’s exact plain-text `.done` line (`object bytes sha256`), binds its bucketless object to run 359fcc3c and the requested step, constructs its URI under `gs://cmu-gpucloud-jjyeung`, concatenates four GCS parts, checks whole-tar bytes/SHA256 before extraction, applies build_t5's unchanged admission function, and runs the unchanged export checker in full mode. Each family uses a fresh process on the same card. Failure stops subsequent families without retry.

Returns contain `ITEMS.jsonl`, `SUMMARY.json`, authenticated score reports, binding/staging evidence, and each family’s `a0/results/{0,budget_2048/0,budget_4096/0}/items_a0.jsonl` raw journals. Gzip level 6 preserves the 512 MiB expanded and sub-90 MB compressed limits. The proposed pool is `/project/community/jjyeung/okh7/ae71c903`; GCS uses `gs://cmu-gpucloud-jjyeung/q8/ae71c903/<token>/`. The pool retains its 4 MiB fsync/hash test, locks operations, and enforces 100 MB. Both return channels verify independently. Token meanings are recorded in `LEDGER.jsonl`.

Accepted A reports exist on this host at `/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/{main,away,forward}/report/B2048.json`; predictions exist at `direct/<family>/results/0/budget_2048.jsonl`. All 150 away and 150 forward items exist, so no second model arm is needed. `evidence/A544.jsonl` contains their normalized records; source hashes are in `evidence/ACCEPTED.json`. A has away accuracies 38/20/6% and 74/150 pairs alike (49.33%).

`f1f2.py` uses the exact `paired()` function from `kit/reader/work/vendor/r5/report.py:36`, with B first, 10,000 room draws, seed 17, and interpolated percentiles. F1 decides on seven types: route planning, object counting, direction easy/medium/hard, relative distance and object-size estimation. Relative count and relative object size are information only. F2 uses TRACE_RULING 2.7’s lower-bound reading; point-estimate failures and the corresponding verdict appear separately as information. Twin equality compares semantic option contents. Step 100 has no verdict; step 200 implements STOP, CONTINUE_TO_400, and CONTINUE. Step 400 returns STOP if F2 fails and CONTINUE otherwise, reporting F1 without using it to stop. F3/F4 are explicitly unevaluated and do not stop this direct read.

The total-count guard is unavailable on the accepted inventory, which contains only single-object counting under `object_counting`. The script prints the constant-7/46.30% guard as unavailable and evaluates the constant-2/61.87% single-count guard. It does not invent total-count observations.

Run the following block for `STEP=100`; use `STEP=200` or `STEP=400` with a fresh token for those reads. Prepare each batch from these final pinned sources. These operator commands were not run. CPU tests did exercise local preparation.
```bash
cd /scratch/jjyeung/orch_n30/cont_ops/work/d0/readk
export PYTHONDONTWRITEBYTECODE=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
L=$PWD/kit/launcher/orchard_launcher.py
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
STEP=100
TOKEN=a$("$PY" -B -c 'import secrets; print(secrets.token_hex(5))')
DEST=$PWD/kit/build/$TOKEN
"$PY" -B "$L" prepare --step "$STEP" --token "$TOKEN" --destination "$DEST"
CMD=$("$PY" -B "$L" submit-command --destination "$DEST")
timeout 300 bash "$OSSH" "$CMD" < "$DEST/BATCH.sh" > "$DEST/SUBMIT.out" 2> "$DEST/SUBMIT.err"
"$PY" -B "$L" record-submission --destination "$DEST"
```
The generated command performs test-only admission then submits the same stdin batch: one GPU, 16 CPUs, 200G, `general`, six hours, no requeue, name `a15_cot_ap<hex>`. Submit only when the final `.done` receipt exists; this job does not wait on an idle GPU. Use the inherited `fetch --destination "$DEST"` after completion; transfers ≥20 MB require its printed governor procedure.

Compute the metrics from extracted return files:
```bash
"$PY" -B f1f2.py --step 100 --a evidence/A544.jsonl --b /PATH/100/ITEMS.jsonl --output F100.json
"$PY" -B f1f2.py --step 200 --a evidence/A544.jsonl --b /PATH/200/ITEMS.jsonl --m100 /PATH/100/ITEMS.jsonl --output F200.json
"$PY" -B f1f2.py --step 400 --a evidence/A544.jsonl --b /PATH/400/ITEMS.jsonl --output F400.json
"$PY" -B -m unittest discover -s tests -p 'test_*.py' -v
```

Job 169526 measured 52m51s for main+away+forward including binding/layout/merge (47m11s generation), from [STEPS.jsonl](/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/STEPS.jsonl), 14:42:05–15:34:56Z. Its [STAGING.json](/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/metadata/STAGING.json) measured 323.8s to transfer 21.583 GB and 173.8s for other staging. At the supplied 121 MB/s, the same transfer would take 178s. Allow roughly 60–70 minutes total for one default read; repeated full hashing and per-family frame pulls are additional uncertainty. Camera added 12m13s in that packet. These are projections, not milestone measurements.

Budget about 220 GB of additional `/tmp` space for retained archives, extracted runtimes/base/export, three family model copies, frame tar/PNG copies, and working space; about 265 GB with camera. Keep the 200 GiB floor: start with at least 440 GB free (490 GB with camera). These are conservative estimates using the accepted 21.583 GB export; admission and each family check actual space.

Validation: 40 CPU tests pass (`evidence/FIX1_TESTS.log`), including packaged bootstrap entry at all three steps, journal archive round trips, strict receipt format/identity, seven-type F1, both F2 readings, step-400 decisions and final pin checks. Eight guarded binds match accepted prompt inventories: all four families at 100, main at 200, and main/away/forward at 400 (`evidence/FIX1_BIND_*.log`). Every test entry installs an audit hook that denies real process creation and socket operations; publish, GPU and cloud paths are mocked. `DIFF.md` classifies changed lines; `REVIEW.md` and `FIX1.md` map each requested fix to code and tests. Uploader source evidence is in `evidence/UPLOADER_FORMAT.txt`; the real receipt sample is in `evidence/DONE_SAMPLES.txt`.

Unverified: live Orchard credentials/assets, final milestone receipts, H100/vLLM execution, actual PNG pixels, returns, and real milestone timing. Camera uses build_t5's reconstructed bridge. New job-facing names are opaque and engine diagnostics are hex-encoded; the unchanged reader/checker still require legacy private paths such as `a0/models/cp1m200`. A literal ban on every private Orchard path remains unresolved and prevents claiming unconditional submit readiness. No SSH, GPU, network, Git, deletion, or Slurm command ran.
