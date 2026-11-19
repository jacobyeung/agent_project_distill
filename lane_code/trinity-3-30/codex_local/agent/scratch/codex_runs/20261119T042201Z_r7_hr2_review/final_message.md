1. **HIGH — The checkpoint race remains (REVIEW1 #1: not resolved).** [hr2.sh:40–43](/scratch/jjyeung/orch_n30/r1_ops6/work/r7/rv2/hr2.sh:40) uses checkpoint age, which cannot exclude a stop-triggered save. The overlap check at lines 99–100 also precedes archive hashing at lines 104–166, and `overlap=yes` does not prevent `ok=1`. **Fix:** defer hashing until checkpoint writing has permanently stopped, or hold an existing writer-shared exclusion throughout. Record overlap after all hashing and reject detected overlap.

2. **MEDIUM — Publication failures can still report success (REVIEW1 #5: partly resolved).** [hr2.sh:167–174](/scratch/jjyeung/orch_n30/r1_ops6/work/r7/rv2/hr2.sh:167) captures archive creation failure, but ignores failures of the archive rename, required receipt copies, and `DONE.json` write. Successful receipt generation and archive creation can therefore produce exit 0 despite missing published evidence. **Fix:** check each required publication operation and exit nonzero on failure; publish successful completion only after those operations succeed.

3. **LOW — The watcher reports receipts and files that may not exist.** [exw.sh:37–38](/scratch/jjyeung/orch_n30/r1_ops6/work/r7/rv2/exw.sh:37) unconditionally says receipts “ran” and lists every output, even when `srun` refuses the step. It also lists `r.json/e.json` at step 600, although [hr2.sh:82–95](/scratch/jjyeung/orch_n30/r1_ops6/work/r7/rv2/hr2.sh:82) generates them only at 400. **Fix:** describe unsuccessful invocations as attempts and list only outputs confirmed by the result.

Remaining REVIEW1 findings:

| Finding | Status | Evidence |
|---|---|---|
| #2: PID selection | Resolved | [hr2.sh:29–34](/scratch/jjyeung/orch_n30/r1_ops6/work/r7/rv2/hr2.sh:29) restricts selection to job descendants running the trainer command. |
| #3: Timeouts | Resolved | [hr2.sh:20](/scratch/jjyeung/orch_n30/r1_ops6/work/r7/rv2/hr2.sh:20): 1,170 seconds plus 10-second grace inside a 1,200-second outer timeout. |
| #4: Shard exclusions | Resolved | [hr2.sh:112–129](/scratch/jjyeung/orch_n30/r1_ops6/work/r7/rv2/hr2.sh:112) applies exclusions centrally before hashing. |
| #6: Step-400 exit status | Resolved | [hr2.sh:170–180](/scratch/jjyeung/orch_n30/r1_ops6/work/r7/rv2/hr2.sh:170) selects export-only success and preserves the step status. |

NOT READY