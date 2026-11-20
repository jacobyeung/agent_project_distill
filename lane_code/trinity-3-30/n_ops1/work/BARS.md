# n_ops1 watcher bars (parse.py 04eab4d2; tests: tests/run_tests.py 47/47 PASS, tests/replay_172660.py 91 checks 0 FLAG (2 WARN lines NEW_GCS_DONE/NEW_CK_MARKER, as before))
STOP (I may cancel without asking): non-finite stream loss on all 4 ranks on two consecutive steps (exit 4).
BLOCKER (exit 2): job state not PENDING/RUNNING; Traceback/Error/REFUS/E## in j.out, q.log, rooms.log, t.log or o/<job>/o.tar; q RESULT not ADMIT;
 non-finite on any rank; a stream (pose .148, vqa .059, pointing .43 = P near step 400) above 3x for 3 consecutive steps;
 step wall >300 s (not a checkpoint/export step); no new step for max(3 x median wall, 15 min); no log/file growth and <0.5 core busy for 10 min (STALL; job-level cgroup, n_ops3 0335Z);
 GPU util 0 on all cards twice in training; cgroup anon+shmem >90% of limit; /project free <150 GiB; node /tmp free <300 GiB;
 ETA(next export) + 30 min > time left; other jobs of ours on advanced >5 min after N's submission; job name not a15_cot_ap<hex> or any kit word (k/g.json list) in name/command/workdir/stdout;
 srun overlap failing twice; two empty checks in a row (then read logs at once).
 Post-preparation refusal points (n_ops5, ORCH 0924Z item 3): NO_TRAIN_START (review.json in n_r, no t.log 20 min); NO_FIRST_STEP (t.log, no step 1 for 45 min); NO_FIRST_CK (no new checkpoint_* dir 25 min after the first step); NO_EXPORT_m<t> (step > t and no live/gcs_m<t>.done 45 min after).
WARN (in RESULT): stream above P median + max(0.5m, 6 x 1.4826 MAD) two steps; skipped microsteps; non-finite outside ranks; new checkpoint/export marker.
n_ops8 2026-11-20 (kit 24m4z): FLAG HELD <n> min when the job pends JobHeld* 15+ min (sbatch --hold until sess_<job>.json is installed; WARN held before). Export done markers also read from node-local $Q/live_spool/state (inner.sh @@LSTATE, with retry.log and j2.retry.log tails).
n_ops8 2026-11-20 (ORCH RULING 2232Z item 3): FLAG NO_RECEIPT_10MIN when an export m<t>/artifact.json exists and the node-local receipts count ($Q/live_spool/private/*.receipts.jsonl lines, inner.sh @@RCPT, count only) is still 0 ten minutes later.
