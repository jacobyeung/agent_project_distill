# Lane: w2_api_data_flywheel (Wave-2 Blue-Sky Deep Design — Unlimited-API Gemini 4D Trace, Counterfactual & Embodied Data Factory)

## Mission
Design a **24/7 Automated Spatial + Embodied Data & Trace Factory** that maximizes our **unlimited Google Gemini API key (`gemini-4-neon`, `gemini-4-carbon`, `gemini-4-argon`, `gemini-4-hydrogen`, `gemini-3.8-flash`)** combined with our exact 3D/4D reconstruction tools (`DA3`, `ViPE`, `Point4D`, `CoTracker3`, `SAM3`) to produce **1M+ ultra-high-signal, leak-free, prior-breaking training rows** that crush BOTH spatial benchmarks (VSI/ReVSI/VSTI/MMSI/DSI/Ego-Exo4D/VQ3D) AND VLA transfer!

## Ground-Truth Inputs to Read First (Exact Paths Only)
1. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_cleansheet_vla_data.md`
2. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_split_breakthroughs.md`
3. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_vla_bridge.md`
4. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_compute_inventory.md`
5. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_student_state.md` (if present)

## Shared Cluster IO Rule (MANDATORY)
We share a 30 MB/s NFS/internet cap with `trinity-0-13`! Every data-factory pipeline MUST run on node-local `/scratch` (1.8 TB free on `trinity-2-28`!), use inline frame JPEGs (never bloat the 20.5 GB Gemini File API cap!), and stream finished tar.zst archives over `.ib` or throttled `io_governor` (`<=4 MB/s` write to `/data3`).

## Deep Design Questions You Must Solve
1. **Six High-Leverage API Trace Streams (Ranked by Points-Per-Day & VLA Impact):**
   - **Stream 1 — SPLIT-Style Closed-Loop Epistemic Traces on Real Noisy Head Outputs:** Run our current student heads (and DA3/ViPE/Point4D) on held-out-clean training rooms (`ScanNet`, `ScanNet++`, `ARKit`, `MP3D`, `R0-rl`) to capture REAL failure residuals, then have `Neon`+`Carbon` synthesize self-verifying multi-turn traces that catch errors, switch views/phrases, and compute exact verified answers (verified by our deterministic 3D solver + `Argon+Carbon` agreement filter!).
   - **Stream 2 — Prior-Breaking Anti-Overfitting Suite (Crushing the VSI→ReVSI 20-pt Cliff):** Reversed/mirrored/rotated/sub-sampled clips, focal-crop parallax warps, perspective-flipped ("facing away / opposite direction / standing at object X") questions, open-ended paraphrased wordings (50+ phrasings per type, eliminating wording-induced call skips!), and large-set counting / multi-instance identity traps (`X6`-hard!).
   - **Stream 3 — Cross-Camera & Tabletop Embodied 4D Corpus (Bridging Indoor Rooms -> Robot VLAs):** Mining `DROID` / `OXE` / `BridgeV2` / `Ego-Exo4D` / `Ego4D` / `HD-EPIC` with `ViPE` + `DA3` + `CoTracker3` + `Neon/Carbon` for: (i) wide-baseline `wrist ↔ third-person` camera pose & 3D reach QA, (ii) millimeter grasp clearance / swept-volume collision / occlusion QA, (iii) ego-motion-decoupled human hand `MANO → SE(3)` pinch trajectories & articulated drawer/door screw axes!
   - **Stream 4 — Dynamic 4D & Long-Horizon Streaming Traces:** Point4D / CoTracker3 + Neon traces for moving-object velocity/relative-motion/collision (`DSI`/`ReSTI` without any benchmark room contamination!) and streaming loop-closed 3D memory queries (`VQ3D`/`HD-EPIC`!).
   - **Stream 5 — Adversarial Red-Teaming Flywheel (Self-Play Curriculum):** `Neon` generates spatial questions specifically targeting our current student's live error buckets; exact 3D solver certifies ground truth; `Carbon` verifies zero visual ambiguity; automatically feeds the next SFT/RL leg!
   - **Stream 6 — Procedural Synthetic Specular/Cluttered Tabletop 3D Data:** `Neon`-authored procedural 3D scenes (glass, metal, occlusions, articulated cabinets, robot grippers) with exact metric depth, pose, 3D OBBs, and visibility!
2. **Exact Leak-Free Governance & Quality Gates:** Room-keyed exclusion asserts (`BENCH v2` + `R0-dev` + `K1-heldout` + `ReSTI ScanNet`!), deterministic Python geometry recomputation (`0` arithmetic errors!), `Argon+Carbon` cross-family visual verification (`96.9%` accuracy), and inline-JPEG API batching throughput math (how many verified rows/hour we can produce starting TONIGHT on `trinity-2-28`!).
3. **Immediate Tonight-Launchable Pilot (Phase 0, 24h):** Exact 10k-row starter batch we can spin up with API Neon/Carbon TONIGHT using frames already on local `/scratch` / Trinity without triggering heavy NFS IO!

## Deliverable
Write a crisp, deeply actionable blueprint (max ~260 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_api_data_flywheel.md`
Print a concise <=18-line summary to stdout.
