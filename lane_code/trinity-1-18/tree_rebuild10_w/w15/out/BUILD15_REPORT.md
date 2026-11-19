# Build 15

**A, C and C′ admit. N must keep opener rows when initialized from P’s export. GO=false remains.** The requested comparator and CPU witness proofs pass. The broader qualification remains partial because external inputs are absent and the packet generator has an exact floating-point serialization mismatch. Sources: `work/build15/proofs/real/RESULT.json`, `work/build15/proofs/final_focused/TESTS.json`, `work/build15/proofs/final/packet/results.json`, `work/build15/SUITE_RUNS.json`.

## Handover and witness

`routing_opener_init` describes each run’s own initialization boundary. P’s recorded value does not constrain N. N must use `keep`; explicit `reset` and omission with a P export refuse with `P_EXPORT_ROUTING_OPENER_KEEP_REQUIRED:routing_opener_init`. The comparator, native preparation, native opener initializer and continuation reader exercise this refusal. The parent initialization path retains its existing behavior. Sources: `work/tree_r1/student_pilot/r1_handover.py`, `work/tree_r1/student_pilot/r2_openers.py`, `work/build15/proofs/final_focused/n1fix/b15_witness/RESULT.json`.

The operator supplies **`v.json`, produced by `launch_r1.p_opener_witness`**, as an exact path/SHA-256 pin in N’s `routing_vocabulary`. The producer authenticates P’s run and handover receipt closure, verifies P’s pinned parent artifact, and reconstructs P’s vocabulary from its authenticated preparation/model manifest and pinned tokenizer metadata using the native `processor_for_receipt` token setup. This supports the legacy P exporter, which records neither `routing_vocabulary` nor `r2_identity`. An optional vocabulary declaration in a newer export must agree. The witness binds `artifact_sha256` to P’s export, `lineage_sha256` to the step-544 parent, and records the vocabulary digest, opener IDs and constituent IDs. Sources: `work/tree_r1/launch_r1/p_opener_witness.py`, `work/base/tree_b01ce449/student_pilot/carrier_c1_run.py`, `work/build15/proofs/witness_edges/RESULT.json`.

Generate the witness after P’s export and handover receipt exist. Then set N’s `routing_vocabulary` pin and produce N’s continuation identity and handover mapping. N’s unchanged preparation reader validates the artifact/lineage binding; its initializer compares the live vocabulary and preserves the input and output opener rows. The producer requires P’s actual preparation and tokenizer files; it does not use N’s tokenizer as evidence for P. Sources: `work/tree_r1/launch_r1/p_opener_witness.py`, `work/tree_r1/student_pilot/r2_openers.py`.

```bash
# Run in the authenticated operator environment with the sealed tree on PYTHONPATH.
python -m launch_r1.p_opener_witness --config /path/to/n.json --output /path/to/v.json
```

The CPU proof runs the legacy native checkpoint/export, handover receipt producer, witness producer, LM artifact loader, preparation reader and opener initializer. A tiny native CPU model and local tokenizer replace pretrained GPU assets; local collectives replace distributed publication. Both opener embedding rows remain equal after loading and keeping. Wrong artifact, lineage, vocabulary, token IDs, missing witness and N reset refuse. No real P export weights or production tokenizer were supplied or inspected. Sources: `work/build15/proofs/final_focused/n1fix/b15_witness/RESULT.json`, `work/build15/proofs/witness_edges/RESULT.json`.

## Real configurations

| Config | Computed tree configuration identity | Result |
|---|---|---|
| A | `fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f` | ADMIT |
| C | `6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74` | ADMIT |
| Cprime | `774503e26f274a10c96ad06210d339c49ebc9a704ac254df81f389b0da4d98a1` | ADMIT |

Source: `work/build15/proofs/real/RESULT.json`. C′ equals the supplied `774503e2...` identity prefix; the computed full identity is shown above. A/C and the preparation receipt retain their full SHA-256 pins. C′ file bytes bind to `31abe0871f35f9ca8d4a6445c5ee95ac03ec2324d37273e6b1f508acdbf246a1`. N’s local metadata replicas retain the original hashes; only their paths changed. Sources: `work/build15/LOCAL_PINS.json`, `work/build15/proofs/real/RESULT.json`.

