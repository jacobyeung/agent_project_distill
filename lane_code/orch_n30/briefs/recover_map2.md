# Lane recover_map2 (runs on trinity-3-30): what of the distillation work survives outside trinity-2-18 and trinity-2-28, and how each queued item restarts

Lane folder: `/scratch/jjyeung/orch_n30/recover_map2` on trinity-3-30. Events folder: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/recover_map2/`. First read `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md` and obey it. This lane is read-only outside its folder, its events folder and the one record named below. It uses no GPU and starts no copy.

## Why
trinity-2-18 went down at 2026-11-15T10:00Z. It held the distillation orchestrator, every lane folder (`/scratch/jjyeung/orch_cd/...` on that node), every kit, the trainer tree, the built rows and the accepted read packets. trinity-2-28, where the work restarted, stopped accepting logins at about 16:15Z; it held only tools and 40 minutes of lane work. The user ruled that this work moves to other nodes instead of waiting. The orchestrator needs to know, for each queued experiment and build, which inputs survive elsewhere and what the cheapest restart is.

## Read first (bounded reads)
- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/ORCH_STATE_SNAPSHOT_20261115T0930Z.md` (state 30 minutes before the first outage; 115 lines; lines 33 to 60 and 77 to 101 matter most).
- `/data2/jjyeung/agent_project_data/distill_design/NEXT_QUEUE_20261115.md` (the queue and its item names).
- `/data2/jjyeung/agent_project_data/distill_design/INDEX.md` lines 107 to 173 for the records of 11-11 to 11-15; open a record only when an item needs it.

## Items to map
1. Official VSI-Bench direct read of the LEG-S1 step-544 export (kit `official544_direct6_two_roots.tar`, 90c2c742) and the ReVSI direct kit (6a285edd).
2. Native routed read on dev-S1: candidate C7 (`evalx/work/milestone/native_package_s24_07`), the family of pilot 9 (ebe307cf4, Orchard job 169792), reader b8ebab38, launcher 555eb739, the mask cache, the step-544 export.
3. K1 grounding kill test (kit of lane k1_build; staging on trinity-1-18 `/scratch/jjyeung/k1`).
4. Re-freeze steps P2 to P8 (CPU re-selection inputs, the dev-S1 route-table data, the frozen-setting files under `official_reads/`).
5. The stacked seal: trainer tree `rs_tree/work/tree_r1` (base: LEG-S1 source 37845077, kit 07ca49df, seal 38917ea5), rows `rs_rows/out/rows_r3` (208,318 rows) and `rs_rows/work/trace_grammar.py`, the `rs_contracts` R2 patches, `rs_cover`, `dx_census`, `b11_native`, `b6_build`, `o3_cache`, the pool revision 2 patch, the label_247 outputs.
6. The LEG-S1 state: run root on Orchard `/home/jjyeung/okit/r/5da50f2b` (slot A, step 544), the stop export `469ddece_mstop.tar`, the step 100/200/400/544 exports, and any GCS copy.
7. The continuation packet and checker (two archives sit in `distill_design/`).
8. Kits built ahead: geometry bake-off (seal 0ef8fe08), own-grounding kits, the VLA kits (LIBERO, navigation, heads), the mixture and form-flag tree (seal 5b1e1862), the dense-frame material.
9. Evidence with sole copies on 2-18: the accepted read packets (`evalx/work/milestone/reports/step{100,200,400,544}_*`), `leg_s1_review/`, the official routed read of 11-13 (`official_reads/`).
10. The IO governor code (`/scratch/jjyeung/io_governor` on 2-18): does a copy exist elsewhere (trinity-3-30 has a folder `/scratch/jjyeung/io_governor`)? This belongs to the main orchestrator; report only.

## Places to look (each bounded)
- trinity-3-30's own local disk first, since you run here: under `/scratch/jjyeung`, the folders `orch_cd`, `distill_evac_finals`, `finals_secure`, `devin_trace_import_2_18_v1`, `devin_trace_import_2_18_hydrated_v2`, `devin_trace_refresh_2_18_v1`, `devin_trace_2_18_hydration_work_v1`, `devin_trace_archive`, `mind_archive`, `vla_pilot`, `vla_pilot_orch`, `g3t_scale_work`, `scannet_poses_full`, `mp3d_e0_models`, `io_governor`, `codex_home_trinity-3-30`, and the `mover_*` folders with their manifests. Use `ls`, `du -s` on single folders and `find -maxdepth 3`; never walk a whole tree. The imported Devin traces from 2-18 matter most: say which lanes and dates they cover and whether a lane's written files (patches, kits, scripts) can be replayed from them.
- trinity-0-13 and trinity-0-28: one batched ssh each, listing `/scratch/jjyeung` to depth 2, `/dev/shm/jjyeung*` and `/dev/shm/mdg*` to depth 1, and `df -h /scratch`. Do not ssh to trinity-1-18 or to Orchard: lane k1_ops3 writes `SCRATCH_1_18_LISTING.txt` and lane evalx27 writes `ORCHARD_INVENTORY.md` into their events folders (`.../orch_n30/events/k1_ops3/`, `.../orch_n30/events/evalx27/`); read those when they appear and say so if they have not appeared by the time you finish.
- NFS, by single-directory listings and named-file reads only, at most about 300 file opens in all: `/data2/jjyeung/agent_project_data/distill_design/` (archives beside the records), `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/`, `/data2/jjyeung/agent_project_data/lanes/` (top level), the mover's thread `/data3/jjyeung/mover_20261111/DISCUSSION.md` (search that one file for `orch_cd` and `2-18`), `/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/` (top-level listing), Codex rollouts under `/home/jjyeung/.codex/sessions/2026/11/{13,14,15}` (list names and sizes; read at most the first 2,000 bytes of a file, and of at most 60 files), the Devin store `/data2/jjyeung/cli_agents/home` (top two levels only).
- GCS: bucket names appear in `distill_design/LEGS1_STATE_COPY_TO_GCS_20261113.md` and `AWS_COPIES_DEDUP_NEED_20261109.md`. List only the prefixes those records name with `gsutil ls`, if it is installed and authenticated on this node; if not, say so and move on.

## Deliverables
1. Within 40 minutes: a RESULT event `first_pass` with the items that can restart now and from where.
2. The record `/data2/jjyeung/agent_project_data/distill_design/RECOVERY_MAP_2_18_OUTAGE_20261115.md` plus its line in `INDEX.md`. One table row per item: needed inputs; surviving copy (host, absolute path, size); verdict (`restart now`, `rebuild`, or `only on 2-18`); the cheapest rebuild route with the base it starts from and a rough effort; what is lost if 2-18 never returns. Mark every line you did not verify as unverified.
3. A final RESULT event that names the record and gives the five restarts you would do first, ranked by benchmark value per hour of work.

Stop when the record is complete. Do not start any rebuild.
