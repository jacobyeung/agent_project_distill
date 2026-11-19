Both switches OFF on N's first launch. ON from the next launch only after one production launch shows parity on real stores. Synthetic fixture parity does not satisfy this adoption gate. Keep either switch OFF while its production parity evidence is missing.

Apply the independent patches to a fresh build-21 tree, base seal `b262e7a7`, and rebuild the authenticated source archive, tree/configuration seals, executable inventory, scan certificate and kit through N's normal process. Never reuse the input seal for changed source. The manifest records patch hashes and every base/patched file hash.

```bash
patch --batch --fuzz=0 --no-backup-if-mismatch -p1 < /scratch/jjyeung/orch_n30/so_modep/out/patches/01_fast_paths.diff
patch --batch --fuzz=0 --no-backup-if-mismatch -p1 < /scratch/jjyeung/orch_n30/so_modep/out/patches/02_selected_sql.diff
```

`S1_PREP_FAST_PATHS=1` enables equivalent lexical path arithmetic and a bounded cache of parsed mapping text. It caches no resolved path, file status or hash. `S1_PREP_SELECT_SQL=1` enables ordered sparse SQLite queries, at most 256 keys each; dense prefixes retain the native full scan. Unset, `0`, and every value other than `1` leave each switch OFF. Every pin hash, filesystem check, selection rule and refusal remains active.

Both switches have process-wide scope. The training and resume legs inherit them: `launch_s1/b/r.sh:29-40` starts mode p as a child, then continues with the same environment. Patch 01 can therefore affect training-time `resolve_read`, and patch 02 can affect prepared-store validation outside mode p. This delivery proves CPU preparation parity; it does not prove full production training behavior.

Set the switches in the generated `<kit>/b/r.sh`, immediately after `export PATH=/usr/local/bin:/usr/bin:/bin` (input line 4), before `export TK_JOB_START`. Its source template is `launch_s1/b/r.sh`. Use these exact two lines for N's first launch:

```bash
export S1_PREP_FAST_PATHS=0
export S1_PREP_SELECT_SQL=0
```

Only after the real-store parity gate passes may the next launch change each approved line to `export S1_PREP_FAST_PATHS=1` / `export S1_PREP_SELECT_SQL=1`. Regenerate the kit's inventory and content-scan certificate after any shell edit; do not edit an authenticated deployed kit in place. The switch names pass the build-21 naming scanner.

The operator must record both values beside the job ID in `<kit>/o/modep_switches.jsonl`, the launch ledger. Each row must contain `job_id`, `S1_PREP_FAST_PATHS`, `S1_PREP_SELECT_SQL`, the rebuilt source seal, worker Python version, UTC time, and paths to the OFF baseline and real-store parity evidence. Existing native receipts do not record these switches. Keep the ledger outside the authenticated admission output directory.

The first production launch must publish its native OFF outputs. Before enabling either switch for a later launch, the orchestrator must validate OFF/ON parity against that launch's actual retained stores and physical frames in an isolated shadow check. The shadow check may enable a switch inside its comparison process; the first production job's launch environment remains OFF. The check must preserve source bytes, selections, physical paths, rebuilt code and request identity. It must exercise the enabled functions and compare full ordered row payloads, not merely final index counts. A second OFF run or synthetic fixture alone is insufficient. This lane has not run the shadow check or authorized extra production preparation.

Compare all mode-p files, including these named files beneath the native admission directory (UUID components vary):

- `prepare_<uuid>/pointing/rows.sqlite`, `vqa/rows.sqlite`, `routing/rows.sqlite`, and `composed/rows.sqlite`, together with each adjacent `receipt.json`.
- `prepare_<uuid>/prepared/vqa_indices.json`, `vqa_scene_indices.json`, `pointing_scene_indices.json`, `routing_scene_indices.json`, `pose_mix_order.json`, `pose_scene_order.json`, `receipt.json`, and `s1_receipt.json`.
- `prepare_<uuid>/config.json`, `handover.json`, `parent_grounding.json`, `result.json`, routing materialization/pool files, and composed membership/intake files.
- `frames_<uuid>/frame_inventory.sqlite`, `frames.json`, and `result.json`: compare inventory bytes, per-source rows/reference/unique counts, and every fixed-sample path and hash.
- `request.json`, `data_receipt.json`, `phase_prepare.complete.json`, `phase_frames.complete.json`, and their UUID publication copies.

