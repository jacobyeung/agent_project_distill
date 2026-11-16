# Frame-host CPU job

The job template is delivered under each kit as `b/f.sh`, with executable bootstrap `b/e.py` and input packet `k/f.json`. It has not run. The packet deliberately has missing real-input pins; the default is to refuse, not to invent hashes or reuse stale stores. The orchestrator must bind those inputs, review the regenerated kit and issue GO before submission. No Orchard call is part of this build.

Command on the approved host, from an opaque kit directory: `bash b/f.sh`. The scheduler form is the same file; only the orchestrator may submit it. The file requests the CPU `general` partition, no GPUs, 8 CPUs, 800 GB RAM and 6 hours. The no-progress limit is 1,200 seconds (`work/tree_r1/launch_r2/build.py`; `launch_r2/host.py`).

The source archive is authenticated by the parent byte verifier and `student_pilot.source_seal.check_archive`, then unpacked into a fresh job-local directory. Native Python source names remain inside that archive/execution namespace; process arguments, kit files and logs use opaque names. This is the explicit parent source-archive convention requested in the build brief. It is not a claim that native module names inside the archive are opaque.

The producer reads pinned family envelopes, preserves sealed exclusions, checks post-filter repeat metadata, then materializes VQA, routing, both pose families, pointing and membership. A2 requires its real dense manifest and frozen-tower assets. Dense reconstruction metadata precedes sparse LM selection. The bridge writes native receipt envelopes and calls the native preparation function. The first-batch check encodes every rank through `Rows.get`, and stops at CPU tensors before model forward. The dry-run encoding check uses the same real reader; neither path claims a pretrained forward or GPU admission (`work/tree_r1/launch_r2/host.py`; `student_pilot/carrier_c1_run.py`).

The input packet requires SHA256 pins for each manifest, each pose source, the native configuration, pose metadata template, real-proof inventory and scene-rebuild specification. The job derives filtered counts and final-reader indices from the admitted envelopes. Component evidence, root mappings, export metadata, the opener vocabulary witness and A2 assets must be bound transitively in those records. Parent source pins are preserved in the kit provenance capsules and `out/POSE_SOURCE_BINDINGS.json`; real row and frame-host pins remain unavailable. All unknown bindings refuse.

Before stores are written, the job performs these metadata steps (`work/tree_r1/student_pilot/r2_scene_bindings.py`; `work/tree_r1/launch_r2/host.py`):

1. Authenticate the merged dev exclusion, its sealed input lineage, and the unchanged benchmark exclusion. The merged pin is recorded in `out/B3B_MERGED_BINDING.json`.
2. Read the real pool package's pinned source metadata. Rebuild its dev and benchmark QID lists, preserving every sealed membership. Run native `s1_pool.prepare` with opaque output filenames and progress summaries, then validate the resulting selection's own upstream report. Recompute the manifest's after-exclusion summaries from the same metadata.
3. Recount VQA, camera, each pose source and pointing from complete metadata for their input receipts. Retain original receipt pins as provenance. Print each source's shared-room removal count under an opaque identifier and pin the named mapping in its receipt. Write new upstream scene reports against the merged list. Full mode requires the pose census inputs to match the sealed pose databases supplied in the packet.
4. Write a `dev_s1_manifest_v1` reference with the merged withhold file and per-source dev/benchmark counts. Bind that reference and its source map in the trainer configuration. The trainer compares the rebuilt census exactly.
5. Run native intake on each complete envelope family. Check surviving source membership and derive type counts and indices in final store order. Apply the metadata repeat gate to those counts before RGB materialization. Then attach the regenerated reports to native stream receipts and run native preparation and every-rank CPU encoding.

The pinned `scene_rebuild` specification contains `pool_manifest`, optional native `remove_files`/`tokenizer`, and `sources` with exact keys `vqa`, `camera`, `pose_a3v2`, `pose_a2v3`, and `pointing`. Each source binds its original `receipt`, complete metadata `rows`, and `count`, which must equal the original receipt count. The rows pin must equal the receipt's `database` pin or its explicit `rows_metadata` pin. The reader opens native SQLite read-only and also accepts JSONL or gzip JSONL, detected by file header. These metadata rows represent the receipt's population before the added withholding. A selected subset needs an explicitly bound metadata export; a matching count alone is insufficient. Historical reports remain provenance; their hashes are never relabelled. Rebuilt selections use separate receipts rather than changing the original database's count.

Each family manifest names `scene_source` (one source key or `pool`) and pinned-content `mix_cells` assignments keyed by row QID. Assignments supply a mixture `type` and a `pair` identifier for facing twins. They classify source rows; benchmark answers never select assignments or quotas. Re-rendered rows must carry `provenance.source_qid` when their original source QID differs. Missing source membership, unknown overlap, incomplete counts or incomplete facing pairs refuse. The real metadata exports and assignments have not been supplied or checked here.

The pose manifest headers must bind their original source through `pose_source_sha256`. Full mode checks the exact sealed database hashes from `out/POSE_SOURCE_BINDINGS.json`: `b32359ce256a567912d6436fac95dcab78bcef3bb2e1154cabdca57bacdc5320` and `0b95850a2dec57ec6702ca72cd198eb5afdcdcdd5f711a76a878104e30ec3571`. The packet also requires the delivered init archive hash, a complete member-hash inventory and an explicit member-size limit. This manifest-header contract is the default pending the absent rows/contract handoff (`work/tree_r1/launch_r2/host.py`).

