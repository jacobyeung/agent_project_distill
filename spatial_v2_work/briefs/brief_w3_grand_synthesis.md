# Lane: w3_grand_synthesis (Wave-3 Final Design Record & Actionable Master Plan)

## Mission
Synthesize ALL Wave-1 ground-truth reports, ALL 9 Wave-2 blue-sky blueprints, AND the independent hostile **Codex Astra** review (`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w3_codex_astra_critique.md`) into our canonical, permanent design record saved to:
1. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/SPATIAL_V2_BLUESKY_MASTER_PLAN_20261128.md` (working copy)
2. `/data2/jjyeung/agent_project_data/distill_design/SPATIAL_V2_BLUESKY_MASTER_PLAN_20261128.md` (permanent outside-`/scratch` design record per USER 2026-11-08 — remember do NOT touch `INDEX.md` yet; we'll append one clean row cleanly).

## Inputs to Read (Exact Paths Only)
- `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w3_codex_astra_critique.md` (Codex Astra's hostile review — address EVERY verified critique and state where we accept, modify, or overrule with evidence!)
- All 9 Wave-2 reports (`w2_*.md`) and Wave-1 summaries (`w1_student_state.md`, `w1_compute_inventory.md`, `w1_split_breakthroughs.md`, `w1_vla_bridge.md`) under `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/`.

## Hard Rules
- Follow the design-record schema (USER 2026-11-08): **Question, Answer, Evidence (with exact numbers/citations), Rejected/Deferred Options (and why), Risks & Failure Modes, Decisive Kill-Tests (with exact GO/NO-GO bars & GPU budgets), Status**.
- Follow `no-archaeology` and `williams-clarity`: active prose, zero fluff, crisp tables, no pleasantries.
- Do NOT run git, delete files, or scan NFS.

## Required Sections (Max ~280 lines — dense, executable, zero bloat)
1. **North-Star Unified Architecture ("Spatial-V2": Dual-Speed Depth+Pose-Anchored 4D Spatial & VLA Foundation Model):** Collapse the winning pieces from all 9 Wave-2 lanes + Codex Astra's adjudication into ONE clean, non-redundant architecture showing exact information flow from pixels -> geometry/depth/pose/4D-flow/3D-slots -> trunk (`taps 16, 24, -1`) -> System-1 30 Hz VLA action head AND System-2 closed-loop epistemic spatial reasoner.
2. **Adjudication of Codex Astra's Critiques:** Explicit table of every Codex Astra blocker/concern -> our ruling (`ACCEPTED`, `MODIFIED`, `DEFERRED`, `OVERRULED + why`).
3. **Lineage Fork & Compute Mobilization Plan (Hours 0–72 & Days 4–14):** Exact GPU allocation across Orchard (`4 advanced + 1 general + preempt`), `trinity-0-13` (`0,2` unwrapped + `6`), `trinity-2-28` (`4..7` `vnice`), `trinity-0-18` (`4..7` `vnice`), and 24/7 Gemini API key (`Neon`/`Carbon`/`Argon`), respecting shared 30 MB/s NFS IO + Nov-29/Dec-01 preservation.
4. **Top 8 Ranked Kill-Tests & Execution Queue (Ready-to-Dispatch Brief Specs):** Exact Tier-0 (launch TODAY), Tier-1 (48h build-ahead), and Tier-2 (moonshots gated on Tier-0/1) with owner type, host/GPUs, exact GO/NO-GO bars, and expected points on VSI-Bench, ReVSI, VSTI, Dynamic/Ego-Exo/VQ3D, LIBERO-Spatial/+Cam, and R2R-CE.
5. **What Was Rejected or Deferred (and Why).**

Print a crisp <=20-line executive summary to stdout when finished.
