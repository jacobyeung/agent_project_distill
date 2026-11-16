# Records and docs hygiene proposal (2026-11-16, read-only audit)

## Measured state
- distill_design/INDEX.md: 196 lines, 86,802 bytes (~40K tokens for 104 lines; Read caps at 25K tokens, so a new orchestrator cannot open it in one call). 208 files in the folder.
- Two formats: a 3-column table (lines 1-~145, 11-08..11-12) then a bullet list from ~line 146 (11-13..11-16, all of 11-15/16 records). No status column in the bullets; trailing empty `| | |` rows (~45 lines).
- Duplicate file rows (same file listed twice): DEVS1_PREDICTED_MASKS_ROUTE_TABLE_KIT_20261112.md; E2E_BUILD_ground_backend_20261110.md; E2E_BUILD_ground_rows_20261110.md; E2E_BUILD_tower_read_20261110.md.
- Status text is stale: e.g. "C1-r | stopped after m400", "T1 retired", "PLAN 11-09 ... awaiting relay", "MDG-A NO-GO" kept next to MDG-3D "decisive" design; AWS-era rows (ELEVEN_DAY_AWS_PLAN, AWS_CLEAR_AFTER_COPY, AWS_ROOT_CLEAR, AWS_COPYOFF_MANIFEST, OFF_AWS_REPLAN) still look current though USER 11-09 ended AWS jobs.
- docs/ has 62 DISTILLATION_HANDOFF_*.md (09-18 .. 11-10) plus BOOTSTRAP; newest is 20261110_0110Z. The real current state lives in ORCH_STATE_SNAPSHOT_20261116T1054Z.md under distillation_orchestrator_20260918/ (12 snapshots there). CLAUDE.md tells orchestrators to read "newest docs/DISTILLATION_HANDOFF_*" = 6 days stale; that is the wrong entry point. (Snapshot says "tail of 20261115T1811Z, search it, do not read whole" - a second hop.)
- MEMORY.md: 18 KB, ~130 lines, 265 files in the memory folder. Lines carry "READ FIRST" on ~25 entries, so the tag carries no signal.

## Lost-node evidence (orch_cd = trinity-2-18, orch_n28 = trinity-2-28)
INDEX lines with /scratch/jjyeung/orch_cd/ or orch_n28 paths (8): GROUNDING_PLAN_RECONCILED_20261110 (briefs in orch_cd/design_g3d/next_briefs), TRACE_SWARM_REVIEW_20261110 (orch_cd/swarm_ops), TRACE_DIAGNOSIS_CP1_DEVS1_REVSI_20261112 (orch_cd/trace_diag/out/TRACE_DIAG.md), DEVS1_PREDICTED_MASKS_ROUTE_TABLE_KIT_20261112 (orch_cd/devs1_masks/cache_r1/ROUTE_PREDICTED.md), plus "lane ... on trinity-2-18" in ARGON_LABELER, GEMINI_AGENT_HARNESS, CARBON_AGENT_LEVEL, GEMINI_NATIVE_LABELING, GT_CEILING_DECOMPOSITION (patches gt_ceiling/out), VLA_NAV_RUNNER, VLA_LIBERO_KIT, VLA_WHERE_PROVIDER, GRD_SELECTOR_KIT. Records' conclusions survive in the .md; the cited raw outputs are gone. RECOVERY_MAP_2_18_OUTAGE_20261115.md already maps what survives; INDEX does not link it from these rows.
Action: add a column/tag `EVIDENCE: LOST (2-18)` or `PARTIAL`, so no one plans a rerun-from-files that cannot happen; say whether the number is cited (keep) or only reproducible (rebuild plan: NEXT_LEG_REBUILD_PLAN_20261115, K1_GT_RASTER_REBUILD).

## Proposed structure
1. `distill_design/CURRENT_STATE.md` (one page, <= 150 lines, single writer = orchestrator, rewritten not appended, per no-archaeology):
   - Goal + intent (2 lines), live runs/jobs (D0 Orchard 170111, stop rule file), nodes up/down, GPU rules, IO rule pointer.
   - Standing rulings (one line each, link) = replaces reading snapshots 0930Z + 1811Z tail.
   - Open decisions + queued ready-to-launch experiments (ranked).
   - "Do not redo" list (NO-GOs: MDG-A, C1-a-p, C1-b, IF-P0, agg, E3 geometry, T1/T2...).
   - Pointers: INDEX sections, newest snapshot.
   Make CLAUDE.md "Orchestrator only" say: read CURRENT_STATE.md, then newest snapshot only if it differs. Delete the "newest DISTILLATION_HANDOFF" instruction.
