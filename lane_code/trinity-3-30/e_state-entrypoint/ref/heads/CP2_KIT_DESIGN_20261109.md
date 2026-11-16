# CP2 kit design (p3_build5, 2026-11-09)

Status: BUILDING (14:30Z). CP2 warm-starts from CP1's strongest export (or T0 m1200, decided by reads) on its own AWS root and must be READY TO LAUNCH, with every rank's first batch through the full forward on CPU, before CP1 ends (~Tue 16:00Z at CP1's pace).

## Question
What does CP2 change relative to CP1 (job 129814: trainer c1mix e6456bc, config B+C, VQA vxm, route table = 3 camera types routed, VSI types direct), and how is each change built and checked?

## Contents and how each is built
| Item | Source / owner | Trainer change (branch cp2-20261109) | Status |
|---|---|---|---|
| VQA at 64 nested frames (ORCH 1054Z) | Codex N64 builds 64-frame rows + a k6tk bundle on AWS CPU from the room-5x VQA receipt and k1208 | 4fe48b9 + 7ab550d: VQA rows with `anchor_slots` hold up to 64 duplicate-layout viewpoints; markers 1..64; carriers only after the 32 anchors; `nested_indices` is the one shared rule | trainer done, review GO; rows building |
| Evaluator parity at 64 | evalx reads CP2 through the trainer encode (aws_v), rows built with `nested_indices` | none | agreed (evalx 1408Z) |
| Tool-mode prompt flag (dual mode) | config `tool_mode_flag` | c3a74ec: routed rows get the flag line before the question; with the flag, VQA keeps direct rows of routed types; policy `cp2-tool-mode-20261109` routes the ten CP2 types | done, review GO; flag text to fix in the kit |
| Routed rows v3.11 | derivgen6 cp2_delivery (96,732 rows, 356 scenes) | c422b95: calculator v3 vendored (9533292e); pre-3.11 rows rerender with the v2 copy | asked derivgen6 to ship rows + RGB to AWS |
| Pose mix: CP1 mix + ARKit sensor depth + A4 rooms (ORCH 1407Z option b) | A3 ARKit subset 15,000 rows/1,403 captures (ap/3543aef8/s/p3), MP3D A4-train 5,240 (s/pm), scans_test r_s 392, ScanNet++ r_spp 3,432; division A4 | d61d4ed: clips admitted under a division-pinned mix when every clip recording is a train scene; ancestor divisions along a consistent chain (A1 -> A3 -> A4). 713bd30: A4 schemas | review GO (d61d4ed); 713bd30 in review; draft spec out/cp2/CP2_POSE_MIX_DRAFT.json |
| Room size rows, ScanNet++/ARKit, >= 1% of VQA | Codex ROOMX (alpha shape, reproduces 24/24 existing labels) | none | ARKit rows building; ScanNet++ meshes only on Trinity (not pulled) |
| 1,208 terminating traces | ap/6e81a204/k1208.jsonl.gz | none | joins the VQA build |
| Pointing: uniqueness + allow-listed scene-absent negatives | streams2: pc1 + pc3 + sa_122731 | none | requested |
| Frozen G3T connector (GX GO); GXP fusion only if GXP-mix beats CP1 | gx_build gxp-mix | merge pending | asked gx_build for the commit and step cost |
| Camera types decode with G3T x s | evalx harness | none | record in the decode spec |

## Findings that shaped the design
- CP1's pose mix gives the depth head no ARKit depth: C1 clips carry zero depth masks and A2's ARKit rows are rejected by their frame prefix, so all 11.6M depth points come from ScanNet/ScanNet++ mesh raycasts. This explains T0 reading ARKit depth 1.21x long. A3 holds 112,240 ARKit rows with sensor depth (mm/1000, optical axis) from 1,403 training captures.
- Only 297 of CP1's 387 room rows train (90 are ReSTI-held); 5x copies restore T0's 1.0% room share (CP1 FAIL path, root ap/15e5748e).

## Rejected
- Training CP2 VQA at 32 frames and evaluating at 64: ORCH ruled train-at-64 for train/test match.
- Pose option (a), A2 + A3 without the C1 clips: drops 25,600 teacher clips, and T1's similar mix read rotation +2.3 deg worse than T0 at m600.
- Spread-64 encoding without carriers: differs from every other CP1/CP2 stream; kept only as evalx's disclosed fast screen.
- Global weights.vqa 2.0 for the room gap (loss_doctor 1331Z).
