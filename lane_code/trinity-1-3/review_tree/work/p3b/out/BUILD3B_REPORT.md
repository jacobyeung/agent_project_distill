# Build 3b report

The tree binds the merged dev population across every stream. Native metadata rebuilds, upstream receipts, the census and the trainer use the same exclusion pin. Both kits remain non-admitting until the real frame-host inputs and existing evidence gates pass. No job was submitted.

## For the tree review

- `student_pilot/r2_scene_bindings.py` deterministically merges the sealed dev list with the shared rooms and capture aliases. It rebuilds native pool selection, source receipts, the exact census, admitted counts and reader indices.
- `launch_r2/host.py` runs the metadata steps before the repeat gate and materialization. `native_config` attaches the rebuilt reports to every native stream receipt. `launch_r2/build.py` binds the merged list in both kits and leaves the new host inputs explicitly missing.
- `student_pilot/r2_intake.py` applies the merged native exclusion in addition to the retained sealed r2 rules. `s1_exclusions.py` and `s1_scene_census.py` recognize provenance aliases consistently and compare the rebuilt reference exactly. Existing foreign-list and census refusal messages remain.
- `student_pilot/r2_contract.py` verifies the all-stream bindings before preparation and prepared reads. Direct configuration also binds the merged population. Review the raw-source provenance, pool selection's own upstream report, reference pin, population counts and rank-facing indices together.
- `student_pilot/s1_pool.py` supports opaque output filenames and progress summaries for the host rebuild. Its native selection rules remain in use. `launch_r2/distributed.py` isolates parent imports after the full regression exposed a bootstrap module collision.

Paths above are relative to `work/tree_r1`. The complete changes against the immutable base are in `out/TREE.diff`; identities are in `out/TREE_FILES.sha256` and `out/TREE_SEAL.json`.

## Bound population

The merged SHA256 is `184fcda38b5dc9d55c7f1cb26b1df832f65ea4e980f3d6221db9b247ef4727fc` (`out/B3B_MERGED_BINDING.json`). It uses the sealed `dev_s1_withhold_v1` schema and preserves the original members. Its inputs are:

| Input | SHA256 | Source |
|---|---|---|
| Sealed dev population | `969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986` | `work/kit07ca49df_meta/m/k/dev_scene_exclusions.json` |
| Shared withheld rooms and aliases | `634820b44927b1a50c18db9b90246b4b99f8954b0d7f5f2893e547f1c92879ed` | `work/shared/WITHHELD_ROOMS_80.json` |

VQA, pool distance/room programs, camera, each sealed pose source and pointing all use this population. Both arms receive it because they share the mixture. Benchmark exclusions and the other sealed r2 exclusions remain independently required. Unknown overlap refuses.

The frame host rebuilds QID exclusion lists before invoking native `s1_pool.prepare`. It re-derives source receipts from authenticated metadata, prints and pins shared-room removal counts, writes the new `dev_s1_manifest_v1` reference, and derives counts and indices from actual admitted envelopes. The metadata pin must be bound by the original receipt; a matching count is insufficient. Native SQLite inputs open read-only. Full mode also binds the pose census to the sealed databases. The repeat gate then runs before any RGB store is materialized. The sealed selection or sealed reference fails the unchanged mismatch checks. The runnable entry is each kit's `b/f.sh`; the required inputs are documented in `out/FRAME_HOST_JOB.md`.

Real removal counts remain unknown. The card names the counts that the frame-host job must fill (`out/PRELAUNCH_CARD.md`). Local fixture counts are not population estimates and do not admit the real mixture.

## CPU evidence

The bounded pool fixture follows the supplied manifest, selection and index shapes. It includes native packed distance and room records and direct routing records. The real producer and `selected_rows` reader retain clean rows and refuse withheld native names and aliases. The pool-family proof also runs real materialization, native store reads, sampling and every-rank encoding (`out/B3B_POOL_PROOF.json`; `out/B3B_POOL_BATCH_PROOF.json`; `work/tree_r1/tests/test_r2_build3b.py`).