| Mutation | Named refusal, identical for A/C/C′ |
|---|---|
| `depth_enabled` | `P_EXPORT_CONFIG_DIFFERENCE:depth_enabled` |
| `align` | `P_EXPORT_CONFIG_DIFFERENCE:align` |
| `camera` | `P_EXPORT_CONFIG_DIFFERENCE:camera` |
| `camera_overrides` | `P_EXPORT_CONFIG_DIFFERENCE:camera_overrides` |
| `lm_lr_scale` | `P_EXPORT_LR_SCHEDULE_MISMATCH:lm_lr_scale` |
| `unknown_extra` | `P_EXPORT_CONFIG_DIFFERENCE:unknown_extra` |
| `N_reset` | `P_EXPORT_ROUTING_OPENER_KEEP_REQUIRED:routing_opener_init` |

Source: `work/build15/proofs/real/RESULT.json`. The camera mutation increases the authenticated trunk depth by two; the camera-weight mutation changes the scale weight. The native CPU fixture additionally tests reset against an actual P-export init.

## Verification and preserved behavior

Focused tests: **62 passed**. Source: `work/build15/proofs/final_focused/TESTS.json`.
Frozen R2 group: **449 tests, 449 passed, 0 failures, 0 errors, 0 skipped**. Source: `work/build15/proofs/final/suite_tree/r2/results.json`.
Packet checks: **200 passed**. Source: `work/build15/proofs/final/packet/results.json`.

The frozen R2 result combines its initial run with the targeted rerun of three tests after restoring access to exact packaged metadata. No source or test assertion changed. The initial results, input hashes and rerun are bound in `work/build15/proofs/final/suite_tree/r2/RESUME_RECEIPT.json`.

The packet check `test_production_generator_on_off` fails an exact JSON comparison at the last printed floating-point digit. The generator source and baseline fixture are unchanged. This is an observed failure under the supplied CPU environment, not a pass or a changed tolerance. `test_decode_attacks_and_move_source_distance` could not execute its assertion: input absent (`/scratch/jjyeung/orch_n30/review_contracts/work/mytests/attack_decode.py`). Sources: `work/build15/proofs/final/packet/results.json`, `work/build15/proofs/packet/console.log`, `work/build15/PRESERVATION.json`.

The original-family read/reader/intake counts remain 1532/0/0, 2000/1186/1102, 2000/1222/1119 and 476/0/431. The exact 601-row exclusion list passes again. Sources: `work/build15/proofs/text/RESULT.json`, `work/build15/proofs/row_delta/RESULT.json`, `work/build15/proofs/preservation/RESULT.json`, `work/build15/COUNT_EQUALITY.json`.

The six population/routing guard mutations are caught with one reused mutant tree. Receipt closure, default deny, Unicode rules, M1 fixed-buffer binding, L1 typed refusals, effective-value comparison and milestone-step continuation remain covered by the focused and R2 suites. Sources: `work/build15/proofs/mutations/RESULT.json`, `work/build15/proofs/final_focused/TESTS.json`, `work/build15/proofs/final/suite_tree/r2/results.json`.

N retains its step-544 parent (`1d6eeb28...`), scale weight `0.04`, and all sealed scene exclusions. The prior repaired counts 777/1476/8067 and complete allocation table remain historical census evidence; the absent raw inputs prevent a new census. The qualification and hashes of each retained result appear in `work/build15/PRESERVATION.json`; unqualified records are retained only as historical records. Sources: `work/build15/inputs/kit_config.json`, `work/build14/proofs/census/CENSUS.json`, `work/build14/proofs/census/PLAN_RUN.json`, `work/build15/COUNT_EQUALITY.json`.

## Inputs not available

- census: not rerun: input absent (/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite). Prior-result qualification: True; no build-15 pass.
- native_builder: not rerun: input absent (/scratch/jjyeung/orch_n30/rows_r1/out/recovery_v3/rows.jsonl). Prior-result qualification: True; no build-15 pass.
- recompose: not rerun: input absent (/scratch/jjyeung/orch_n30/rows_r1/out/recovery_v3/rows.jsonl). Prior-result qualification: True; no build-15 pass.
- encode: not rerun: input absent (/scratch/jjyeung/orch_n30/rows_r1/out/recovery_v3/rows.jsonl). Prior-result qualification: True; no build-15 pass.
- mapping: not rerun: input absent (/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/work/tree/student_pilot/type_mix.py). Prior-result qualification: False; no build-15 pass.
- depth_sweep: not rerun: input absent (/scratch/jjyeung/orch_n30/review_tree11/work/parity/geo_dump.py). Prior-result qualification: False; no build-15 pass.
- generator suite group: not rerun: input absent (/scratch/jjyeung/orch_cd/ground_backend/work/c1mix_sb/student_pilot/ground_lifting.py). Its full source binding changed, so no prior suite pass transfers.
- legacy suite group: not rerun: input absent (/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/MANIFEST.json). Its full source binding changed, so no prior suite pass transfers.

