# Build GTC-B: add arm b (t_big) to the GTC kit (lane lever6, trinity-2-28)

You are a build subagent of lane lever6. Check `hostname -s` prints trinity-2-28; stop if it prints `trinity`.

## Rules (binding)
- /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md bind you.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states; a dropped Orchard connection is retried once after 60 s. For you: NO stream, NO ssh, NO Orchard call, NO Git, NO GPU (CUDA_VISIBLE_DEVICES=''), no deletion.
- No recursive grep/find/du/ls -R on /home or /data*. Write only under /scratch/jjyeung/orch_n30/lever6/gtcb. lever6/gtc (kit, out, SHA256SUMS_GTC) is read-only: copy the kit to lever6/gtcb/kit and work on the copy. Python as the GTC kit uses (p1cpu for CPU code, sam3_capretry_native_v1 for the tracker), nice -n 10, threads <= 8.
- You may read lever6/gtc/out/RELIFT_GTC.json only to reuse cells a, e, t, s for the paired b - t and pairing checks; do not print or report any value of b (b does not exist yet).

## Registration (binding; plan /data2/jjyeung/agent_project_data/distill_design/ROUTED_READER_LEVER_PLAN_20261120.md section 'Rank 1 follow-up (GTC-B)', and the GTC sections above it)
Arm b: the bound GT instance mask on the served anchor where its area at 240x320 is largest (ties lowest anchor), carried forward and backward over the 32 anchors under K1's carry rule (as arm s carries), same tracker, frames, resize, relift path; paired with a and e on the 117 items; operands with no visible anchor keep empty masks. Bars as for t; the verdict field applies them to b - a on all 117 items. Report: b - a with the room bootstrap, share of e - a, seed median size and count under 200 px, per-frame precision/recall vs GT per dataset, per-dataset split, b - t (descriptive).

## Do
1. Copy lever6/gtc/kit to lever6/gtcb/kit. seeds.py: add arm b seeds (out to lever6/gtcb/out/SEEDS_GTCB.json + seeds npz) without changing t or s seeds (assert t and s seeds equal SEEDS_GTC byte for byte). track.py: run arm b only (flag), both directions, same carry; outputs to lever6/gtcb/out/track. launch_gpu.sh: arm b only; refuse hosts trinity-1-13, 0-23, 0-8, 3-23, 0-18; card empty means <= 100 MiB used in both readings; vnice off trinity-0-13 unchanged.
2. relift_t.py (copy): read t and s tracks from lever6/gtc/out/track (read-only) and b from lever6/gtcb/out/track; compute everything registered for b; keep t, s computations identical (assert t and s statistics equal RELIFT_GTC.json's, without printing), and the verdict field for b.
3. Tests: b == e when the b track is GT on every frame; b == a with served masks; seed rule (largest anchor, ties); both-direction carry; verdict edges. Run test_units and the real-dump relift test (assert only).
4. REPORT_GTCB.md (<= 30 lines): changes, seed counts (units, median seed size and count under 200 px are seed facts, not results: report them), forecast GPU seconds, launch command for trinity-0-13 (paths identical there; list exactly which new files must be copied to 0-13), tests. SHA256SUMS_GTCB.
Final message under 12 lines. If a hook blocks writing a file, give its content in the final message.