Per-stream proofs run real intake, materialization, SQLite reads and membership admission. Re-sealing a leaked row still fails the native reader. The integrated proof runs native preparation, census verification, the mixed sampler and encoding for every rank. Synthetic RGB, a tiny lossless processor/tokenizer and pretrained-model metadata stand in at the unavailable model boundary; producers, filtering, census, stores and readers are real. Encoding stops before model forward (`out/B3B_NATIVE_PROOF.json`). Retained earlier model proofs remain separate evidence.

The host metadata proof derives actual fixture counts and reader indices. Its incomplete fixture population fails the repeat gate before a store is written; no synthetic full-population admission is claimed (`out/B3B_COUNTS_PROOF.json`). Mutations cover old config/upstream/pool/reference bindings, census counts, incomplete metadata, source membership, cross-stream assignments, facing pairs and output containment (`work/tree_r1/tests/test_r2_build3b.py`).

| Test evidence | Tests | Failures | Errors | Skips |
|---|---:|---:|---:|---:|
| `out/B3B_ALL_TEST_RESULTS.json` | 200 | 0 | 1 | 0 |
| `out/B3B_CLOSURE_TEST_RESULTS.json` | 37 | 1 | 1 | 0 |
| `out/B3B_FINAL_TEST_RESULTS.json` | 14 | 0 | 0 | 0 |
| `out/B3B_FOCUSED_TEST_RESULTS.json` | 8 | 0 | 1 | 0 |
| `out/B3B_REVISED_TEST_RESULTS.json` | 10 | 0 | 1 | 0 |

Every number in that table comes from the file named in its row. Earlier failed runs remain visible. Their fixture defects and any production fixes are recorded in `work/build3b/STATUS.md`; the accepted regression results determine the final status.

The full-suite run and subsequent targeted closure resolve all 200 required cases; the latest outcomes cover 204 cases and all pass (`out/B3B_REGRESSION_ACCEPTANCE.json`). This is cumulative acceptance, not a claim that the earlier full run passed before its defect was repaired. The per-case evidence remains linked in that record.

Changed-statement coverage over the cumulative tree is 5086/5098; production coverage is 2930/2942. The unexecuted production classes are `{'CPU-only': 0, 'frame-host': 10, 'model-loader': 0, 'GPU': 2}` (`out/B3B_COVERAGE_CLASSIFIED.json`). The standard-library tracer records current hits and remaps prior hits only across unchanged lines from authenticated snapshots. Each remaining statement has its file, line, text, category and reason (`out/B3B_COVERAGE_REMAP.json`; `work/build3b/coverage.py`).

## Artifacts and limits

Tree seal: `ba0c6ebfd34e44c8565011866ef7913880c95e276d76b6fdcf965da6e942827c` (`out/TREE_SEAL.json`).

| Arm | Kit | SHA256 | Source |
|---|---|---|---|
| A0 | `work/build3b/kits/b8e96247a318` | `5d2a4fb07370eb32861368f5b0ab33b7ed41a657a34d2e73a2e642bd1d2ad781` | `out/B3B_KITS.json` |
| A2 | `work/build3b/kits/5bf7dfd2e984` | `f0ffdadbce5234160a857983f3137ae5830ed8537b95f604dadb9c00693d537a` | `out/B3B_KITS.json` |

Temporary storage is 152205340 bytes; the lane is 1192989817 bytes (`out/B3B_FINAL_REVIEW.json`). The harness measures storage before and after each test, retains fixtures, and applies the required file-size and CPU limits (`work/build3b/TEST.sh`; `work/build3b/bounded_runner.py`). The storage walker matched the inherited walker exactly (`out/B3B_STORAGE_WALK.json`). The previous temporary folders were read-only. No full store or real checkpoint/frame/database/cache copy ran locally.

Not checked: real pool bytes, real source joins and counts, real metadata exports, actual frame-host runtime/relocation, full stores, pretrained forward behavior, GPU fit or timing, distributed training or evaluation. The A2 dense artifact remains an explicitly synthetic staging fixture. The existing scanner checks external job paths/arguments/environment and runtime filenames; native source namespaces and native receipt contents retain the previously disclosed scanner exceptions (`out/BUILD3_REPORT.md`; `work/tree_r1/launch_r2/build.py`).

No network, SSH, Git, other agent, launch or Orchard call ran. All writes stayed inside the lane.
