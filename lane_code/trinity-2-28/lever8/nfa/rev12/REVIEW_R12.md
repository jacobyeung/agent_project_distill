# REVIEW_R12 (o_sub_preempt_r12.sh, fresh read-only review, trinity-2-28, 2026-11-21)
Verdict: NO-GO, on one small fix (finding 3). R1 and R2 are correct; three lines after the hold can still exit under set -e and leave a held job with no message.
Line numbers refer to /scratch/jjyeung/orch_n30/lever8/nfa/o_sub_preempt_r12.sh. I read the files only and ran nothing against Slurm.

1. R1: PASS in logic. Line 46 sets Partition and ExcNodeList in one `scontrol update`. Slurm applies update fields in sequence and may keep some after an error, so the single call is not atomic by itself. The script does not rely on atomicity: any nonzero exit goes to the else branch (:64-67), which cancels. A zero exit is re-verified (:47-56), and a wrong partition or exclusion cancels (E93). No path releases a job without the verified pin (community-4 is excluded via :29 and checked by :51-53).
2. R2: PASS. Line 48 takes one snapshot, and :50 splits it on spaces; newlines stay as separators. The `^Requeue=` anchor matches only the token that starts the line "   Requeue=N Restarts=..." after the split. A missing field (empty rq) or a duplicate match ("0\n0") fails `[ "$rq" != 0 ]` and cancels (E94), so the check fails closed. The check runs after the partition move and before the release (:62), which is the right order.
3. NO-GO: three lines after the hold exit under set -e and leave the job held without an E-code. This breaks criterion 1 ("no path leaves a job held"):
   - :47 `part=$(squeue ...)`: a transient squeue failure exits. The job is held on preempt with the pin set (or unverified).
   - :48 `sj=$(scontrol show job ...)`: a failure exits in the same state.
   - :62 `scontrol release`: a failure exits with the job held, pinned and Requeue=0.
   Lines :47 and :62 were in the original, and :48 replaces an equivalent pipeline under pipefail, so neither patch added these paths; R1 asks that they be closed anyway. Fix: `part=$(squeue ...) || part=gone` (the mismatch then cancels); `sj=$(scontrol show job "$job") || sj=` (empty exc and rq then cancel); `scontrol release "$job" || { scancel "$job" || true; echo "E95 $job cancelled: release refused" >&2; exit 1; }`.
4. Advisory: :54, :59 and :66 run `scancel ... || true` and then print "cancelled" even when scancel failed, which leaves the job held. Print the real outcome instead, e.g. `scancel "$job" && s=cancelled || s="CANCEL FAILED, still held"`.
5. Criterion 3, every exit with a job submitted:
   - :37 SUBMIT.cmd exits nonzero after sbatch has succeeded: the job is live on general, unheld and not recorded in 70.txt (pre-existing, same as o_sub.sh:22).
   - :38 the first output line is not digits: the same state (pre-existing, o_sub.sh:23).
   - :39/:40 the set -C write fails (only a race, since :7-8 tested both files): the job is live on general, with 70.txt possibly written (pre-existing).
   - :43 the hold fails: exit 0, and general carries the job (accepted).
   - :47/:48/:62: held on preempt (finding 3).
   - :55/:60/:67: cancelled, or held if scancel failed (finding 4).
   - :63: released on preempt, pinned to community-0..3, Requeue=0 (success).
   The patch adds no new failure path, because :49-52 cannot fail (sed -n, `|| true`).
6. Criterion 4: PASS. The diff against lever7/nfa/kit/o_sub_preempt.sh touches only :45-67. It holds the single update (R1), the snapshot and Requeue parse and E94 (R2), cancellation in E92/E93 instead of leaving the job held (R1), and the message text. Lines 1-44 are byte-identical, so the receipt, pool, queue and node-list guards are unchanged.
7. Consequence to note: E92, E93, E94 and E95 now cancel, but a/70.txt and a/71.txt stay. Neither o_sub.sh (:5) nor this script (:7-8) will run again, so a refused update spends the one attempt, and a retry needs an orchestrator decision.
8. Advisory (pre-existing): :29 always adds orchard-community-4. If Orchard has no node by that name, Slurm rejects the update, E92 cancels, and the attempt is spent. A one-line check that `sinfo -h -N -n orchard-community-4` lists the node would show this before submit.
