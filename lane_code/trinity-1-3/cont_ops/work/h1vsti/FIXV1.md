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

All suites, real-RGB runtime fixtures and 106 legacy plan comparisons pass. The Validation section below records counts, log paths and this fork's final seal. Validation required no code changes.

The operator commands below were not executed. All working paths point into h1vsti. The commands use FIX6's approved `ossh.sh` transport directly; `tools/operator_transport.sh` only forwards to that same script and is not required. Use the uploaded question file, the pinned existing frame archive, completed export receipts and an authorized allocation.

```bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1vsti
export PYTHONDONTWRITEBYTECODE=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
L=$PWD/kit/launcher/orchard_launcher.py
export A_TRANSPORT=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh

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

## Validation

Completed 2026-11-18 10:17:38Z, before the 11:05Z deadline. Every suite listed in REPORT.md passes under `/scratch/jjyeung/envs/p1cpu/bin/python`. Fixture writes remain under `evidence/test_*`; h1read and the packets remain read-only.

| Suite or check | Passed | Failed | Log under evidence/ |
|---|---:|---:|---|
| R6 admission, population, capture, summary and legacy matrix | 9 | 0 | `evidence/FIXV1_NEW_TESTS.log` |
| FIX6 regressions | 7 | 0 | `evidence/FIXV1_FIX6_TESTS.log` |
| FIX5 regressions | 6 | 0 | `evidence/FIXV1_FIX5_TESTS.log` |
| FIX4 regressions | 10 | 0 | `evidence/FIXV1_FIX4_TESTS.log` |
| Step-544 admission | 7 | 0 | `evidence/FIXV1_TARGETED.log` |
| Real-RGB unfiltered a7 runtime | 4 items | 0 | `evidence/FIXV1_RUNTIME.log` |
| Real-RGB direct-filter a7 runtime | 3 items | 0 | `evidence/FIXV1_RUNTIME_DIRECT.log` |
| Real-RGB r6 runtime | 6 items | 0 | `evidence/FIXV1_RUNTIME_R6.log` |
| Full candidate | 133 | 0 | `evidence/FIXV1_TESTS.log` |
| Ported readk | 53 | 0 | `evidence/FIXV1_READK_PORTED.log` |
| Original readk reference | 53 | 0 | `evidence/FIXV1_READK_REFERENCE.log` |
| Reviewer refute | 4 | 0 | `evidence/FIXV1_REFUTE.log` |
| Legacy plan comparisons (included in r6 suite) | 106 plans | 0 | `evidence/FIXV1_NEW_TESTS.log` (`R6_LEGACY_PLANS`) |
| Final pin test | 1 | 0 | `evidence/FIXV1_FINAL_PIN_TEST.log` |
| SHA256 manifest | 250 files | 0 | `evidence/FIXV1_SHA256_CHECK.log` |
| Operator shell syntax (`bash -n`) | 1 | 0 | `evidence/FIXV2_OPERATOR_CHECK.log` (empty on success) |

The legacy matrix compares serialized plan bytes and `plan_sha256` against authenticated h1read fix 6: 8 cases for `359fcc3c`, 32 for `17c4ffa4`, 2 for `469ddece`, 32 for `673bc60f`, and 32 for `05b8ac69`. It covers main and a7 separately wherever admitted, both filters, every registered milestone, and both endpoints of each admitted stop-generation range. Step 544 admits a7 only among the legacy families. The reference FINAL_PINS SHA256 is `7891b795c3d0600ac2e45689c13ccf200756cfc450581ca485fff2105abb488b`. `evidence/FIXV1_AUDIT.json` retains every case, suite count, log digest and fixture path. CONFIG integrity pins authenticate the fork and are not claimed byte-identical.

Both r6 identities prepare successfully with and without the direct filter, retaining 900 items and 150 per type. Unregistered combinations refuse. The source-preservation and synthetic-summary tests pass, including the byte-identical capture pin. The six-item r6 runtime covers every type with real RGB frames and the actual worker, evaluator, budget derivation and mergers. Engine, model staging and parity probes are mocked; these results establish offline execution, not live GPU parity or production accuracy.

No suite failed, and no code fix was necessary. All 122 files in the recorded kit/tools/tests inventory retain their V2 entry hashes. The requested command corrections are at `FIXV1.md:57` (Python), `FIXV1.md:59` (transport), `REPORT.md:23` (validation Python), and `evidence/FIXV1_OPERATOR_COMMANDS.sh:4,6`. The transport uses FIX6's `ossh.sh` directly; the local forwarding wrapper is not required. Operator commands were syntax-checked but not executed.

Two execution-helper errors and their causes are recorded in `evidence/FIXV2_EXECUTION_NOTES.log`: the sandbox refused tmux's socket, and system Python lacked `str.removeprefix` in a report helper. The attached session and the required Python interpreter completed the work. No cluster-killed job was retried.

This fork's final seal is:

- `evidence/FINAL_PINS.json` SHA256: `272da0e4c86528fd07db88a8da90c59009b2d494fa5f29e2eed8ec93598e28a1`.
- `SHA256SUMS.txt` SHA256: `dff33822d81da6f0882516229e733df69fd43d0b139365b59c965bf53d545284`.

`evidence/FIXV1_PRESEAL.log` and `evidence/FIXV1_SEAL.log` record sealing; `evidence/FIXV2_RUN.log` records suite execution times. The final pin test and all 250 checksum entries pass. FIXV1.md and post-seal verification logs stay outside the manifest to avoid circular hashes.
