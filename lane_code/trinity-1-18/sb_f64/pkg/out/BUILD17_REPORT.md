# Build 17

**GO=false. This package is incomplete for the requested production proof.** Room certification, resource scripts and the export-only receipt path are implemented and tested. The complete native mode-q fixture at both milestones is not demonstrated. The successful component proofs do not close that requirement. Sources: `work/build17/proofs/native/RESULT.json`, `work/build17/proofs/final_focused/TESTS.json`.

## Change table

| Requirement | Status | Evidence |
|---|---|---|
| Full pinned room rule and regenerated removal list | Closed for the three slices; v7 scope is qualified below | `work/build17/proofs/rooms/RESULT.json`; `work/tree_r1/student_pilot/r1_rooms.py` |
| General-partition CPU and one-GPU scripts | Closed; full-size resource estimates are GUESS | `work/build17/proofs/operator/{j.sh,j1.sh,SIZING.json}` |
| One native production-mode fixture with persisted handover, opener, initialization and every rank’s loss | **Not closed: the combined fixture remains unimplemented** | `work/build17/proofs/native/RESULT.json` |
| Export-only P receipt, proof-only N reader and training refusal | Closed in native producer/reader component tests; complete mode-q integration remains unproven | `work/tree_r1/launch_r1/p_export_receipt.py`; `work/build17/proofs/export/TESTS.json` |
| Checkpoint binding at the stop milestone | Preserved and tested | `work/tree_r1/tests/test_r1_export17.py:test_checkpoint_600_unchanged`; `work/build17/proofs/preservation/RESULT.json` |
| Operator request template and inventory | Available; future P milestone sizes and hashes remain unresolved | `work/build17/proofs/operator/` |
| Refusal tests, mutations, fresh kits, final checks and package | Evidence below; failed or absent groups are not passes | `work/build17/proofs/mutations/RESULT.json`; `work/build17/SUITE_RUNS.json`; `work/build17/KIT_RESULT.json` |

## Room certification

The admission code pins the split, visit metadata, alias map, reserve list and v7 build-time certification. Their exact hashes are in `work/build17/inputs/config.json:r1_training.room_authority`. The split’s teacher hash is checked against the supplied full authority. The room rule uses the row’s canonical field before aliases. The full census was rerun from the read-only mirror; it retains counts and bounded examples, not copied rows or databases. Sources: `work/build17/rooms17.py`, `work/build17/rooms.log`, `work/tree_r1/student_pilot/r1_rooms.py`.

| Population | Rows | K1 hits | R0 hits | Unresolved | Unremoved slice hits |
|---|---:|---:|---:|---:|---:|
| absolute_distance | 8315 | 0 | 0 | 0 | 0 |
| recovery | 994 | 21 | 0 | 0 | 0 |
| units | 8577 | 262 | 0 | 0 | 0 |
| v7, report only | 204413 | 2637 | 0 | 119375 | Not certified |

Source for every count in this table: `work/build17/proofs/rooms/RESULT.json`; that file binds the exact source paths and hashes. The regenerated list contains 283 rows and equals `work/build16/inputs/s.json` byte-for-byte. The full authority contains 50 held-out K1 rooms; the reserve file contains 372 rooms, and the rule also unions the split’s R0 captures. Sources: the same result and `work/build17/inputs/s.json`.

The gate certifies that the three pinned slices exclude K1/R0 after the pinned lists. It binds v7’s `EXCLUSIONS.json` as certification of the build population that record names. It reports resolvable v7 K1 hits and unresolved legacy rows separately. It does not certify all v7 rows as overlap-free. Unknown overlap is not a pass. Source: `work/build17/inputs/room_audit.json:certifies`.

## Job sizing

| Script | Request | Address-space cap | Time |
|---|---|---|---|
| `b/q.sh` / `j.sh` | CPU, 8 CPUs, 256 GiB RAM | 240 GiB | 48 hours |
| `b/q1.sh` / `j1.sh` | One GPU, 8 CPUs, 192 GiB host RAM | 180 GiB | 12 hours |

All resource sizes and durations in this table are **GUESS**, not full-model measurements. Source: `work/build17/proofs/operator/SIZING.json`. The scripts select the general partition and contain no submission name. The operator supplies that name when submitting. The local proof runner retains Trinity’s process bound; the job scripts use their own request-sized caps.

The estimate budgets three CPU copies of 9 billion BF16 parameters (54,000,000,000 bytes), 24 GiB for frozen towers and heads, 96 GiB for activations/workspace, and 48 GiB for runtime/readers. The GPU estimate budgets 28 GiB for weights/towers/heads, 40 GiB for activations/workspace, and 12 GiB of allocator margin. All are **GUESS** from the load/first-batch code, recorded in `work/build17/proofs/operator/SIZING.json`. The one-GPU script is recommended for latency, conditional on an operator-selected GPU with at least 80 GiB. No GPU or full-size memory fit was measured. Every logical rank runs sequentially in the one proof process; no optimizer step is requested.

## Fixture evidence and missing integration

