# Build brief 07: official read kit for VSI-Bench (5,130) and ReVSI (999), eight and seven categories, export as a parameter

Builder: Claude Opus, high effort. Written by lane queue_synth, 2026-11-16. No official routed read runs before the re-freeze file of step P8 exists; this kit must be ready before it.

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). No Git, no deletion, no GPU, no Orchard submission without an ORCH GO naming the job. Never open a benchmark answer or score while building; tests use fixtures. Lane folder `/scratch/jjyeung/orch_n30/official_kit`; events `B/events/official_kit/`.

## Why
Step 544 has only partial official numbers: six direct VSI-Bench tasks (68.77) and five direct ReVSI categories (64.94). Absolute distance and room size were not read, because the student answers them through calls. So no eight-task or seven-category number of this lineage exists, and none can be set against 75.05 or 57.5. Two readers will exist: the registered harness backend (after P8) and the end-to-end reader of brief 04. The kit takes the reader as a parameter and labels every number with it.

## Inputs
- Accepted direct kits and their returns: VSI-Bench kit f42aa1a4 (job 170008; trinity-1-3 `/scratch/jjyeung/orch_n30/evalx27/work/kit/build/a8acc277397/`), ReVSI kit ea1a1b2d (job 170037; `.../work/kit_revsi/build/a348bc58686/`); records `OFFICIAL_VSI_DIRECT_STEP544_20261115.md`, `REVSI_DIRECT_STEP544_20261115.md` (frame path: PyAV, 32 floor-uniform anchors each duplicated; ReVSI media at Orchard `okh7/313db5a47f11ff0c/`).
- Native serving: kit C8r (`B/events/native_r2/c8r_kit/`), the VSTI kit V1c (`B/events/native_r4/STATUS.md`) for in-job tower and scale preparation on a benchmark's own frames.
- Rules: `REFREEZE_PREREGISTRATION_20261115.md` (P1 to P8, fallback section: strict arm primary), amendments 1 to 3 (amendment 3: no benchmark score chooses a route; room calls of step 544 and D0 exports are served as the primary arm with the stated label; the unserved arm is secondary), `B6_GROUNDING_DESIGN_20261115.md` answer 2 (the selector fitted on VSTI and ReVSI rooms may not serve a ReVSI or VSTI mask read; the K1 refit must).
- External read's caches for VSI-Bench scenes: trinity-1-18 `/scratch/jjyeung/vsi_recache` (completeness unverified; under the end-to-end reader no cache is used for the claimed run).

## What to build
1. One kit, three parameters: benchmark (VSI-Bench 5,130 or ReVSI official999 tier 32), export (`.done` record or the step-544 artifact), reader (direct-only; harness backend named by the P8 freeze file's sha256; end-to-end reader of brief 04).
2. Geometry and masks for the benchmark's own frames computed inside the job by the reader (tower pass on the 288 or 261 videos); no file from a different frame path.
3. Reports: official aggregation (eight tasks, direction as the mean of its three subtypes; seven ReVSI categories as equal means of subtypes); scene bootstrap, 10,000 draws; per type the call rate, refusals, forced closes; distance and room by asked unit; the first line of every report names the reader and says whether EAT-1 passed for it. A harness-served number carries the words "harness-served, not an end-to-end result".
4. A direct-only re-bind for a D0 export (the six and five direct categories), so the export the init rule selects is read once on the same items as step 544; no milestone other than the selected one is read on official items.

## Tests
Scorer check: reproduce 68.77 and 64.94 from the accepted returns; fixture runs of every reader mode on a tiny model; whole-worker CPU rehearsal with the production CONFIG; an in-job proof of ten dev-S1 items against job 170056 before any official item is decoded; denominators equal 5,130 and 999 with unread types impossible.

## Do not touch
D0 job 170111, the VSTI read and its pool, K1 and its pool, the registered records, any benchmark label file outside the scorer.

## Deliver
`out/OFFICIAL_KIT_READY.md`, hashes, time estimates (expect 3 to 6 H100-hours for VSI-Bench with calls served and 1 to 2 for ReVSI), mirror on a second node, STATUS.md, one RESULT event. Review: one independent refute review (another model family) of aggregation, reader labelling and the freeze binding; this kit touches scoring, so the review is required.
