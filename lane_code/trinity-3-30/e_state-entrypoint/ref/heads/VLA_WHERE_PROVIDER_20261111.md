# VLA where-provider (U1 and NU geometry), schema v2 CPU build (lane vla_where, 2026-11-11)

## Question
What code turns the frozen student's own presence and pointing, SAM 3's masks and G3T's depth and pose into U1's "where" input (a printed line plus 18 numbers per entity) and into NU's click-to-motion layer, and does it work before any GPU run? Contract: `/scratch/jjyeung/orch_cd/vla_design_review/VLA_SCHEMA.md` (`vla_schema_v2`) sections 0, 5, 6, 8.2, 9, 12; design `VLA_ACTION_HEAD_DESIGN_20261111.md` §2.1-2.3.

## Answer
- **Where it lives:** `/scratch/jjyeung/orch_cd/vla_where/work/vla_where/` (package `vla_where/`, `tests/`, `scripts/`; `source env.sh`). The archive and its sha256 are under `/scratch/jjyeung/orch_cd/vla_where/out/`.
- **Provider:** `WhereProvider.where(obs)` reads only the whitelisted `Observation` (instruction, t, agentview at t, wrist at t and at t-8/-16/-32, raw proprio at those steps) and the hand-eye constant. It runs one G3T call on [wrist_t, agent_t, wrist history]. Each view needs P(yes) >= tau, a student point and a SAM 3 mask that contains the point. The mask is eroded by 2 px and lifted with confident G3T depth. The cross-view rule tests mask membership, and the scale comes from proprio and the hand-eye fit. With a scale, X_wrist = s·M·X_g, because G3T frames are mirrored on LIBERO's dataset images. The output is the schema 5.2 record (`[2, 18]` fp32, mask, reason codes) and the 5.4 line, formatted from float64 values.
- **ViewSetG3T:** the pinned tower (`FrozenG3TTower._load`, dense_frames 32, depth_chunk_size 8, bf16) runs on any number of views, with convert's per-view camera checks. A failed check gives `no_lift` for the chunk. It returns T_view0<-view, K_g, FoV, pixel-centre depth and confidence, gravity up, and the 51 x 51 endpoint grids for T-11. `pose9` builds production's inverse rows.
- **Student and SAM 3:** the student uses verify_kit's V1 yes/no prompt (P(yes) from the first-token yes/no mass) and the native single-image pointing prompt (`hrp_reread`), through native `generate` on `full_weights`. SAM 3 runs `Sam3Tower.encode` once per chunk and then `detect(noun)`.
- **Phrase table v2:** 40 LIBERO instructions, each entity a phrase plus a SAM 3 noun.
- **Dropout and evaluation conditions:** a sha256 draw withholds a chunk (seed 17, rate 0.2). Generators exist for `withheld`, `shuffled`, `scale_k` and `gt_where`.
- **Cache:** one entry per training frame, under the schema 9 key (T-7's digest `8e2cc39e...b2a6`). Writes are resumable and atomic, the manifest binds one provider, and `lookup` can re-verify a key.
- **Online form:** a per-chunk call with a JSONL record log, served over an optional Unix socket.
- **NU:** `ClickTranslator.decide(text, obs)` reads only schema 8.4's observation and parses vla_heads' `nav_grammar_v1`, vendored by sha256. It lifts with `floor_plane` by default, with `g3t_depth` (floor fit) as a check, and receives commanded metres through `executed_commanded`.

## Tests (CPU)
`cd /scratch/jjyeung/orch_cd/vla_where/work/vla_where && source env.sh && python -m pytest tests -q`: 68 pass in about 16 s.
- **Conformance:**
  - T-1: examples 1-3 run from `schema_examples.scene_inputs` and `points_for` (sha-pinned import). Vectors match within 4.9e-7, lines byte for byte, and the stated pixel counts and cross-view pixels match.
  - T-3: example 4, including the above-horizon click and the `floor_depth_g3t` fit (129,540 inliers, z 2.018927). Actions match navrun's built-in lift.
  - T-7: the key and the digest reproduce, and changing any of 60+ leaves changes the key.
  - T-10: the whitelist holds by construction. An image-only provider (colour stub plus the tree's tiny real G3T) gives bitwise-identical records under hidden-state changes, and the navigation backend rejects any non-whitelisted key.
  - T-11 (CPU fp32 tier on the tiny tower): pose9 matches within 1e-6, and depth and confidence within 1e-5. An inverted pose fails.
- **Units:** the lift, erosion, extents, the mirror and fx < 0, scale rules (including non-finite skips), the hand-eye fit and pin, presence, point, selection, tie, behind and range rules, the camera-check failure, dropout, conditions, the cache, the socket, the grammar and the pre-check.

## Findings on vla_libero's first LIBERO-Spatial replays (`vla_libero/out/renders_v2`, 4 episodes, every 4th sim state; CPU, GT-reading stubs)
- **The proprio and hand-eye scale is exact on real kinematics.** With vla_libero's `hand_eye.json` (sha256 ec5f9d04...), s / s_GT - 1 is at most 2.4e-7 over 28 records.
- **P-2 catches the mirror convention.** With mirrored G3T-like frames, X_wrist = s·M·X_g gives a median error of 0.6 mm. Dropping M fails P-2's 3 cm rule.
- **The cross-view rule exempts occluded projections (`cross_view_occlusion_rel: 0.05`, schema 6.3 step 8 and the code default).** With GT perception the strict rule rejects 63% of correct plate lifts in the placing phase (27 of 43 on vla_libero's renders_v2), because the carried bowl hides the plate in the wrist view. The exemption recovers all 30 strict rejections of correct lifts and accepts no more wrong lifts (5.9% strict and 5.9% exempt, n = 3,173 wrong lifts from the wrong-instance, cross-noun distractor and noisy-geometry stubs). r = 0.02 adds 0.7 points of wrong accepts on the target; r = 0.10 recovers only 80%. Script: `scripts/crossview_occlusion.py`; results: lane `out/occlusion/full_20261111/`; test: `tests/test_occlusion_exemption.py`.
