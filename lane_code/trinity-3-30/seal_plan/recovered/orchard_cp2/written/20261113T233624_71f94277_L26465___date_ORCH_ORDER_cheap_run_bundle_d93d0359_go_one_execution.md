<!-- recovered by seal_plan: transcript=71f94277 line=26465 utc=2026-11-13T23:36:24.644Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_ORDER_cheap_run_bundle_d93d0359_go_one_execution.md heredoc_quoted -->
# ORCH order: fixed bundle d93d0359 confirmed; this note grants ONE cheap execution

I read the three diffs against acf803e7 myself: the runtime diff (sha e0f95bfb, one function, `worker_command`: `/usr/bin/env` and an explicit minimal environment `PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME=TMPDIR=<the node-private folder>`; `--export=NONE` kept), the test diff (fe8df785: the launch line run through a stand-in `srun` with an empty environment must reach the helper's first frame; the old launcher fails it), and the operator-file diff (f05911ce: the two compute-step lines and one note). Every other runtime file is byte-identical. Accepted.

**Use:** bundle `/scratch/jjyeung/orch_cd/leg_s1_canary/out/state_copy_169097_20261113T2329Z_b9bfe98f.tgz` (sha256 d93d0359...), bootstrap pin 3e719e27..., operator file `out/STATE_COPY_OPERATOR_169097_20261113T2329Z_b9bfe98f.json` (54f3592e...). Bundle acf803e7 is superseded. The release validator's local folder-count stop (1,058 fixture folders against a limit of 1,024 on Trinity) concerns the lane's scratch folder, not the bundle; I accept the release with that stop recorded.

**Grant.** One cheap execution with five new sessions under object names absent from your map. The five sessions minted at 23:08Z stay untouched. Login spool on `/var/tmp` as proven; a new nonce and a new spool folder.

**Conditions** (unchanged from 2123Z): job RUNNING with normal steps after the last completed save; no save due and no milestone export within 30 minutes; capabilities through standard input only; detached launch, second short fetch, raw saved before decoding; no retry; job checked before and after with step times.

**Timing.** An ordinary save is due about 23:52Z, so wait for it to complete, then launch. Start no later than 00:50Z (the step-200 export is due about 01:25Z). If that window is missed, the execution moves to after the step-200 export has finished and been attested.

**If it dies again before the helper's first frame:** stop, post the raw return, do not repeat. Before launching, check from the evidence you already hold that `/usr/bin/python3.12` exists on the compute node (your runtime facts record the host's `/usr/bin/python3` as 3.12.3 and node tracebacks show `/usr/lib/python3.12/`); if you hold a record that contradicts it, tell me instead of launching.

Report as ordered in 2123Z, plus both login spool folders (path, size) for the user's removal list. The full copy remains unauthorized.