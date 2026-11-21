# Fix GTC reading code after review NO-GO (lane lever6, trinity-2-28)

You are a build subagent of lane lever6. Check `hostname -s` prints trinity-2-28; stop if it prints `trinity`.

## Rules (binding)
- /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md bind you.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states; a dropped Orchard connection is retried once after 60 s. For you: NO stream, NO ssh, NO Orchard call, NO Git, NO GPU (CUDA_VISIBLE_DEVICES=''), no deletion.
- No recursive grep/find/du/ls -R on /home or /data*. Write only under /scratch/jjyeung/orch_n30/lever6/gtc (kit/relift_t.py, kit/tests/, work/, SHA256SUMS_GTC) and lever6/gtcfix. Do NOT modify track.py, seeds.py, gtc_common.py, frames.py or launch_gpu.sh (the GPU job runs now from a copy of them on another node). Do not touch lever6/gtc/out/track.
- Never compute, print or look at any cell value, score or difference (a, e, t, s, subsets). Tests assert equality or counts only. The tracker's real output does not exist yet on this node; do not wait for it.

## Defect to fix (review: /scratch/jjyeung/orch_n30/lever6/gtcrev/REVIEW_GTC.md, B1)
relift_t.py (about lines 139-150) never computes the registered seed-size subset. Registration (plan /data2/jjyeung/agent_project_data/distill_design/ROUTED_READER_LEVER_PLAN_20261120.md, section 'Rank 1 follow-up (GTC)'): "if t - a misses the first bar but the items whose t seeds all have at least 200 pixels show t - a >= 8 with lower bound > 0, the reading is undecided ... the subset's t - a and item count are reported in every case."
- Membership (fixed now): an item is in the subset when every one of its operands has a t seed with status OK and area_240 >= 200 (SEEDS_GTC.json). An item with an operand that has no t seed (never visible on any anchor) is excluded. The reviewer counted 58 of 117 under this rule; assert the count your code finds equals the count from SEEDS_GTC alone (do not print scores).
- Output: the subset's n items, n rooms, t - a with the same room bootstrap and stats() as the full set (10,000 draws, seed 20261120), per dataset and overall; and apply the guard in the verdict field exactly as registered (first bar on all 117 items decides; the guard turns 'not the source' into 'undecided' only when the subset meets t - a >= 8 with lower bound > 0).
- Also make relift_t.py emit the registered verdict as a field (one of: source_once_seed_right / not_the_source / undecided, with the reason), computed from the bars in the registration, so nobody applies the bars by hand.
- Add tests: subset membership count; guard logic on synthetic stats (all four branches); verdict mapping at the bar edges.
- Rerun test_units.py and test_relift_t.py (the real-dump test asserts only; it took about 600 s for the reviewer), update SHA256SUMS_GTC (it must still cover track.py etc. unchanged), and write lever6/gtcfix/FIX_NOTES.md (<= 15 lines): what changed, test results, the subset count.
Final message under 10 lines. If a hook blocks writing a file, give its content in the final message.
