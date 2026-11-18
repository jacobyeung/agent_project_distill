# Direct type filter and partial returns

`prepare --types direct` excludes `object_abs_distance` and `room_size_estimation` from generation in every selected family. The CONFIG, hashed plan, returned SPEC and SUMMARY identify the selection. A7 retains 1,781 items: counting 385, size 293, direction easy/medium/hard 192/194/192, appearance order 246 and relative distance 279. The summary records the excluded populations as 290 and 98 items, without scores. Coverage counts rooms with kept items; the registered A7 denominator remains 100.

Full source membership, source hashes, protocol, export, adapter, asset, binding, frame, parity and budget checks remain required. Selection follows full-population validation. Generation, both mergers and the report use the same kept task provider. Main, away and forward retain full-population frame staging and validation, including excluded items. Completion additionally requires exact kept IDs. A filter that empties a family refuses before creating its preparation directory. The evaluator, direct wrapper, adapters, scoring and export-checker source bytes remain unchanged.

Unfiltered preparation reproduces the retained FIX3 plan bytes and `plan_sha256` exactly. Every CONFIG field except the five integrity fields also matches: `payload_pins`, `payload_sha256`, `launcher_pins`, `launcher_review`, and `launcher_review_pin` change because they authenticate changed source. **Whole-CONFIG byte identity is not satisfied:** retaining the old pins would invalidate the new code or require packaging the old implementation. No admission check was bypassed to manufacture equality. The regression test names this exception explicitly and compares against the existing FIX3 fixture.

On SIGTERM, SIGINT, SIGUSR1, a chain failure or an exception, the job packs journals before publishing. The archive contains `PARTIAL.json` and `SUMMARY.json` with `complete: false`, per-family finished counts, per-type counts, and per-journal retained counts. Counts use unique completed IDs in the ON16k journal, with merged ON16k rows as a fallback; budget arms are reported separately rather than added together. These counts do not claim completed B2048 scoring. Available `g0.jsonl`, `items_a0.jsonl`, summaries and binding/asset evidence are retained within the cap. Partial summaries identify all raw scores as provisional. Malformed or torn journals retain only their valid prefix; a cancellation during a summary write does not prevent journal recovery.

The packer reserves space for metadata and compression overhead, then retains whole-line prefixes under a conservative raw-byte budget. This can truncate earlier than a compression-dependent budget would. Both source and retained counts, omitted files, malformed summaries and truncation flags remain visible. Production archives stay below 89.9 MB; proof archives stay below 19.9 MB. Fetch reports PARTIAL, including when it requests registration of a large transfer. Unpack authenticates the archive and prints that scores are not final. The default final-result verifier continues to reject partial reads.

The synthetic 1,958-line journal contains 54,953,745 bytes of deterministic, high-entropy generation text. Packing took **1.586 seconds**, including scanning, compression and fsync, and produced a 32,016,104-byte archive without losing a line. `evidence/FIX4_TESTS.log` records the measurement. The fixture also exercises the real 19.9 MB proof cap, retains all 1,958 finished-item counts, and truncates returned lines cleanly.

Shutdown waits at most two seconds before killing the child group, then at most one second to reap. Partial publishing gives the pool eight seconds and shares a 15-second deadline across the pool and GCS fallback, with one additional second for a receipt. A verified pool return ends the transfer. Failed jobs skip the optional final GPU observation and final proof-trace upload. A late signal during final GPU observation or normal publishing switches to the partial path. Repeated allocation signals cannot interrupt partial packing or transfer. Regression tests exercise both late paths and a publishing exception. With the measured packing time, the configured waits leave room inside a 30-second kill-wait on a responsive local filesystem. **The actual Slurm KillWait and remote transfer performance were not measured:** no network or Slurm command was permitted. This is an offline packing measurement and bounded-transfer implementation, not a demonstrated live cancellation return. A stalled filesystem, unavailable return channels, or an earlier SIGKILL can still prevent delivery.

The changes are classified as BEYOND in `evidence/INTENDED_PORTS.md`, which the sealer includes in DIFF.md. The classifications cover the explicit population, provisional recovery format, bounded shutdown/transfer and separate partial verifier. `evidence/FIX4_AUDIT.json` lists the eight changed, previously pinned kit files. The shared filter is new; `kit/reader/read_filter.py` links locally to the launcher source and preparation packages its bytes as a regular reader file.

