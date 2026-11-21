# Fresh review of the GTC-B registration and kit (lane lever6, trinity-2-28). Read-only; write one report file.
Check `hostname -s` prints trinity-2-28; stop if it prints `trinity`.
## Rules (binding)
- /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md bind you.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states; a dropped Orchard connection is retried once after 60 s. For you: NO stream, NO ssh, NO Orchard call, NO Git, NO GPU (CUDA_VISIBLE_DEVICES=''), no deletion, no edit of kit files.
- No recursive grep/find/du/ls -R on /home or /data*. Write only /scratch/jjyeung/orch_n30/lever6/gtcbrev/REVIEW_GTCB.md (scratch copies under lever6/gtcbrev/tmp). Python: the kit's interpreters, nice -n 10, threads <= 8.
- Do not compute or look at any value of b (it does not exist yet). The t/s results already read (RELIFT_GTC.json) may be opened only for equality checks.
## Files
- Ruling: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/lever/20261121T2137Z_ORCH_ANSWER_lever6_yes_to_t_big_registered_first.md
- Registration: /data2/jjyeung/agent_project_data/distill_design/ROUTED_READER_LEVER_PLAN_20261120.md, section 'Rank 1 follow-up (GTC-B)' (and the GTC sections just above it for conventions).
- Kit: /scratch/jjyeung/orch_n30/lever6/gtcb (kit/REPORT_GTCB.md, kit/*.py, kit/launch_gpu.sh, kit/tests, out/SEEDS_GTCB.json, SHA256SUMS_GTCB). The reviewed base kit: lever6/gtc (reviews lever6/gtcrev/REVIEW_GTC.md and lever6/gtcrev2/REVIEW_GTC2.md). Relift code lever5/r1x/r1/relift.py.
## Criteria (GO / NO-GO, file:line for every defect)
1. Arm b matches the registration: GT instance on its largest 240x320 anchor (ties lowest), carried both ways under K1's carry rule, same tracker, frames, resize and relift path as t and s; paired with a and e on the 117 items; unseeded operands empty.
2. The verdict applies the t bars to b-a on all 117 items, and every registered report field (b-a with the room bootstrap, share of e-a, seed median and count under 200 px, per-frame precision and recall per dataset, per-dataset split, b-t descriptive) is computed; t and s remain identical to the banked RELIFT_GTC.json.
3. Nothing selects after results; the seed rule depends on GT and anchors only.
4. The launcher follows the rules (host refusals, two readings 5+ min apart, normal priority on 0-13, timeout, no rerun after a kill); the copy list to 0-13 is complete.
5. Tests exercise b == e, b == a, b == t and the verdict edges; rerun test_units.py (and test_relift_t.py if it fits in 15 min); SHA256SUMS_GTCB verifies.
## Output
REVIEW_GTCB.md (<= 40 lines): first line `VERDICT: GO` or `VERDICT: NO-GO`; a line per criterion; blocking defects with the smallest fix; non-blocking notes. If a hook blocks the write, give the content in your final message. Final message: verdict and blocking defects only.