`out/tests/review1_file_parity.json` lists every fixture filename and digest as a checklist; production may add files. Compare the complete production file set. For exact byte comparison, the isolated check must replay the same paths and identities as the baseline without overwriting production outputs. Fix only the native telemetry `resources.seconds` and `resources.peak_rss_kib` in the comparison harness, as the delivered CPU harness does. Dependent hashes must be recomputed by native publication, not discarded by the comparator. If the orchestrator cannot preserve identities or account for an authenticated difference, parity remains unproved and the switches remain OFF.

Read native phase timing through `phase_prepare.complete.json` and `phase_frames.complete.json` into their `result.json` payloads; `data_receipt.json` also exposes `phase_resources.frames.seconds`. Use `work/measure_modep.py` on the OFF launch's admission directory:

```bash
nice -n 10 <native-python> -I -s -B /path/to/measure_modep.py <OFF-admission-directory> --launch-utc <UTC> --exit-utc <UTC>
```

The helper reports `estimated_path_saving_seconds = 0.264 * OFF phase_resources.frames.seconds`. This is a fixture extrapolation, not a measured saving. Planning bound: **≤18.5 min, estimated (possibly 0)**. The 40–70 minute path-heavy share is unmeasured, and warm 256-byte local files do not reproduce Orchard storage latency. Patch 02 contributes zero additional minutes to the estimate. On a later approved ON launch, compare actual frame seconds per reference, matched preparation time, the post-prepare residual, and total mode-p time against the OFF baseline. Do not count the estimate as an observed reduction or add overlapping phase estimates.

Any byte, row-order, count, sample, pin or refusal mismatch blocks adoption. A latency regression returns the affected switch to OFF. Preserve failed artifacts. Never relaunch a cluster-killed job automatically.

## Review round 1: finding -> fix -> test

| Finding | Fix | Regression and deliberately broken variant |
|---|---|---|
| 1 MEDIUM: sparse chunks lacked ordered parity | Select 820 of 4,096 rows; four chunks per pass, table and view; compare full ordered events and native inventory bytes | `test_multichunk_sparse_events_and_order_sensitive_output` and `test_multichunk_frame_inventory_bytes_are_order_sensitive` pass. Reversing chunk traversal fails both; reversing rows fails the ordered test. |
| 2 LOW: no positive path proof; degenerate frames | Count both fast helpers; assert zero calls OFF and positive calls ON; use 32 physical frames per native source | `test_switch_reaches_fast_resolver_only_when_on`, the sparse spy assertions, and `work/native_parity.py` pass. Ignoring either ON switch fails its test; the one-frame fixture fails the native harness. |
| 3 LOW: parser source spelling | Reuse `mapping.__getattribute__("sp" "lit")` | `test_mapping_parser_preserves_source_spelling` passes; restoring the literal attribute spelling fails it. |
| 4 LOW: savings claim exceeded evidence | State the bounded estimate and compute it from OFF frame telemetry | `work/test_review_contracts.py` checks the claim, arithmetic and helper output; an inflated headline and changed multiplier each fail. |
| 5 LOW: scope/provenance undocumented | Name process-wide inheritance, the exact kit lines and the per-job ledger | The document contracts pass; removing scope, a switch line, or the ledger requirement fails. |

Run `work/validate_matrix.py` with `work/env.sh` to include the new tests in all four configurations; N's focused list alone does not include them. `TMPDIR` must point to retained scratch fixtures. `work/run_gloo.sh` remains a socket-enabled lane follow-up; it checks CPU inventory digests across ranks, not a distributed fast path. Production real-store parity, production timing and H100 training remain outstanding.
