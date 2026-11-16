# Earliest launchable configuration: D0, a data-only reseal on kit 07ca49df (lane seal_plan, 2026-11-15)

Answer to ORCH order 1800Z. Evidence: the recovered texts (`orch_n30/recovered/recovered_briefs_20261115_v2.tar.gz`), `distill_design/TRACE_RULING_20261115.md`, `LEG_S1_TREE_20261111.md`, `DOSE_POOL_KIT_20261111.md`, `POOL_R2_MIXTURE_CONTRACT_TOTALCOUNT_20261112.md`, `LEG_S2_MIXTURE_AND_FORM_FLAG_20261112.md`, `orch_n30/events/evalx27/ORCHARD_INVENTORY.md`. Unverified marks claims that only an Orchard listing or a CPU run of the kit can settle.

## Verdict
D0 is the earliest configuration that respects the trace ruling, and it can launch about one working day after the rows lane starts, if the Orchard inventory (rows brief step 0) finds the sealed input row files. D0 runs the sealed LEG-S1 trainer source and its kit machinery unchanged and replaces only the row files of the VQA and routing streams. Two things change outside code: the kit's input pins, and three config fields (the init artifact, a new run identity, the step budget). The kit's own builder can produce both without code edits (unverified until the kit builder is run). The full stack (A0, then A2) stays as planned and is built in parallel.

## D0 contents (per 288-row step, world 4, no MDG; stream quotas of the sealed leg)
- VQA 128, natural shares of the replaced store (the sealed leg used natural shares within stream quotas, not per-type quotas; TRACE_RULING 1a): the nine sealed direct families re-rendered in the ruled grammar from the values each row holds (direction easy/medium/hard, relative distance, object size, counting, appearance order, 3D box with one Locate line; identities, questions, options, frame pins and answer bytes unchanged), plus facing toward/away pairs subsampled to about 17,500 pairs (35,000 rows, about 29 rows/step at natural share), plus the 2,335 total-count rows if their source annotations exist.
- Routing 64: the sealed camera displacement, movement direction, rotation and absolute-distance programs unchanged (GT printed responses; no K1 output needed), the sealed 581 room programs unchanged (GT responses; see ruling 3), route planning re-rendered with one Step per waypoint (replaces the empty think block).
- Pose 64 and pointing 32: the sealed stores unchanged (the kit already binds both pose sources).
- Rows in the 80 withheld rooms and the 1,172 lineage-less room rows are filtered in the row build.
- Init: the step-544 export (artifact 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef) as a warm start with a new run identity, not an exact resume of 469ddece (the changed stores must refuse resume anyway). Length: register 1,000 steps (~146 GPU-h at 131 s/step, estimate) or a shorter first allocation; stop rule and reads F1-F4 of TRACE_RULING 2.7 at steps 100 and 200.

## What the unchanged tree cannot consume, and the minimal change for each
| Item | Why the unchanged tree has a problem | Minimal change | In D0? |
|---|---|---|---|
| Replaced store bytes | The kit pins the ordered content hashes of its input stores (rs_cover matched them against production), so new rows fail the kit verifier | Rebuild the kit with the tree's own builder and new input pins; no code change (unverified: that `launch_s1/build.py` accepts new pins without edits) | yes |
| Init and run identity | The kit's config names the CP1 m200 init and run 469ddece | Config fields only, if the tree's warm-start path (`student_pilot/warmstart.py`, LEGS1_WARM_START_CONTINGENCY_20261113.md) takes an export artifact (unverified) | yes |
| Re-rendered direct rows | None for the schema: they are direct text targets like the sealed VQA rows | none; the grammar is enforced by the row build's validator and its receipt, not inside the tree | yes |
| Facing pairs and totals as extra families | The sealed config has no `extra_pool_sets` (mixture contract absent), so they cannot be added as a separate pool with a share | Put them into the replaced VQA store itself and set their share by how many rows the build writes; twins kept in the store together (the sampler does not guarantee both twins land in the same step: accepted cost) | yes |
| New subtype keys (away, multi-category total) | The tree may key direction rows by `object_rel_direction_*|toward` and may refuse an unknown subtype (unverified) | If refused: label them with the existing type keys; the CPU first-batch run shows which | yes, after the check |
| Room size as a direct type | The pinned route file lists room size as a program type; a direct room row may be refused, and changing the route file is a config change that earlier reviews treated as high risk | Keep the 581 sealed room programs (GT responses) instead; room direct waits for A0 | no |
| Unit rows (non-metre programs) | Program rows enter only through the sealed admission audit, which aborts on some row patterns (rc_review: `audit_training_contract` near `s1_routing.py:403-406`) | Needs the contracts patch | no (A0) |
| Recovery rows (failed call, then direct answer) | The sealed admission has no support for failed-call fallback rows (o3_cache RESULT 0608Z) | Needs tree code | no (A0) |
| Frames of the new rows | Re-rendered sealed rows keep their pins. Facing pairs come from direction programs that carry pins in the sealed routing input (unverified). Rows without pins use the `frames_pending` schema, which the trainer's preparation resolves through k6tk (DOSE_POOL_KIT_20261111.md) | none if the k6 store staged with the kit is complete (unverified: evalx27 saw only 1.33 GB at `cp4tk_fr/k6tk`) | yes |
| Scene exclusions | The tree applies BENCH v2 and dev-S1 exclusions at admission; new rows come from the same scenes | none; the build also filters the 80 withheld rooms | yes |
| Job-visible paths | Kit 07ca49df already ran on Orchard under opaque names | none | yes |

## What D0 gives up against the full stack
