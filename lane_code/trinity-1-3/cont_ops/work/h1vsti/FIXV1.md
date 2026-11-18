# Separate r6 reads

The fork admits opaque family `r6` alone for `469ddece`, generation `mstop`, step 544, and `673bc60f`, milestone 200. It refuses r6 on other runs, steps, generations, or mixed-family requests. Other family/run admissions retain their existing behavior. Main+a7 decision reads remain on h1read.

All **900 items** execute: **150 per type**, across **68 rooms**. The commands below use **no `--types` filter**. The optional `--types direct` excludes none of these six types and also executes all 900. Both preparations record the exact count and type population in their hashed plans.

| Changed file:line | Behavior |
|---|---|
| `kit/launcher/orchard_launcher.py:149` | Close r6 admission to the two identities; preserve legacy gates. |
| `kit/launcher/orchard_launcher.py:193` | Authenticate the new registry and exact population against the plan. |
| `kit/launcher/orchard_launcher.py:234` | Package r6/c6, bind the registry digest, and record 900 items with six 150-item counts. |
| `kit/launcher/R6.json:1` | Pin the question file, existing archive inventory, required frames and capture bytes. |
| `kit/reader/worker.py:70` | Dispatch r6 into the shared a7 asset reader in a fresh process. |
| `kit/reader/x7.py:53` | Accept a question filename and population validator while preserving archive validation. |
| `kit/reader/x7.py:111` | Use the same reader, evaluator, frame loader, decoding, arm and mergers for r6. |
| `kit/reader/x7.py:138` | Register the six task names as MC types inside the r6 child. Evaluator source and functions are unchanged. |
| `kit/reader/r6.py:17` | Check the capture SHA256, validate the 900-item population, and emit binary scores and trace flags. |
| `kit/reader/chain.py:57` | Report per-type constants and capture rates for r6. |
| `kit/launcher/orchard_job.py:137` | Mount the existing asset directory read-only for r6. |
| `kit/launcher/chain_save.py:84` | Retain r6 compact rows, request/binding evidence and raw merged journals. |
| `tools/build_r6.py:24` | Reproduce the opaque question asset from pinned sources; prove all frame references match a7. |
| `tools/item_ids.py:27` | Decode r6 item and physical-room identities locally during unpacking. |
| `vsti_summary.py:18` | Validate complete returns and calculate accuracy, capture rates, paired intervals and the gate. |
| `tests/test_fixv1.py:1` | Cover admission, source preservation, capture, chain output, summaries and legacy plan equality. |
| `tests/runtime_fixture.py:22` | Exercise all six r6 types through the real evaluator and budget mergers with a synthetic engine. |
| `tests/test_fix4.py:148`, `tests/test_fix5.py:54`, `tests/test_fix6.py:125` | Read retained fixtures from h1read; explicitly account for the three changed reader adapters and two new modules. |
| `tools/test_fix3.py:19`, `tools/seal.py:13` | Add fork suites and sealing inventory while keeping fixture writes under `evidence/test_*`. |

The prompt path is the same as a7 MC items. `kit/reader/evaluator/parity.py:16` calls `evalpath.official.build_prompt_context(task, 'ours')`; `kit/reader/evaluator/evalpath/official.py:34` concatenates the original question, one newline, the original labeled options on separate lines, two newlines, and the unchanged answer-format instruction. That instruction asks the model to think and finish with the option letter alone on the final line (`official.py:13`). No task-specific prompt text is added. `x7.py` also records per-item prompt hashes before generation.

The reader uses the accepted direct arm, 32 f32 anchors duplicated consecutively into 64 processor frames, greedy decoding, thinking enabled, ON16k generation, and the existing B2048/B4096 continuation policy. B2048 is the primary score. The 64-token cap applies to continuation answers; early closed ON answers retain the accepted reuse policy. The evaluator digest, direct wrapper, export checker, source functions and native prompt/pixel guards remain unchanged. Engine, max-model length, max sequences and inflight remain 0.32.0, 49,152, 32 and 16.

Each `r6/ITEMS.jsonl` record contains `id`, `room`, `task_type`, `predicted_letter`, `gold_letter`, binary `score`, and `template_capture`, plus step/budget provenance and a trace digest. Invalid or unparsed predictions use JSON null for the predicted letter. The inherited a7 refusal, parse-failure and token-cap policy still scores zero. `template_capture` equals the pinned `flag(trace)` on the authenticated B2048 scoring trace: `scoring_text` for a forced continuation, otherwise `raw_generation`. It includes generated thinking and the final answer, without the question/options. It does not flag an unused ON16k suffix beyond the B2048 prefix.

The capture implementation is copied byte-identically to `kit/reader/c6.py`, SHA256 **`bbc735c3daf0fe8a7126883cb955097a1e52a2dcc738a19b902cb8e8c120c87b`**. The launcher payload and r6 registry pin it, and the reader verifies it before staging.