Sources: `work/build15/PRESERVATION.json`, `work/build15/INPUT_AVAILABILITY.json`, `work/build15/SUITE_RUNS.json`. No missing data were fabricated or substituted. The inherited full parity sweep is not counted as a build-15 pass.

## Coverage, seal and delivery

Current observations cover **70/70 changed production statement heads against build 14**.
The standard-library monitor authenticates compiled code and exact source hashes. Cumulative coverage against the original tree, including inherited observations, is separate. Sources: `work/build15/DELTA_COVERAGE.json`, `work/build15/CHANGED_COVERAGE.json`, `work/build15/GAPS.json`.

Source seal: `67f8baf14b966a15b7d7a0efe64fc375632daee45d94f113f7b82f77d8a11480`. Archive: `out/tree_rebuild_b15_67f8baf1.tar` (gzip). Archive size and SHA-256 are recorded in `work/build15/DELIVERY.json`; stream verification is recorded in `work/build15/proofs/integrity/RESULT.json`.
Sources: `out/TREE_SEAL.json`, `out/TREE_FILES.sha256`, `out/TREE.diff`.

| Kit | SHA-256 | GO |
|---|---|---|
| a2 | `befc7f7918181f1d95670f026208705e34767c7d914eb78d58d24d11bfe0e473` | false |
| a0 | `f69e4c7e6b350d1de27a8ba35a695b2b85fe1fba68d8b66a3c15c73ccc3d425a` | false |
| r1 | `71e989b5cfdc22155807acddebefd5594715e4dcbb33aa6ccc36f6ee3d90a9f9` | false |

Source: `work/build15/KIT_RESULT.json`. Each kit was staged from empty and passed its existing scanner and hash verifier. No job was submitted. Production admission, full frame-host staging, GPU/pretrained execution, BF16 parity and the prior product-inference blockers remain unchecked or unresolved. No model, inference selector, fallback, agent loop or training-data quota changed.

Storage and temporary-size checks are recorded in `work/build15/STORAGE.json`, per-test storage receipts and the final integrity receipt. All proof writes stay under this workspace. No checkpoint, database, cache or frame set was copied from an external input.

## For the confirmation

Run from the package root using the supplied CPU environment. These commands retain proof outputs in fixed folders. Missing-input qualifications remain explicit.

```bash
bash work/build15/run.sh work/build15/real15.py
bash work/build15/run.sh work/build15/opener15.py
B15_PROOF=final_focused bash work/build15/run.sh work/build15/test15.py tests.test_r1_build15 tests.test_r1_build14 tests.test_r2_build_n1 tests.test_r2_n1fix tests.test_r2_n1fix3 tests.test_r2_build12 tests.test_r1_build13 tests.test_r2_build3.Build3.test_opener_export_keep_and_reset
bash work/build15/run.sh work/build15/witness_edges15.py
bash work/build15/run.sh work/build15/proofs15.py text row_delta preservation confusables mutations ground_runtime verify_route
bash work/build15/run.sh work/build15/preserve15.py
bash work/build15/run.sh work/build15/suite15.py
bash work/build15/run.sh work/build15/packet_inputs15.py
bash work/build15/run.sh work/build15/packet15.py integrated packet contract
bash work/build15/run.sh work/build15/delta_coverage15.py
bash work/build15/run.sh work/build15/coverage15.py
bash work/build15/run.sh work/build15/integrity15.py
```

The packet command currently records the qualified failures above. Use `kits15.py` only with an empty kit destination; `integrity15.py` verifies the retained kits. `delivery15.py` packages the final source and evidence. `localize15.py` is a build-time relocation step, not a routine confirmation command.
