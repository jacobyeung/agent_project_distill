# jn7.sh: jn6.sh plus the traceback copy and the node hold on a failure before training

X = `/project/community/jjyeung/okh7/x_22c714e1`. jn7.sh replaces jn6.sh unchanged otherwise (same SBATCH header,
job name a15_cot_apb2edfac4, ROOT=X/n, j2 publisher, j6 live mirror, gate copy, TERM/USR1 forwarding).
Stage it as X/jn7.sh and check its sha256 against `jn7.sh.sha256` before any submission.

## What jn7 adds
1. **tb.txt.** On every non-zero exit, right after the failure text (j2.log/j2.err or the fixed fallback) and before
   the final live snapshot, the wrapper copies the kit's node-local traceback file `$N/tb.txt` (fix4 TB_CONTRACT:
   in the sandbox `/tmp/q_22c714e1/tb.txt`) to `X/o/<job>/tb.txt`. Bound 204800 bytes: a larger file keeps its first
   and last ~102 KB with an omission line. The copy is unscreened for words (ORDER 1212Z item 3); only URLs are replaced
   by `[URL]`. No other file is read. Without a kit traceback file, tb.txt holds one line `no traceback file at ...`.
   Bounded by `timeout --signal=KILL 30s`.
2. **Node hold.** After all publication, the job holds instead of exiting when all of these hold:
   - the exit status is non-zero;
   - no TERM or USR1 reached the batch shell while the work ran (the stop/export path is never held);
   - training has not started: neither `$N/t.log` (j.sh opens it as it launches t.py) nor `$N/p/rv.json`
     (rv.py installs the review pin just before t.py) exists;
   - the helper `$N/j7.py` was written and published `X/o/<job>/HOLD.txt` (no record, no hold);
   - more than 60 s remain before `SLURM_JOB_END_TIME - 660` (when Slurm sets that variable).

   HOLD.txt names the node, the status, the failing step, the deadline and the node-local paths (node directory `$N`,
   prepared root `$N/p`, `$N/p/q`, `$N/p/q/RESULT.json`, `$N/tb.txt`, `$N/j.sh`, `$N/r.json`, the logs, the Slurm logs).
   A copy is also at `$N/HOLD.txt`. During the hold nothing is removed; the node directory and `/tmp/q_*` stay.
   The hold ends at the first of: `X/o/<job>/RELEASE` exists (poll every 15 s, each poll bounded at 10 s), 180 min
   (`J7_HOLD_S=10800`), the job-end cap above, or TERM/USR1 to the batch shell (scancel, time-limit warning) at once.
   It then writes `X/o/<job>/HOLD_END.txt` (`reason=release|timeout|signal status=<original>`) and exits with the
   original status.

Wrapper refusals before job.sh (fewer than 4 H100, v.py seal, resolve.py/l.py) also hold: the forced-refusal job
below uses exactly this. Setup failures before the helper exists (node directory, j2.log redirect, j2.py creation)
never hold.

## During a hold (ORDER 1212Z items 4 and 6)
```sh
cat X/o/<job>/HOLD.txt X/o/<job>/tb.txt          # node, paths, traceback
srun --overlap --jobid <job> --pty bash          # enter the held node; prepared state is under $N (see HOLD.txt)
touch X/o/<job>/RELEASE                          # end the hold; the job exits with the original status within ~25 s
```
scancel also ends it at once. The hold never extends a job that reached training.

## Forced-refusal CPU job (written, NOT submitted)
Token `4c026eacd9fc`; job name `a15_cot_ap4c026eacd9fc` (opaque). After X/jn7.sh is staged and its sha256 checked:
```sh
sbatch -p preempt --gres=none --cpus-per-task=2 --mem=4G --time=00:25:00 --job-name=a15_cot_ap4c026eacd9fc /project/community/jjyeung/okh7/x_22c714e1/jn7.sh
```
(`-p general` with the same flags if preempt is blocked.) Expected: refusal `fewer than 4 H100; stop before staging`
in X/o/<job>/j2.log; X/o/<job>/tb.txt = `no traceback file at ...; status=3`; X/o/<job>/HOLD.txt within about a minute
of the start (`status=3 step=gpu`; hold_seconds = 10800, or about 840 if Slurm sets SLURM_JOB_END_TIME for the 25-min
limit); the job stays RUNNING. Check at most once a minute; after at least 2 minutes of hold, `touch X/o/<job>/RELEASE`;
expected within ~25 s: job ends, `sacct` ExitCode `3:0` (FAILED), HOLD_END.txt `reason=release status=3`.
If RELEASE is never written, Slurm's TERM at T+15 min ends the hold (`reason=signal`).

## Local evidence (trinity-1-18, W/w28jn7)
- `t7c.log` (57/57 checks PASS, folder t7c): hold cases (start, RELEASE, timeout, TERM, USR1, group TERM, helper failure, t.log and rv.json markers,
  success, stop path TERM/USR1, tb bound and URLs, byte-equal small tb, job-end cap) and t6.sh cases A-K on jn7.
  Runs with the node's system python3 (3.6), older than Orchard's.
- `work/build27/{tests.log,extra.log,results.json}` (38/38 main, 52/52 with extra, PASS): the jn6 harness (jn5-vs-jn6 build26) rerun as jn6-vs-jn7, every
  case, with RELEASE pre-created for jn7 so a held case ends at its first poll; it asserts which cases held and that
  every helper-era failure published a bounded tb.txt.
- Not covered locally: real Slurm signals, SLURM_JOB_END_TIME on Orchard, srun --overlap into a held job, Orchard NFS.
  The forced-refusal job covers the first three in part.