| File and lines | Change |
|---|---|
| `kit/launcher/orchard_launcher.py:149,192,316,423` | Validate/filter identity, refuse empty populations, package the shared selector and report partial fetches. |
| `kit/launcher/read_filter.py:9,16,23,33` | Closed direct preset, population counts and one validated provider for worker/merger/report imports. |
| `kit/reader/worker.py:70` | Select after the unchanged full bind/validation, retain binding and parity checks, require exact kept IDs. |
| `kit/reader/x7.py:110` | Select after full asset validation; bind the filter and report the kept population. |
| `kit/reader/chain.py:46` | Report excluded counts and coverage of kept rooms; keep registered room coverage. |
| `kit/launcher/chain_save.py:99` | Pack bounded partial journals, count finished/retained records and tolerate torn summaries. |
| `kit/launcher/orchard_job.py:157,167,192,292` | Bound child shutdown, protect finalization from late signals and pack before publish. |
| `kit/launcher/orchard_results.py:34,70,106,184` | Bound partial transfers, authenticate the partial marker and preserve strict final-result verification. |
| `kit/launcher/trace_runtime.py:94` | Upload the final proof trace only for a complete return. |
| `tools/unpack_return.py:20` | Authenticate and label a partial return. |
| `tests/test_fix4.py`, `tests/runtime_fixture.py`, `tools/test_fix3.py` | Add ten regression tests and a filtered actual-worker/budget/merger fixture; retain the original suites. |
| `tools/seal.py`, `REPORT.md`, `evidence/INTENDED_PORTS.md` | Record current behavior and seal the source and validation evidence. |

The operator commands below were not executed. They use the pinned assets and permissions in UPLOAD_PLAN.md. Run them from this kit with an authorized allocation and a fresh token.

```bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1read
export PYTHONDONTWRITEBYTECODE=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
L=$PWD/kit/launcher/orchard_launcher.py
export A_TRANSPORT=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
TOKEN=a$("$PY" -B -c 'import secrets; print(secrets.token_hex(5))')
STEP544=$PWD/kit/build/$TOKEN
"$PY" -B "$L" prepare --run 469ddece --namespace 8865619b \
  --step 544 --generation mstop --families a7 --types direct \
  --token "$TOKEN" --destination "$STEP544"

CMD=$("$PY" -B "$L" submit-command --destination "$STEP544")
timeout 300 bash "$A_TRANSPORT" "$CMD" < "$STEP544/BATCH.sh" \
  > "$STEP544/SUBMIT.out" 2> "$STEP544/SUBMIT.err"
"$PY" -B "$L" record-submission --destination "$STEP544"
```

After the job ends, use the same destination. If using a new shell, restore `STEP544` to the directory printed/created above; do not generate another token for fetch.

```bash
"$PY" -B "$L" fetch --destination "$STEP544"
# For an archive >=20 MB, fetch retains EXIT.json and prints the exact transfer
# command. Register that stream with the IO governor and execute it once.
"$PY" -B tools/unpack_return.py --destination "$STEP544"
```

The supplied rates imply `385 × 6 s + 1,396 × 1 s = 3,706 item-seconds`. The accepted reader permits 16 concurrent items, so the rate-only wall-time estimate is `3,706 / 16 + 480 = 712 seconds`, or **about 12 minutes including staging**, at sustained full concurrency. Frame loading, prompt preparation, parity probes, budget continuations and merging add time; the journal generation timer does not cover all of them. At eight effective concurrent items the same calculation gives about 16 minutes. The serial calculation is approximately 70 minutes. These are estimates from the supplied rates, not measured filtered production runtimes; retain the existing six-hour allocation limit.

All work stayed inside this kit. Tests wrote fixtures only under `evidence/test_*`; logs are retained validation evidence. No production preparation, production receipt, reference source, network, SSH, Slurm, GPU, Git or deletion operation was performed. FIX4.md and post-seal verification logs remain outside the manifest to avoid circular hashes.

| Validation | Result | Evidence |
|---|---|---|
| Candidate suite | 111/111 pass | `evidence/FIX4_TESTS.log` |
| New FIX4 regression suite | 10/10 pass | `evidence/FIX4_NEW_TESTS.log` |
| Step-544 admission suite | 7/7 pass | `evidence/FIX4_TARGETED.log` |
| Ported readk suite | 53/53 pass | `evidence/FIX4_READK_PORTED.log` |
| Original readk reference suite | 53/53 pass | `evidence/FIX4_READK_REFERENCE.log` |
| Reviewer refute suite | 4/4 pass | `evidence/FIX4_REFUTE.log` |
| Unfiltered runtime | 4 items pass | `evidence/FIX4_RUNTIME.log` |
| Direct runtime | 3 kept items pass | `evidence/FIX4_RUNTIME_DIRECT.log` |

The reproducible validation commands are in REPORT.md. All original suites remain in the gate. The fixture benchmark and signal paths use CPU-only synthetic journals; remote pool/GCS operations are mocks.

The final manifest test passes, and all 190 checksum entries verify. Evidence: `evidence/FIX4_FINAL_PIN_TEST.log`, `evidence/FIX4_SHA256_CHECK.log` and `evidence/FIX4_SEAL.log`.

- FINAL_PINS SHA256: `33e62c60cd055d255bd0ce8c2fd7680037a276fb90642737c882c3e1d8e83531`.
- SHA256SUMS.txt SHA256: `994f660c7fb8be0c72e8f53a2ad72760298dfe2ccbfa17034f01309b29178e65`.