`vsti_summary.py` prints accuracy with n, constants **25.3/33.3/50/50/50/50**, pooled accuracy, overall/per-type capture rates, and SHA256 of the exact `r6/ITEMS.jsonl` it reads. It accepts opaque or locally decoded item identities and rejects partial, missing, duplicate, mismatched or unregistered returns. `--base` requires R1 m200 minus baseline mstop/544. Each interval uses **10,000** paired, item-weighted draws of whole physical rooms with replacement, **seed 20261118**, and linearly interpolated percentile endpoints. Each type resamples rooms containing that type; the pooled estimate resamples all 68 rooms. A type is marked when its upper endpoint is strictly below zero. The gate passes only when the pooled point difference is positive and no type is marked.

The source schema has `dataset` and `scene`, without a `room` key. The uploaded item adapter writes the corresponding physical-room identity into `room`; local unpacking decodes it to `dataset/scene`. The summary uses this item field for clustering.

`UPLOAD_PLAN_V1.md` specifies the only new upload:

| Local file | Bytes | SHA256 | Orchard destination |
|---|---:|---|---|
| `assets/b62c14e9.jsonl` | 2,375,536 | `ef9b1c45f3cb3da84c108748b2e2ae7830ceeac5a0114b7cb52c44fab76fd58e` | `/project/community/jjyeung/okh7/af83c921/b62c14e9.jsonl` |

R6 reuses a7's `d81f4a26.tar` at its existing staged destination. All 2,176 required frame members match by SHA256, covering 564,411,344 bytes. Missing frames and additional frame bytes are both **zero**. The source item, reader-layout and capture pins appear in the upload plan and `evidence/FIXV1_ASSETS.json`. The local ID map and summary tool never enter the Orchard package.

Validation currently passes the eight small r6 tests and seven step-544 tests. Full suites, real-RGB runtime fixtures, legacy matrix and resealing await the requested heavy-I/O authorization. The pending request follows the supplied Trinity rule, “Ask before any heavy IO command”; the full gate repeatedly reads the 798 MB local archive. No test failure or cluster kill caused this pause. The inherited FINAL_PINS/SHA256SUMS do not authenticate the edited fork; resealing remains required before submission.

The operator commands below were not executed. All working paths point into h1vsti. `tools/operator_transport.sh` is a local entry point for the existing approved site transport; it is not packaged for Orchard. Use the uploaded question file, the pinned existing frame archive, completed export receipts and an authorized allocation.

```bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1vsti
export PYTHONDONTWRITEBYTECODE=1
PY=python3
L=$PWD/kit/launcher/orchard_launcher.py
export A_TRANSPORT=$PWD/tools/operator_transport.sh

TOKEN_544=a$("$PY" -B -c 'import secrets; print(secrets.token_hex(5))')
STEP544=$PWD/kit/build/$TOKEN_544
"$PY" -B "$L" prepare --run 469ddece --namespace 8865619b \
  --step 544 --generation mstop --families r6 \
  --token "$TOKEN_544" --destination "$STEP544"

TOKEN_200=a$("$PY" -B -c 'import secrets; print(secrets.token_hex(5))')
R1_200=$PWD/kit/build/$TOKEN_200
"$PY" -B "$L" prepare --run 673bc60f --namespace 8865619b \
  --step 200 --families r6 \
  --token "$TOKEN_200" --destination "$R1_200"

submit_read() {
  local dest=$1 cmd
  cmd=$("$PY" -B "$L" submit-command --destination "$dest") || return
  timeout 300 bash "$A_TRANSPORT" "$cmd" < "$dest/BATCH.sh" \
    > "$dest/SUBMIT.out" 2> "$dest/SUBMIT.err" || return
  "$PY" -B "$L" record-submission --destination "$dest"
}
```

Execute each submission once, separately, when its export and allocation are ready:

```bash
submit_read "$STEP544"
submit_read "$R1_200"
```

After each job ends, retain its original destination and token. Restore those variables in a new shell; do not prepare a new token for fetch.

```bash
"$PY" -B "$L" fetch --destination "$STEP544"
"$PY" -B "$L" fetch --destination "$R1_200"
# For a return >=20 MB, fetch saves EXIT.json and prints the exact transfer
# command. Register that stream with the IO governor and execute it once.
"$PY" -B "$PWD/tools/unpack_return.py" --destination "$STEP544"
"$PY" -B "$PWD/tools/unpack_return.py" --destination "$R1_200"
"$PY" -B "$PWD/vsti_summary.py" --read "$STEP544/fetched/x"
"$PY" -B "$PWD/vsti_summary.py" --read "$R1_200/fetched/x" \
  --base "$STEP544/fetched/x"
```

Orchard job 171197 recorded **768.974 seconds** for **1,781 a7 items**, with about **17 minutes total wall time** (`../h1read/kit/build/adff67f7ae9/fetched/x/SUMMARY.json:104`). Scaling its chain time gives `769 × 900 / 1781 ≈ 389 seconds`. Adding the observed approximately 251 seconds of overhead gives **about 640 seconds, or 11 minutes per read**. Allow **15–20 minutes per read** for prompt-length and continuation differences; this is an extrapolation. The six-hour allocation remains unchanged.

No network, SSH, Slurm, GPU, Git, deletion, production preparation or submission was performed. All writes and test fixtures stay within h1vsti. h1read and the two source packets remain read-only.
