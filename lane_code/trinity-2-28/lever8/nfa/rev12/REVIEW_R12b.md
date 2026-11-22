# REVIEW_R12b (o_sub_preempt_r12.sh, fresh read-only review, trinity-2-28, 2026-11-21)
Verdict: GO. R1 and R2 are correct, REVIEW_R12 findings 3, 4 and 8 are closed, and every exit after the hold now cancels the job or releases it pinned, each with an E-code or a success line.
Line numbers refer to /scratch/jjyeung/orch_n30/lever8/nfa/o_sub_preempt_r12.sh. I read the files, ran `diff` against the original and `bash -n` (syntax OK), and ran nothing against Slurm.

1. R1: PASS. Line 50 sets Partition and ExcNodeList in one `scontrol update`. Slurm may keep one field when the other fails, so the script does not trust the call: a nonzero exit cancels (E92, :66-68), and a zero exit is re-verified from fresh squeue and scontrol reads (:51-57); a wrong partition or exclusion cancels (E93, :58). The release (:64) runs only after both checks and the Requeue check pass, so no path releases a job without the pin.
2. R2: PASS. Line 52 takes one `scontrol show job` snapshot; :54 splits it on spaces with newlines kept, and the `^Requeue=` anchor matches only the real token. A missing field (empty rq), a duplicate match ("0\n0"), or a failed snapshot (sj empty) fails `[ "$rq" != 0 ]` and cancels (E94, :61-62). A Comment or path that held " Requeue=0" would only add a duplicate line, so the check still fails closed.
3. REVIEW_R12 finding 3: CLOSED. :51 (`|| part=gone`) and :52 (`|| sj=`) can no longer exit; a failure routes to E93 or E94, which cancel. :64 now runs `|| { E95 ...; exit 1; }` and cancels on a refused release.
4. REVIEW_R12 finding 4: CLOSED. cx (:44) prints "cancelled" only when scancel succeeds and "CANCEL FAILED, still held" otherwise. cx returns 0 in both cases and runs inside an argument substitution, so it cannot trip set -e before the E-code prints.
5. REVIEW_R12 finding 8: CLOSED. :29-31 add orchard-community-4 only when sinfo lists it, so a missing node no longer makes Slurm reject the update and spend the attempt. The test fails open (a sinfo error or a SIGPIPE from `grep -q` under pipefail omits the node), but that is harmless: whenever community-4 sits in preempt, :25 and :28 already put it in ex, and a node outside preempt cannot run a preempt job.
6. Criterion 3, every exit with a job submitted:
   - :39 SUBMIT.cmd exits nonzero after sbatch succeeded: the job is live on general, unheld, not in 70.txt (pre-existing, o_sub.sh:22).
   - :40 the first output line is not digits: the same state (pre-existing, o_sub.sh:23).
   - :41/:42 a set -C write fails (only a race after :7-8): the job is live on general, 70.txt possibly written (pre-existing).
   - :47 the hold fails: exit 0, and general carries the job (accepted in REVIEW_FIX2 5); the line prints %P %T.
   - :58 E93, :62 E94, :64 E95, :68 E92: cancelled, or held with "CANCEL FAILED, still held" in the message.
   - :65 then end of script: released on preempt, pinned to community-0..3, Requeue=0, exit 0.
   No other line after :40 can exit: :53-56 are `printf | tr | sed -n`, `sort | paste` and `|| true` pipelines, the `[ ]` tests sit in if conditions, and :67 ends in `|| echo gone`. No line after the hold exits without an E-code or the success line.
7. Criterion 4: PASS. The diff touches only :29-31 (finding 8), :43-44 (cx), :49-68 (R1, R2, E94, E95, cancellation in place of "release it for general", and message text). The receipt, pool, queue and FORBIDDEN guards (:1-28, :32-42) and the hold (:45-48) are byte-identical to the original.
8. Advisory (edge, fails closed): if preempt holds only community-0..3 and community-4 is absent, ex is empty. Slurm then shows ExcNodeList=(null), so `have` differs from the empty `want`, and E93 cancels and spends the attempt. That would need preempt to shrink to community-0..3; nothing needs to change unless it does.
9. Advisory (carried from REVIEW_R12 7): E92-E95 cancel but leave a/70.txt and a/71.txt, so a retry needs an orchestrator decision.