| Requested stage | Observed evidence | Qualification |
|---|---|---|
| Verify staged pins | Refusal and relocation tests | Component tests |
| Native tiny-store builder | `carrier_c1_data.build_stream` builds the RGB fixture’s VQA store | Executed |
| `s1_routing.build` | No successful combined fixture run | Not demonstrated |
| `r1_routing.compose_native` | Separate composition and room-refusal tests | Not demonstrated in the combined fixture |
| Prepare through `s1_admission` | No successful combined fixture run | Not demonstrated |
| `r1_population.bind_prepared` and `r1_loader.production_audit` | Separate inherited native-reader/sampler tests | Not demonstrated in the combined fixture |
| Persisted handover reader | Export-only and checkpoint component admissions | Executed separately |
| In-job opener witness and N initialization | Native export/witness/init component tests | Executed separately |
| Every rank’s resumed first batch and loss | Inherited tiny forward component test | Not a production-mode fixture |
| One mode-q RESULT admitting both milestones | No such result | **Open** |

Sources for this table: `work/build17/proofs/native/RESULT.json`, `work/build17/proofs/final_focused/TESTS.json`, and the exact functions in `work/tree_r1/tests/test_r1_build{15,16,17}.py`. Native stage names in the implementation are not treated as observations.

The RGB probe uses synthetic frames containing a red square left of a blue square, reduced native model dimensions, and `PatchGridProcessor` in `work/build17/native_assets17.py`. This permitted HF constructor stand-in uses a real persisted HF tokenizer and emits the native pixel, grid, attention, media-token and input-ID fields. It resizes by nearest sampling, patchifies temporal pairs, and preserves the tiny vision configuration’s patch/merge token counts. No trainer, reader or producer function is changed to fit it. The native Qwen vision constructor works without a stand-in in this probe.

The native builder/reader/encoder probe produces 32 video tokens and pixel shape [128, 24]; its native VQA forward has finite loss 12.44449520111084. Source: `work/build17/proofs/native/RESULT.json`. This probe does not demonstrate all head losses, every rank, P export initialization, or mode-q admission. The missing combined fixture is unfinished build work, not a claim that the permitted processor stand-in is unavailable.

## Export-only binding

The new producer hashes the published artifact, heads, full-weight manifest, index and shards, actual runtime config, binding, preparation, stream receipts and stream indices. Its distinct receipt states that no checkpoint exists at the milestone. It refuses a milestone at or beyond the configured stop. The unchanged checkpoint receipt producer remains byte-equal. Sources: `work/tree_r1/launch_r1/p_export_receipt.py`, `work/build17/proofs/preservation/RESULT.json`.

N requires both `r1_training.proof_mode="q"` and the mode-q invocation scope. A config flag alone cannot authorize export-only admission. The real launch refuses `p-export-only-v1` by name; the donor reader checks the invocation scope again. Stop-step checkpoint metadata, layouts, RNG and absent-state reporting retain their existing verification. Sources: `work/tree_r1/student_pilot/r1_persisted.py`, `work/tree_r1/student_pilot/r1_handover.py`, `work/tree_r1/launch_r1/entry.py`.

Component tests admit export-only step 400 and checkpoint-bound step 600. They refuse an export-only stop receipt, a training config, a training invocation, altered shards, invalid checkpoint status and invalid producer binding. The same-size shard twin tests hashing independently of size checks. Sources: `work/build17/proofs/export/TESTS.json`, `work/build17/proofs/final_focused/TESTS.json`, `work/build17/proofs/mutations/RESULT.json`. These tests use native synthetic exports and the real producers/readers; they do not supply the requested complete persisted-subset, export-tar, mode-q fixture.

### P operator usage

Run inside P's allocation after the export upload finishes, before allocation cleanup.

For a non-stop milestone, run `python -m launch_r1.p_export_receipt --run-pins r.json --artifact artifact.json --output h.json --trainer-commit <commit>`.

`r.json` must contain exact `{path,sha256}` pins named `config`, `binding`, and `preparation`; `SLURM_JOB_ID` supplies the allocation identity.

Expected receipt fields: `schema=p-export-only-v1`, `step`, `stop_step`, `checkpoint_status="no checkpoint at this milestone"`, `job_id`, `trainer_commit`, `pins`.

`pins` binds artifact/config/binding/preparation, heads, full_weights, its index and every shard, stream receipts and any stream indices.

Keep every JSON byte unchanged; persist the metadata plus one export-weights tar, and obtain h.json's trusted SHA-256 independently.

Stage P's pinned model manifest and tokenizer/config metadata separately for the in-job opener witness.

N admits this receipt only through mode q with `r1_training.proof_mode="q"`; its training launch refuses it.

The producer and reader refuse the configured stop step; at step 600 use the unchanged `launch_r1.p_handover_receipt` with checkpoint metadata and RNG files.

## Operator packet