2. `INDEX.md` (<= ~100 lines, one table, columns: Topic | File | Status | Verdict (GO/NO-GO/OPEN/DESIGN) | Evidence (OK/PARTIAL/LOST)) grouped by topic:
   A. Results that bind (step-544 reads: OFFICIAL_VSI, REVSI, NATIVE_ROUTED_READ, VSTI_NATIVE, E3, POLICY_AUDIT, REFREEZE_*, D0_*).
   B. Active/next leg (D0_STOP_RULE, D0_ROWS_ADMISSION, D0_V5, A0_AFTER_NATIVE_READ, NEXT_LEG_*, CONTRACTS_REBUILD, NEXT_QUEUE).
   C. Rulings (TRACE_RULING, USER rulings, B6_GROUNDING).
   D. Grounding line (one row per decision; GROUNDING_* 11-10 designs collapse into one row pointing at GROUNDING_PLAN_RECONCILED; MDG rows -> NO-GO).
   E. Pose/geometry (C1 family, POSE_*, G3T, ViPE, GX) - mostly closed.
   F. Traces/data pools (TRACE_POOL_* v2..v3.11 as one chain, ending at TRACE_RULING).
   G. Orchard/infra/tools (ORCHARD_*, ROUTED_READ_*, E2E_BUILD_*, Gemini/Argon/Devin tooling).
   H. VLA/dynamic (not built or CPU-only).
   I. ARCHIVE (superseded/closed): below the main table, one line each, no status prose.
3. Mechanics: a script `tools/index_lint.py` (reads INDEX.md and one directory listing only) that fails on duplicate files, missing files, rows without Status/Verdict, files in the folder not in INDEX (currently 208 files vs ~150 rows: ~15 11-13..16 records have bullets but no status), and long rows (>300 chars). Each new record appends its row through a helper (`index_add.sh topic file status verdict`) instead of ad hoc edits; this ends the table-to-bullet drift and duplicate rows.
4. Status rule: a record's status line changes when the verdict changes (live -> closed), never grows a chain of dates. Cap status at 160 chars; details stay in the record.

## Entries to move to ARCHIVE (superseded, closed, or wrong-era)
- Merged/superseded designs: C1R_G3T_DESIGN_OPUS/ASTRA (-> MERGED), GROUNDING_NAME_TO_3D_ASTRA + GROUNDING_OBJECT_FIRST_SVP (-> PLAN_RECONCILED), TRACE_POOL_V2_READ, V3, V3_READ, V3101_READ, V3101CAM_READ (-> V3102_REREAD -> CP2 read -> TRACE_RULING 11-15), SOTA_PLAN / SOTA_BREAKTHROUGH_PLAN / IMPROVEMENT_REVIEW / OFF_AWS_REPLAN / ELEVEN_DAY_AWS_PLAN (11-09 plans; superseded by MODEL_IMPROVEMENT_PLAN + NEXT_QUEUE_20261115), DRASTIC_ARCHITECTURE (TOWER-0 done), MASK_DECODER_GROUNDING_DESIGN (NO-GO), GX_GEOMETRY_INPUT (gated, never run), POSE_SWEEP_ARMS, C1_PLACEMENT_SWEEP, FRAME_FUSION_PROBE, C1AP, C1_SWITCH, LT5, T2_ROUTED_TRACES_BUILD (stopped), TRAINING_EFFICIENCY_20261108 (EFA/AWS).
- AWS-only tooling: AWS_CLEAR_AFTER_COPY, AWS_ROOT_CLEAR, AWS_COPYOFF_MANIFEST, AWS_COPIES_DEDUP_NEED (AWS ended; keep only the dedup verdict for storage decisions).
- Closed Orchard state-copy trio (ORCHARD_STATE_COPY_*, ORCHARD_STACKED_TMP_MOUNTS): state "closed for 169097" - one row.
- Reads against old baselines: CP1_ROUTING_TABLE, C1_HEAD_EXPORT_HARNESS, E0_* (superseded by step-544 reads).
- Review verdict one-offs (C1_TRAINER_REVIEW, C1_DELTA, C1R_*_REVIEW, MIXED_GATE_REVIEW): fold into their parent design as a line.
Do not move/delete files (no-deletion rule); only move INDEX rows. Add `SUPERSEDED_BY:` to each archived row.

