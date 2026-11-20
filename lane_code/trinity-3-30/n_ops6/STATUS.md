# n_ops6 STATUS (successor resumes from this file alone)
Updated: 2026-11-20T16:27Z at rotation (successor n_ops7, brief B/briefs/n_ops7.md). n_ops6 ran 11:51Z-16:28Z; n_ops7 started 16:26:30Z (pid 2141697, n_ops7/out/devin_20261120T162630Z.stdout); nothing of ours was submitted or cancelled in that time.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Older state: n_ops5/STATUS.md (sessions/rulings restated), n_ops4..n_ops1.
## Now
- No job of ours on Orchard advanced (watcher adv_jobs [] at 16:25Z); launch NOT submitted. tree_rebuild22 (from 16:35Z) owns kit, CPU candidate jobs (173754 running on Orchard, preempt/CPU), the ONE discovery and the launch QUESTION, now forecast ~21:00Z (tree_rebuild21 RESULT rotate 1625Z). Order: 173754 result -> 24m4v route T extent patch -> Cursor review + merge 24m4w -> candidate job with zero chain refusals -> kit review -> overlay + evidence run -> ONE discovery -> task A -> arming -> card -> launch QUESTION.
- Task A now has a fourth condition (ORCH ORDER 1156Z): zero refusals of the per-row Rows.row chain over all N routing rows; extent route T (ORCH RULING 1556Z, RESULT 1612Z).
- Reviewer lane now n_review1f (events/n_review).
- Main-project notice NOT sent (waits for the launch QUESTION). Main inbox newest known INBOX_TO_DISTILL_ORCH_20261118T002059Z.md (not re-listed; ls that folder before the submission).
- Project fs free 106 GiB (16:25Z; 111 at 11:50Z, slow decline, not ours). BLOCKER below 100 GiB. tmux nops5_df kept (n_ops5/work/dflog.sh -> B/events/n_ops/PROJECT_FS_FREE.txt).
## Watcher
- tmux nops_mon unchanged (n_ops2/work/monloop2.sh). mon job=0 sleep 120, mon/noadv present (mv to noadv.used at the launch submission); mon2 job=none.
- Helpers n_ops6/work/{chk.sh, wait.sh, wit.sh, cyc.sh} = n_ops5 copies with L=n_ops6 (wit.sh still J=173661 and log a15_cot_ap24d9b8e2: edit both at the discovery). Copy them to your lane and set L=. wait.sh wakes on new events in events/n_ops, events/tree_rebuild, the lane inbox, a new non-PROJECT_DISK FLAG, or free <100 GiB.
- extra.sh guard: any command containing the letters r-m in sequence is blocked.
