# Lookup: define R0's three exclusion checks (lever5, read-only inventory)

You run on trinity-2-28 for lane lever5. Check `hostname -s` prints trinity-2-28 (stop if `trinity`).

## Rules (binding)
- /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md bind you.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states. For you: NO copy or stream, NO ssh, NO Orchard, NO Git, NO GPU, no deletion, no write outside /scratch/jjyeung/orch_n30/lever5/r0chk.
- No recursive grep/find/du/ls -R on /home or /data*. Read named files; `ls` single directories; `grep` inside one named file is fine; read big files in bounded parts (head/sed -n ranges). Use `stat -c %s` on named files for sizes; for a directory of many files, estimate from `ls -l` of that one directory (non-recursive), never du.
- Read at most ~50 files in total; this is an inventory, not an analysis.

## Context
D = /data2/jjyeung/agent_project_data/distill_design. D/R0_RESERVE_SCENES_20261116.md (read it first) lists three open gaps of the R0 reserve (rooms no checkpoint has seen):
1. Stream scene lists: separate scene lists of the T0 and CP1 training streams were not found; a found list is to be run through `test_exclusion.py` (on trinity-1-18 /scratch/jjyeung/orch_n30/b10_reserve/code/test_exclusion.py; a copy may be inside the archive or the mirror named in that record's Status). The plan record D/ROUTED_READER_LEVER_PLAN_20261120.md (section "Rank 4 (WORD): legality", open item) says the lists are fetched "from their AWS receipts".
2. Mesh-similarity scan: the 98 R0-dev ScanNet++ meshes against trained ScanNet++ scenes, first PLY headers and bounding boxes, then full meshes only for near matches.
3. MMSI-Video clip mapping: BENCH v2 (3119aa4a) records 134 MMSI-Video clips without scene mappings; a phash pass over ~6 frames per recording.
Use D/INDEX.md (grep it for T0, CP1, stream, receipt, BENCH, MMSI, scannetpp, mesh) to find the records that name these inputs; follow named paths only.

## For each check, find and report
- What it compares (which list against which list; what counts as a collision).
- Its inputs and exactly where they sit (path, host, or AWS/GCS URI and the receipt file naming it), with sizes where you can stat them. For check 1: does a T0 / CP1 stream scene list (or a manifest from which scene ids follow) exist anywhere reachable from Trinity without AWS (e.g. a receipt or manifest copied to /data2 or /data3)? If only on AWS/GCS, name the URI and size.
- Bytes it would read from /data* or /home (estimate, with how you estimated), and how long it would take (CPU; the governed rate is 8 MB/s for reads).
- Whether check 1 reads under 20 MB from NFS.

## Deliverable
Write /scratch/jjyeung/orch_n30/lever5/r0chk/R0_CHECKS.md (<= 60 lines; one section per check with the fields above, plus a line of unknowns). Final message: the same in brief, with the paths.