## Storage and time bounds

| Store | Estimate, bytes | Per-file limit, bytes | Source |
|---|---:|---:|---|
| VQA | 3,200,000,000 | 4,800,000,000 | User build brief; `launch_r2/host.py:ESTIMATES` |
| Routing | 1,700,000,000 | 2,550,000,000 | User build brief; `launch_r2/host.py:ESTIMATES` |
| Pose | 1,500,000,000 | 2,250,000,000 | User build brief; `launch_r2/host.py:ESTIMATES` |
| Pointing | 800,000,000 GUESS | 1,200,000,000 | `launch_r2/host.py:ESTIMATES` |
| Membership | 1,000,000,000 GUESS | 1,500,000,000 | `launch_r2/host.py:ESTIMATES` |
| Dense metadata | 1,000,000,000 GUESS | 1,500,000,000 | `launch_r2/host.py:ESTIMATES` |

The margin is 1.5× each estimate, giving 9.2 GB estimated stores and 13.8 GB of store limits, excluding input mounts, the source closure, SQLite journals and init staging. These totals are arithmetic from the table. No checkpoint or frame replica is bundled. Full mode requires the delivered-export mapper and must account separately for the approximately 21.6 GB export reported in `work/cont_ops/D0_LAUNCH_PROCEDURE.md`, procedure step 3. All outputs belong under the one kit job folder.

GUESS: allow 120–360 minutes for preparation and CPU encoding. The lower end follows the parent preparation measurement of about 105 minutes; real repaired-row encoding and hashing have not been timed (`work/cont_ops/D0_LAUNCH_PROCEDURE.md`, procedure step 8). The watchdog refuses a wall-time overrun or a stalled step rather than relaunching it.

The watchdog covers input hashing and execution. The native SQLite writer bounds database pages; serialized membership and dense manifests have independent limits. A process file-size ceiling backs those limits, and the write audit refuses paths outside the job root while allowing pinned read-only SQLite inputs. The init mirror links to the staged members rather than duplicating their bytes (`work/tree_r1/launch_r2/host.py`; `launch_r2/runtime.py`; `student_pilot/r2_materialize.py`).

After successful preparation, the orchestrator must pin `o/ee000004/0.json` as the launch record’s prepared receipt and reseal the kit. The production entry verifies the receipt against the source archive, input packet, statement obligations and every rank/stream, then reuses the existing stores. It still requires independent review and production authorization. Native runtime receipt contents retain native identifiers; the external scanner checks their filenames and in-folder links, not those internal values (`work/tree_r1/launch_r2/entry.py`; `launch_r2/build.py`).

## Statement obligations

The inherited unresolved statements are listed below. The host must record actual line hits, not merely a successful process return. Native first-batch planning is reachable through the encoding-only mode. The full-store branch remains prohibited on Trinity. A successful encoding check cannot claim execution of the model-forward path.

| Historical file:line | Class | Statement |
|---|---|---|
| `student_pilot/carrier_c1_run.py:1617` | model-loader | `plan = next(data.mixed_indices(counts,offset+1,start_step=offset,training_mode=cfg.get('training_mode', 'mixed'),` |
| `student_pilot/carrier_c1_run.py:2933` | model-loader | `plans = list(data.mixed_indices(counts, steps, training_mode=cfg.get('training_mode', 'mixed'),` |
| `student_pilot/r2_materialize.py:24` | frame-host | `if os.environ.get('STUDENT_R2_FRAME_HOST') != '1':` |
| `student_pilot/r2_materialize.py:25` | frame-host | `raise ValueError('Full materialization requires an explicit frame-host admission')` |
| `student_pilot/r2_materialize.py:26` | frame-host | `limit = None` |

Source for every inherited statement above: `out/B2_COVERAGE_CLASSIFIED.json`. Current line mappings and unexecuted statements are in `out/B3B_COVERAGE_CLASSIFIED.json` and `out/B3B_COVERAGE_REMAP.json`.

`launch_r2.runtime.obligations` resolves the current lines from their real functions and binds each source hash. The host deliberately tests missing full-store authorization before the admitted call, then checks that every inherited obligation was reached. The native dry-run and first-batch sampler statements now run before forward in encoding-only mode. The local source-bound receipt is `out/B3_HOST_STATEMENT_PROOF.json`; full-store obligations remain unrun.

The producer/estimator proof uses a bounded synthetic family slice and prints its extrapolation. Its actual row count, produced SQLite bytes, hypothetical census and calculated limit are in `out/B3_ESTIMATOR_PROOF.json`. These are measured fixture bytes and arithmetic, not a real-population estimate. The missing real count file prevents a real after-filter repeat table.

Not checked: real-row census and extrapolation, full stores, actual pose-source joins, real export staging, first batches on real RGB, host runtime/dependency availability, final input relocation, pretrained-model admission and the full host statement-hit receipt. The synthetic estimator and local containment proof do not supply those missing results. A real host result is required before GPU launch.
