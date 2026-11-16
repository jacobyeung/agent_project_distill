<!-- recovered by seal_plan: transcript=71f94277 line=22524 utc=2026-11-13T16:01:31.314Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/20261113T1606Z_ORCH_AGREE_end_runbook_with_three_additions.md  -->
# ORCH (2026-11-13T16:06Z): I agree to the end-of-allocation runbook (sha c9a0d883), with three additions

I read all of `out/RUNBOOK_END_OF_ALLOCATION_469ddece.md`. Its sequence, the project-space guard, the uploader-only boundary, the loss-baseline check, the retention procedure and the completion report stand as written. Add the following and post the revised hash.

## 1. Measure what the one-hour reserve depends on, today

The trainer stops one hour before the wall. In that hour the job must save (about 70 s), pack the stop export (about 5 min), upload it (unmeasured), and write and re-read a slot of about 111 GB on the project filesystem (unmeasured). At 123 MB/s for both passes the slot alone takes 30 minutes; at 60 MB/s it cannot fit at all.

- **Read rate:** take it from evidence you hold, no new job: the staging verification of 2026-11-12 (357.3 GB hashed in 2,193 s, about 163 MB/s) and this job's own staging log (bytes and seconds per archive from the project filesystem to `/tmp`). Report both.
- **Write rate:** one measurement is approved. A CPU job on `general` (2 CPUs, 8 GB memory, 10 minutes, no requeue) writes one 8 GB file of non-compressible bytes with a final sync to a fixed path in our own project sandbox, times it, re-reads it once and times that. On any repeat it rewrites the same file in place. The file stays; add it to the candidates list for the user. Run it now if `general` is free; it goes before the checker's fixture rehearsal and before the eval lane's read. Not on the login node.
- **Upload rate:** when the step-1 export uploads, report its bytes, seconds and MB/s per part from the receipts and `o/gcs.log`. That figure sizes the foreground pass at the end.
- Then put numbers in the runbook's time budget: the expected duration of each phase in the last hour, the latest slot start, and the margin. If the sum exceeds 45 minutes, tell me at once; that decision is mine and needs hours of notice, not minutes.

## 2. Unsent milestones during the run

Any milestone export that has not uploaded by the next milestone lengthens the foreground pass at the end. Report an unsent milestone when you first see it (already in the GO), and keep a running count in your STATUS.

## 3. Conditional permission for the uploader-only intervention

The runbook requires my word at the time. Keep asking, with the five evidence items. If you have reported at the cutoff and I have not answered within **five minutes**, you may proceed once, under exactly the reviewed boundary and its preconditions, without my answer:

- all ranks and the native launcher have exited, `r.sh` is in its final persistence block, a complete checkpoint of the final saved step exists, and the mirrored loss baseline reaches that step;
- the blocker is a validated, job-owned `gcsput.py` subtree, validated per target as the runbook says;
- you end only those subtrees, including uploaders the finite final pass spawns afterwards, each validated fresh;
- you stop and report if anything else is the blocker.

Reason: the cost of acting is one unsent export, which the slot's checkpoint can regenerate; the cost of not acting is the allocation's whole training state. This permission covers nothing wider, expires when job 169097 ends, and does not cover the retention copy, which still needs my word.

The hour-12 agreement condition of the GO is met once you post the revised hash.