The request template is `work/build17/proofs/operator/REQUEST_TEMPLATE.json`; the short stage/verify/submit/read sequence is `OPERATOR.md` in that directory. `STAGING.json` records source, opaque staged name, size, hash and delivery category. `P_LOCATIONS.json` records exact A, C, C-prime and runtime config paths and the authenticated v7 source receipt. The source receipt’s hash matches P config A and names `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/d.db`. This build does not upload v7. Source: `work/build17/proofs/operator/P_LOCATIONS.json`.

The known unique upload inventory totals 235704834 bytes across 35 files. It includes slices, N-side lists, authorities and the kit/tree. 79 discovered input records lack local size measurements; milestone outputs also lack actual sizes/hashes until P produces them. These are unresolved fields, not invented values. Source: `work/build17/proofs/operator/SUMMARY.json` and `STAGING.json`.

At a non-stop export, persist the export-only receipt and its metadata closure; no checkpoint is implied. At the stop, persist complete.json, layouts and RNG alongside the checkpoint receipt. Both need P’s model manifest and tokenizer/config metadata, plus one export-weights tar. The packet uses opaque staged locators and leaves the submission name to the operator. Sources: `work/build17/proofs/operator/MILESTONE_INPUTS.json`, `out/EXPORT_RECEIPT_USAGE.md`.

## Verification and preservation

The focused run passes 88 tests; the edge run passes 4 tests. Source: `work/build17/proofs/final_focused/TESTS.json` and `work/build17/proofs/edges/TESTS.json`.

The export-producer edge run passes 4 tests covering path escape, hash mismatch, duplicate manifest entries, absent weights, invalid milestone/stop, stream mismatch, index closure and CLI invocation. Source: `work/build17/proofs/producer_edges/TESTS.json` and `work/build17/export_edges17.py`.

The mutation matrix catches 25 mutants. Source: `work/build17/proofs/mutations/RESULT.json`. Each entry records a passing clean control, a failing mutant, the test and the current source hash.

Changed-statement coverage observes 286 of 321 changed AST statement heads. Source: `work/build17/DELTA_COVERAGE.json`. Standard-library monitoring counts only matching source hashes and compiled code; unobserved statements remain listed. No coverage package is used.

The frozen R2 suite passes 449 of 449 tests, with 0 failures and 0 errors. Source: `work/build17/proofs/final/suite_tree/r2/results.json`; `work/build17/SUITE_RUNS.json` records the runner result and unavailable generator/legacy groups.

Packet outcomes, from `work/build17/proofs/final/packet/results.json`: 2 failed, 200 passed. Failed tests remain failures.

The packet failures concern its unchanged exact floating-JSON comparison and the absent external `/scratch/jjyeung/orch_n30/review_contracts/work/mytests/attack_decode.py`. The missing generator and legacy inputs are named in `work/build17/SUITE_RUNS.json`; the large real-row parity sweep was not rerun. No absent input is fabricated.

The trainer, model, legacy checkpoint/export producer, opener rules, counting guard, row grammar, intake and sampling implementation pass byte-equality checks against the supplied baseline where required. The step-544 parent, 601-row list, K1 list, final z list, card cells and weight_scale=0.04 remain bound. P’s real A, C and C-prime configs pass effective-value comparisons. Sources: `work/build17/proofs/preservation/RESULT.json`, `work/build17/proofs/real/RESULT.json`, `work/build17/proofs/final_focused/TESTS.json`.

Every kit was staged into an empty directory and passes its inherited scanner/hash verifier with GO=false. No scheduler, Orchard, GCS, network, GPU, SSH, Git or additional agent was invoked. Source: `work/build17/KIT_RESULT.json`; `work/build17/run.sh` supplies local resource limits. Storage measurements are in `work/build17/STORAGE.json` and the per-test result files.

## Package

The source seal is `846ead7a30d461a51075469621a54b1723c450e1f2a51c107cb8e0b26926ed95`. The gzip tar is `out/tree_rebuild_b17_846ead7a.tar`; its exact byte size and SHA-256 are in `work/build17/DELIVERY.json`. Stream verification is in `work/build17/proofs/integrity/RESULT.json`. No real checkpoint, frame set or database is copied into the package. Source: `work/build17/delivery17.py`.

The archive retains current code, kits, packet inputs and verification records. `work/build17/PACKAGE_OMISSIONS.json` lists bulky historical generated payloads excluded from the archive; those files remain in this workspace.

## For the confirmation

This is a review package, not the final qualified kit for a production proof. Confirming the requested build requires the missing complete native mode-q fixture, including export-only admission at the non-stop milestone, checkpoint admission at the stop, all-rank initialized losses and the corresponding refusal twins. The operator must also resolve actual P milestone pins and sizes before a real submission. The existing component passes do not waive either requirement.

From the workspace root, `bash work/build17/run.sh work/build17/integrity17.py` verifies the package, source seal and staged kits. Review `work/build17/DELIVERY.json`, `work/build17/proofs/integrity/RESULT.json` and `work/build17/proofs/operator/OPERATOR.md`. This verification does not submit a job.

Not checked: full-size model loading, frozen-tower peak memory, GPU latency, a real P milestone export, complete mode-q admission, or a real cluster submission. The artifact is not ready for the requested production proof.