## docs/ handoffs
- 62 handoffs + BOOTSTRAP: successors must skip all (CLAUDE.md already says history). Propose `docs/HANDOFFS_ARCHIVE_README.md` (one file, 10 lines: "do not read; current state = distill_design/CURRENT_STATE.md") and a `docs/archive/` move by the git owner only (path change touches a Git-tracked tree; needs serialized commit, not by lane). Results docs (RESULTS_*, MATCHED_PAIR_*, *_RESULT.md, ERROR_ANALYSIS_*) are Sept-era: label as "September; superseded by distill_design" in a docs/README.md. VERIFICATION.md stays (referenced by AGENTS.md).
- Snapshots (12 in distillation_orchestrator_20260918/): keep only the newest as working state; CURRENT_STATE replaces the "snapshot + tail of older snapshot + 0930Z standing rulings" 3-hop chain. Fold the standing rulings and "do not redo" list out of 20261115T0930Z into CURRENT_STATE once.

## MEMORY.md consolidation (18 KB -> target ~6 KB, <= 40 lines; details stay in the linked files)
Merge candidates (each group -> one line):
- Executors: codex-default-executor, devin-first-every-lane, index-executors-carriers, codex-token-economy (11-12 "dispatch Codex only when needed"), lane-command: three lines say who carries what; CLAUDE.md says Codex default, memory says Astra via Codex / Opus via Devin. Keep one line.
- AWS (5 lines): aws-down-until-user-says, index-aws-reference, aws-gpu-waste-not-allowed, aws-pull-under-100gb-approved, "AWS ends 11-19" in goal line: AWS runs nothing; keep one ("no AWS jobs") + move reference to index.
- GPU priority/scheduling: trinity-gpu-priority-rules, pack-single-gpu-jobs, higher-signal-takes-gpus, spare-gpus-to-data-generation (IO cap 18), trace-supervision-priority, stop-idle-watchers, no-compute-waste: one "GPU policy" line.
- No-control/no-replicate (4): no-seed-replicates, no-more-controls, uniqueness-not-replication, stack-best-then-ablate -> one line. Note "Higher signal takes GPUs" (stop weaker run) and "keep building rounds: run to completion" pull opposite ways; state precedence once.
- IO (6): io-governor (11-15), IO rates 11-12 (download 20 / copies 10 MB/s), spare-gpus IO cap 18, lesson-rebuilds, reads-no-ask, no-grep-NFS: these conflict with the admins' rules in the global CLAUDE.md (20 MB/s total, 8/4 MB/s copies). Replace by one line pointing at the governor and global rules; remove 10/18/20 variants. This is the highest-risk contradiction.
- Orchard (orchard-queue-facts, lesson-orchard-fs-can-fill, d0-leg-running): one line + D0 state moves to CURRENT_STATE (d0-leg-running is state, not memory).
- Design/process lessons (lessons-process-rules, experiment-design-lessons, prelaunch checklist, launch-first-check-after, lesson-launch-kit, lessons-launch-night, push-back, review-decision-code, build-experiments-first (also in AGENTS.md - drop from memory)): one "Launch discipline" line.
- Result lines (about 20: oracle bottleneck, head-backed programs, pose limit, presence, devs1 baseline/route table, f17 vs parent, ReVSI step544, VSI step544, routed read, native read, E3, IF-P0, LEG-S1 m100): not memory; move to CURRENT_STATE "results that bind" (one line each, link to design record). Mark superseded ones: oracle 10-27, toolprog 11-07, MDG-A init, route table 11-12 (parent) are overtaken by step-544 reads.
- Stale/overtaken: "Rotate ~300K tokens" vs unlimited-context sessions; "SOTA bars ~9B" and "Closed-model bars" (merge); "Run-check cadence" lanes 1 min/5 min vs CLAUDE.md orchestrator ~15 min vs "routine polling every 10 min": pick one in AGENTS.md; "Eval frames unrestricted" vs "Eval frame layout must match training": same-topic pair, merge; "Reconstruct dense then subsample" and "Drastic architecture OK" and "No harness end-to-end": merge as "architecture constraints".
- Remove "READ FIRST" from all but <= 5 lines (cluster safety, executor, launch policy, current goal, CURRENT_STATE pointer).
- Add top line: `Entry point: distill_design/CURRENT_STATE.md`.

## Savings
A new orchestrator now reads: CLAUDE.md chain + 18 KB memory + 87 KB INDEX + 28 KB snapshot + older snapshot tail (~60K tokens before any work, with a stale handoff pointer). After: CLAUDE.md chain + 6 KB memory + ~6 KB CURRENT_STATE + 8 KB INDEX top sections (~15K tokens). Also every lane brief that says "read INDEX.md first" stops costing ~40K tokens per lane.
