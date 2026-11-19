# n_ops1 watcher bars (parse.py; tests: tests/run_tests.py 28/28 PASS, tests/replay_172660.py 91 healthy checks 0 flags)
STOP (I may cancel without asking): non-finite stream loss on all 4 ranks on two consecutive steps (exit 4).
BLOCKER (exit 2): job state not PENDING/RUNNING; Traceback/Error/REFUS/E## in j.out, q.log, rooms.log, t.log or o/<job>/o.tar; q RESULT not ADMIT;
 non-finite on any rank; a stream (pose .148, vqa .059, pointing .43 = P near step 400) above 3x for 3 consecutive steps;
 step wall >300 s (not a checkpoint/export step); no new step for max(3 x median wall, 15 min); no log/file growth and <1 core busy for 10 min (STALL);
 GPU util 0 on all cards twice in training; cgroup anon+shmem >90% of limit; /project free <150 GiB; node /tmp free <300 GiB;
 ETA(next export) + 30 min > time left; other jobs of ours on advanced >5 min after N's submission; job name not a15_cot_ap<hex> or any kit word (k/g.json list) in name/command/workdir/stdout;
 srun overlap failing twice; two empty checks in a row (then read logs at once).
WARN (in RESULT): stream above P median + max(0.5m, 6 x 1.4826 MAD) two steps; skipped microsteps; non-finite outside ranks; new checkpoint/export marker.
