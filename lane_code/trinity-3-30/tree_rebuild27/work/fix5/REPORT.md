# fix5 REPORT: jn7.sh (jn6 + tb.txt publish + node hold before training)
Status: STARTED 2026-11-21 ~12:25Z (Opus high, session trinity-3-30; build on trinity-1-18 W/w28jn7).
## Progress
- read brief, rules, ORDER 1212Z items 3-4, ANSWER 1214Z item 4, jn6.sh and its tests.
- 12:25Z read kit j.sh (decoded k/j.json), job.sh, rv.py gate, ep.py, fix4 TB_CONTRACT.md (node file $N/tb.txt = $Q_ROOT/tb.txt, <=204800 B).
- Design: training marker = node-local $N/t.log (j.sh opens it as it launches t.py) OR $N/p/rv.json (rv.py installs the review pin just before t.py). Hold iff status!=0, no TERM/USR1 forwarded to the child, no marker, $N/j7.py written, >60 s left before SLURM_JOB_END_TIME-660.
- 12:33Z first test round (jn7 d4c8e7e5): harness v7 cases passed; t7 H1 FAILED: j7.py used str.isascii (py3.7+), node python3 is 3.6 -> no HOLD.txt, hold ran with a failing poll. Fixed (regex), and the hold now starts only after HOLD.txt is published (helper failure = no hold). New bytes jn7 98edfd9e; rerun of t7 + harness started ~12:37Z (old runs kept as W/w28jn7/t7_v1, work/build27_v1).
- 12:40Z round 2 on jn7 98edfd9e: harness main 38/38 PASS (jn6+jn7). t7 H1 (hold+RELEASE, 10 s release->exit), H3 TERM/USR1, H4 group TERM, H5 helper failure all ok; H2 was a test bug (10 s hold is below the 60 s minimum, so no hold by design) and the stub-kit helper lacked a mkdir. t7.sh fixed (e02f6e00), t7 rerun ~12:42Z.
- 12:55Z DONE. jn7.sh 98edfd9e1f30f4ba8190702091bed87a8e4b2aa5839468b22ebec30d4b3846fd. t7c.log 57/57 PASS (hold/RELEASE/timeout/TERM/USR1/group TERM/helper failure/markers t.log+rv.json/success/stop path/tb bound+URLs/end-time cap + t6 A-K); harness jn6-vs-jn7 main 38/38, extra 52/52 PASS.
- Deliverables: 1-18 W/w28jn7/out/{jn7.sh,jn7.sh.sha256,JN7.diff,T_JN7_USAGE.md,t7c.log,tests.log,extra.log,results.json}; packet B/events/tree_rebuild/jn7_review/ (15 files, SHA256SUMS).
- Forced-refusal job (NOT submitted; ledger line added): stage X/jn7.sh (sha 98edfd9e), then
  sbatch -p preempt --gres=none --cpus-per-task=2 --mem=4G --time=00:25:00 --job-name=a15_cot_ap4c026eacd9fc /project/community/jjyeung/okh7/x_22c714e1/jn7.sh
  expect refusal in j2.log, tb.txt note, HOLD.txt (status=3 step=gpu), job RUNNING; after >=2 min touch X/o/<job>/RELEASE -> FAILED 3:0 within ~25 s, HOLD_END reason=release.
- Removal candidates: W/w28jn7/t7_v1, t7_v2, t7_v2b, work/build27_v1 (superseded runs).
- Known limit: a TERM arriving while finish() publishes is ignored (as in jn6), so the job can still hold; scancel's KILL or the time limit still ends it.
- rm_guard hook queued a false-positive grep command in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md (not a deletion; no action needed).
