# RUN: training-start rehearsal for 174246 at WAITING_REVIEW (fix15, 2026-11-21; kit 7e23bbdd)

Optional CPU pre-check once the job RUNS and p/s exists (one srun, no GPU): s/o_pre.sh (ships rh, runs rh/pre.sh).
Who runs it: the coordinator (tree_rebuild28), after n_review1j has posted the gate PASS or FAIL, while
X/o/174246/live/WAITING_REVIEW.json exists and before review.json is installed. Orchard calls stay 2+ minutes apart.
The rehearsal's numbers are not evidence for the card's first-steps row (ORDER 1757Z item 4).

## 1. Start (one command, returns in about 75 s)
    cd /scratch/jjyeung/orch_n30/tree_rebuild28/work/fix15
    timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < s/o_start.sh > rd/start.out 2>&1; cat rd/start.out
s/o_start.sh (sha256 1ff06c09) ships rh/ to the node's /tmp/a15_rh_174246/rh (one srun step), then starts on the login
node `nohup setsid srun --overlap --jobid 174246 -N1 -n1 timeout -s TERM -k 20 870 bash /tmp/a15_rh_174246/rh/go.sh`,
and after 40 s prints the driver's log. If rh/ changes, rebuild with `bash s/mk_orchard.sh` first.

What the first print must show: "gpus before: 0,0;1,0;2,0;3,0", "rendezvous port 29517", "sandbox: N args",
"acceptance stand-in rc=0 ... PASS_STAND_IN_NOT_A_REVIEW", "training start (four ranks, 2 steps)".
A "REFUSE:" line means the driver stopped before the GPUs (the reason is in the line; nothing was started).

## 2. Watch (every 2-5 minutes, never closer than 2 minutes to another Orchard call)
    timeout 300 bash .../tools/ossh.sh 'bash -s' < s/o_poll.sh > rd/poll_$(date -u +%H%M).out 2>&1; cat rd/poll_*.out | tail -60
Shows the driver log tail, each rank's last stage, STEP and ERROR records, the last GPU samples, and, once the
run has ended, the summary (sum.out).

## 3. Stop at once (any time; also safe after the run ended)
    timeout 300 bash .../tools/ossh.sh 'bash -s' < s/o_stop.sh > rd/stop.out 2>&1; cat rd/stop.out
rh/stop.sh TERMs the driver (its trap cleans up), the training process group and every process whose environment
carries A15_RUN=<run folder>, KILLs what is left after 15 s, then prints the proof: marked processes left [],
driver left [], GPU memory and compute apps. It never touches a job process: the job's processes do not carry A15_RUN.

## 4. Pull the evidence (after the end; under 15 MB of base64)
    timeout 300 bash .../tools/ossh.sh 'bash -s' < s/o_pull.sh > rd/pull.b64 2>&1
    mkdir -p pull && sed -n '/^H4sI/,$p' rd/pull.b64 | base64 -d | tar xzf - -C pull
summary.json, go.log, accept.log, ev_rank0-3.jsonl, smi.csv, the tail of t.raw.log (unscreened), proof.txt,
job_before/after.txt, env.txt, bwrap_args.txt and the tree's smoke folder (metrics_174246.jsonl, smoke.json).

## Expected durations (fix14/fix6 measurements on 174134 under kit 929ab213's predecessors; model load and step times never measured)
- guards, layout, acceptance stand-in: 10-60 s.
- ranks up about 2 s after the start; seal, RESULT, identity and verify_staging to about 43 s; admit (u.py) to about
  110 s; admit again inside train to about 180 s; rank-0 prepared(admission=True) to about 250 s.
- then authenticate (2 s), model load on rank 0 with asset hashing, the other ranks, fla check, wrap, rows, first
  step, second step: not measured before; my guess 3-8 minutes.
- budget: the driver stops the ranks itself at 800 s after its start and cleans up in about 30 s; srun's timeout
  (870 s, KILL 20 s later) is the backstop. Everything ends within 15 minutes of the start.
- the driver also stops the ranks within 5 s if the job's own start appears (n_r/review.json, p/rv.json, t.log,
  REVIEW_ACCEPTED.json or REVIEW_REFUSED.json).

## What success looks like
summary.json (also printed by s/o_poll.sh once the run has ended): "result": "ended rc=0", "ranks_up": 4,
"steps_done" with two steps each listing ranks 0-3, "losses_finite": true, "losses_per_stream" per step and
rank, "step_seconds_max_over_ranks", "seconds_launch_to_first_step_end", "peak_gpu_mib_nvidia_smi" for GPUs 0-3,
"errors": [], and go.log ending with "proof: marked processes left: []", "proof: ps lines naming the rehearsal: 0",
GPUs back to 0 MiB with no compute app.
A failure shows as "result" other than "ended rc=0" with "errors" (rank, stage, type, message, traceback) and
"tracebacks_in_output"; ORDER 1757Z item 3 then applies (BLOCKER with the traceback, debug in the gate window).

## What runs, and what does not
- Same as the job after a PASS: the kit's inner-shell environment (tk_env, tk_pythonpath c, OMP 8) and sandbox
  (tk_bwrap plus the Q_NS/Q_NJ binds and the live bind), the job's own absolute paths (/tmp/q_22c714e1_174246,
  /tmp/q_22c714e1, /tmp/jjyeung/q_22c714e1, the frame map Q_E4 = /tmp/jjyeung/q_22c714e1/p/q/f/<sha256 of X/data2root>),
  the job's own TK_JOB_START (read from the running j.sh at the start), rv.py's PASS-branch checks and writes, t.py's
  launch line (torch.distributed.run, four ranks, e.sh, u.py's checks, verify_staging, admit, train).
- Kit 7e23bbdd (k/j.json 2ca9c9bd, decoded 9f7a02bb): the five python steps run under $Q_NS, so the stand-in acceptance
  gets /tmp/q_22c714e1 and /tmp/q_22c714e1/v.json and the launch gets /tmp/q_22c714e1/p and /tmp/q_22c714e1/v.json,
  as the kit's rv.py (line 436) and t.py (line 441) do. $Q_NJ stays a second read-only name of the job folder and the
  /data2 map target; the sandbox binds are unchanged from 929ab213 (only a.py, pf.py and the step paths changed).
- Different, on purpose: the job folder is read-only at all three names; the writable paths (v.json, p/rv.json,
  p/pr.json, p/q/r run output, j, cache, tmp, rp = X/runs, X/o, X/ck, the live folder X/o/174246/live) are scratch
  folders under /tmp/a15_rh_174246/run_<UTC>/w bound at the same absolute paths; the review record is a stand-in
  labelled A15_REHEARSAL_STAND_IN_NOT_A_REVIEW and lives only in that scratch; train(cfg, smoke_steps=2) (the tree's
  smoke length: no step-0 export, no checkpoint, no export, output r/smoke/174246); --standalone is spelled out as
  the same c10d rendezvous on localhost:29517 (the job's is localhost:0, an ephemeral port); stages are timed by
  wrappers that log and re-raise.
- Publishers: none is started. Not run at all: pc.py --loop and --loop-small (upload sessions), j2.py (periodic
  session), j6.py (live mirror), ep.py/o.py/rd.py (evidence and final publish), the export and stop-file paths
  (smoke length; stop.request is pc.py's). Pointed at scratch: the live folder bind (rv.py's live directory), X/runs,
  X/o, X/ck, the run output p/q/r. The job's own pc.py loops keep running and watch only /tmp/q_22c714e1_174246/p/q/r
  on the host, where the rehearsal writes nothing.
