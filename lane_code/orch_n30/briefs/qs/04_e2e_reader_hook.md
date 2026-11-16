# Build brief 04: the end-to-end reader (in-forward call hook, one artifact, learned scale, no guard)

Builder: Claude Opus, high effort. Written by lane queue_synth, 2026-11-16. CPU build first; the parity read (about 1.3 H100-hours or one Trinity 48 GB card for 3 hours) needs ORCH's GO.

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). No Git, no deletion, no GPU and no Orchard submission without an ORCH GO naming the job. Read named files only. Lane folder `/scratch/jjyeung/orch_n30/e2e_reader`; events `B/events/e2e_reader/`.

## Why
The user wants one trained model that uses its own heads inside its own train of thought, with no external tool and no agent loop. The acceptance test is brief 03 (EAT-1). The next leg (A2) may claim a routed type only through a reader that passes it. This brief builds that reader for everything that needs no new trained head, and the sockets for the two heads that do (brief 05 and the scale head below).

## Scope: what the reader serves, and how
| Call | Source in the artifact | Fixed math | Replaces |
|---|---|---|---|
| `<move>`, `<turn>`, `<pose>` (camera types) | frozen G3T tower run inside the call on the read's own frames; own gravity head | relative pose, unit conversion, formatting | the cached tower outputs, the gravity guard |
| metric scale for any metric response | a scale head in the checkpoint (below) | multiply | `tower_scale_rule.json` |
| `<ground obj=NAME mode="box">`, `<gap>` (absolute distance) | a grounding socket: stage 1 = frozen SAM 3 tower inside the artifact plus a selector head trained on tower tensors; stage 2 = the own-encoder head of brief 05 | unprojection of the selected mask's pixels, box from points with no tuned constant, gap | the mask cache, the fitted logistic selector, the alias table, the depth cut, the fitted box policy |
| `<ground mode="room">` | none: A2 trains room direct; a checkpoint that still emits the call gets the response of a room-area head only if one exists, and otherwise the call is unserved and counted | — | room rule rv |
| a failed or empty response | the model's own continuation (recovery rows in the leg) | — | the reader's fallback arm |

## Inputs
- Current runtime: kit C8r, `B/events/native_r2/c8r_kit/` (code_c8r.tar f4535bc0...), VSTI kit V1c (`B/events/native_r4/STATUS.md`), spec quoted in `distill_design/B6_GROUNDING_DESIGN_20261115.md` section 4.1; `NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md`.
- The tree's native decode path: `student_pilot/carrier_c1_decode.py` and the tower read layer in the next-leg tree (package `tree_rebuild_b5_ba346bd9.tar`, trinity-1-3 `/scratch/jjyeung/orch_n30/tree_rebuild_w/out/`, mirror trinity-1-18 `/scratch/jjyeung/n30_mirror/tree_rebuild/`); records `E2E_BUILD_tower_read_20261110.md`, `GF1_FUSION_CONNECTOR_20261111.md`, `VLM_E2E_NEXT_LEG_20261110.md`.
- K1 for the scale head and the selector head: tower outputs for 300 training captures at trinity-1-18 `/scratch/jjyeung/k1/run_tower_sam_2` (mirror trinity-3-30 `/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2`), 296 GT rasters (K1_GT_RASTER_REBUILD_20261115.md), split 242 train / 58 held-out by room; E3's fitted rules as the bar (`E3_BACKEND_GEOMETRY_PRICING_20261116.md`: S4+G1 62.9 on distance, GT-scale oracle 66.0).
- Step-544 export: artifact 1d6eeb28...; its arm on dev-S1 is job 170056.

## What to build
1. The hook: a module registered on the model; when the model closes a call it computes the response from tensors of the same forward and writes the response tokens; one `generate` entry; KV cache continues. No text parsing outside the module, no second prompt.
2. One artifact: an export manifest that carries LM, ViT, heads, connector, G3T and (stage 1) SAM 3 by sha256, and a loader that reads nothing else.
3. The scale head: a small head on the own depth head's features and the tower's tokens that predicts the per-clip log scale, trained on GT scale of K1 train captures (and, in the leg, in the pose stream at no extra step cost). Bar on K1 held-out: distance at least S4+G1's 62.9 with the paired interval not below zero; report against the oracle's 66.0.
4. The stage-1 selector head: a small network on tower tensors only (SAM 3 mask tokens and scores, the name's text embedding, own-ViT features pooled in the mask), trained on K1 train candidates with the existing labelling rule (half a candidate's members match the named GT instance at IoU above 0.5). Bar on K1 held-out rooms: AUC within 0.02 and top-1 within 2 points of the logistic selector on the same candidates (B6's kill rule). No alias table: the name goes in as written.
5. Gravity: the own gravity head's output is used as is; delete the guard. Print how many of the 84 dev-S1 captures the old guard refused (11 sealed, 1 reviewed) and what the head-only path answers on them.
6. Parity and price: on job 170056's 636 dev-S1 items with the step-544 export, the new reader against the old runtime, paired by room: camera types must agree within noise (identical calls expected); distance and room report the price of each replacement separately (hook only; plus scale head; plus selector head without aliases; plus no depth cut).

## Tests
CPU: tiny-model end-to-end `generate` with every call type; hook equals the old response session token for token when fed the same tensors; loader refuses a file outside the manifest; EAT-1 (brief 03) static clauses pass. Before any GPU read: the first batch of the real export through the full forward on CPU for one item per call type.

## Do not touch
D0 job 170111, the VSTI read, K1 jobs and `/scratch/jjyeung/k1` (read only; copy what you need over InfiniBand), sealed kits, the registered records. The guard read of brief 01 keeps the old backend by rule.

## Deliver
`out/E2E_READER_READY.md` with the EAT-1 report, the parity table, heads' K1 numbers, hashes; mirror on a second node; STATUS.md; one RESULT event asking for an independent review (another model family; the hook, the loader and the two heads' training code) before the parity read.

## What might go wrong
- SAM 3 inside the call costs 2 to 7 s per name; report seconds per item.
- The selector head may miss parity: then distance is claimed only as a direct answer until brief 05 lands, and the report prices that (the routed gain at stake is +0.96 VSI points strict on the external read, +0.42 [-0.23, +1.08] off the selection scenes).
- Removing aliases and the depth cut may cost up to about 3 task points on absolute distance (0.4 VSI points): measure it, do not restore the table.
