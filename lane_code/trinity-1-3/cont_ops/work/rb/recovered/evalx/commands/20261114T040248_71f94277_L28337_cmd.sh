<!-- recovered by seal_plan: transcript=71f94277 line=28337 utc=2026-11-14T04:02:48.146Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd; S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$C" <<'EOF'
import sys
C = sys.argv[1]
head = ("NOTE ON YOUR WORKING DIRECTORY: you were started in /home/jjyeung/agent_project_distill only because Devin requires a trusted workspace. That folder is on overloaded network storage. Do not search, index, list or read it, never use a built-in search or grep tool on /home or /data*, and never run git there. Do all work in the lane folder named below, using absolute paths.\n\n"
        "# Evalx successor 19 (lane `/scratch/jjyeung/orch_cd/evalx` on trinity-2-18). ORCH (orchestrator orch-home-distill-79) remains the launch authority.\n\n"
        "This brief has three parts: your predecessor's draft (verbatim), the binding rules, and ORCH's addendum. **Where the addendum differs from the draft, the addendum wins.** Your predecessor has been stopped; you are the only evalx lane.\n\n"
        "---\n\n")
draft = open(C + "/evalx/work/BRIEF_SUCCESSOR19_DRAFT.md").read().rstrip("\n")
rules = """

---

## Rules (all binding)
- Every GPU job runs under vnice with a stall guard.
- Every ssh into Trinity goes through work/trin_vl/tssh_long.sh with CALLER=evalx: one call per minute, with commands batched into one `bash -s` script. Polls of a Trinity node run once per 10 minutes outside launches. Reuse an existing session to a node instead of opening a new login. If any ssh login or copy drops or is refused, stop, do not retry, and post it.
  - Never pipe a file into tssh_long.sh while also redirecting its stdin.
  - Never put a pkill pattern that also appears in the ssh command line; it kills the session.
  - GNU nproc obeys OMP_NUM_THREADS; use `nproc --all`.
- Never delete anything: a local guard blocks any removal call, even inside scripts, and blocks shell text that names deletion operations (even in a test's deny-list); a blocked command is never retried. Write such text into files with your editor tool. No AWS, no /data* bulk reads, nothing over 1 GB on 2-18 /scratch, no git in /home trees.
- Whenever a card of ours is stopped or started, post the event with a fresh nvidia-smi and pgrep reading taken in the same call. An URGENT inbox note wins; act on it within two minutes.
- Kit workers run with `python -I`; use p1cpu or the sam3 env, never PYTHONPATH.
- Main has priority over every GPU, over disk and over the IO governor (USER 2026-11-13: rebuttal evaluations first); ours run only on a card that reads empty at a fresh check, under vnice, released at once on request. Never trinity-0-8, 0-23, 3-23; leave 0-18 free.
- Events go to `events/` with a `date -u +%Y%m%dT%H%MZ` stamp taken in the writing command; RESULT, QUESTION or BLOCKER for anything ORCH must act on. Post events only for those; routine progress goes to `STATUS.md` (ten lines, rewritten in place).
- Never end your turn: loop on `timeout 270 bash work/trin_vl/hold_wait.sh 4` and act on what it prints.
- Rotate before 250K tokens: write the next draft and post RESULT_ready_for_successor.

## ORCH addendum (2026-11-14T04:03Z). This supersedes the draft wherever they differ.

**1. The native recovery IS authorized, on trinity-0-28.** The draft's section "Native recovery: no transfer may start yet" was written before my GO. Read `inbox/20261114T0356Z_ORCH_GO_recovery_on_0_28_no_more_node_scans.md` first and carry it out: no retry of trinity-0-3 and no further node probes; through an existing session to trinity-0-28 read free space and whether GPU 6 is empty (stop and tell me if free space is below 152 GB); restart the step-200 export with the confirmed helper (`native_transfer.py` ee98dce8) under a freshly pinned plan and intent, into a new folder beside `export_BAD`, governed, 8 MB/s, behind main; hold threshold 126 GB free, floor 125 GB, with the five-minute guard restarted at that number; then the three depth files from GCS, then the model manifest; nothing else goes onto that node; then the one ten-minute restoration and parity probe on GPU 6 under vnice. Main was told the bytes before the first byte (24.3 GB more, about 129 GB free at the end). If the stream stops for any reason the helper cannot ride through, stop and post the raw log; no second recovery without my word. Also record, for the user, how many new Trinity logins the lane opened in the five minutes before the trinity-0-3 drop at 03:54:10Z (from the rate limiter's record).

**2. The packed four-GPU job is closed: not built** (record `/data2/jjyeung/agent_project_data/distill_design/ORCHARD_PACKED_JOB_FEASIBILITY_20261114.md`). Do nothing on it.

**3. IF-P0's baseline arm P0 will move to the `advanced` partition** as an ordinary single one-GPU job when the production leg releases that cap (about 15:00Z). Lane if_p0 is resealing its kit to admit that partition and will hand you a second packet with a fresh token. You submit it only on my separate written word. Duplicates: job 169413 (the `general` copy) stays queued until the `advanced` job has been accepted and has passed its preflight; then I order 169413 cancelled; if 169413 starts first, the `advanced` packet is never submitted. Never cancel or submit on your own reading of the queue.

**4. Later direct reads.** The step-400 export is due about 08:50Z and the final stop export about 14:30Z; the operator (orchard_cp2) delivers each artifact and attestation to your inbox. Each read is pre-authorized as ONE submission on `general` with the accepted launcher (digest b13c6dcc; it admits step 400) and producer 8365bd3b, after your queue and main-notice check. The final export's step is not in the launcher's admitted set: when the operator tells you its step number, ask me for the one-line admission as you did for step 200. Step-400 and final packets carry the same watch list as step 200.

**5. Camera baseline hardware:** the label stays "baseline hardware evidence incomplete"; spend no more sessions on it.

**6. First actions, in order:** read `STATUS.md` and the inbox notes from 0234Z on; carry out item 1; one queue observation with `TZ=UTC` in your next routine Orchard session; then hold on the inbox.
"""
open(C + "/evalx/BRIEF_SUCCESSOR19.md", "w").write(head + draft + rules)
print("written", len(head + draft + rules))
EOF
kill 1228219 2>/dev/null; sleep 2; if kill -0 1228219 2>/dev/null; then echo "old lane still alive"; else echo "old lane stopped"; fi; (cd /home/jjyeung/agent_project_distill && bash /scratch/jjyeung/orch_cd/orch_tools/devin_bg_acp.sh /home/jjyeung/agent_project_distill $C/evalx/BRIEF_SUCCESSOR19.md gpt-6-astra-max 43200 $C/evalx/out/devin_stdout_19.log) 2>&1 | tail -n 3; sed -i 's#evalx|evalx/BRIEF_SUCCESSOR18.md||#evalx|evalx/BRIEF_SUCCESSOR19.md||#' $S/LANES; sed -i 's#\[evalx\]="evalx/BRIEF_SUCCESSOR18.md"#[evalx]="evalx/BRIEF_SUCCESSOR19.md"#' $S/lanewatch.sh; grep evalx $S/LANES; grep -n 'evalx' $S/lanewatch.sh | head -n 2 | cut -c1-80