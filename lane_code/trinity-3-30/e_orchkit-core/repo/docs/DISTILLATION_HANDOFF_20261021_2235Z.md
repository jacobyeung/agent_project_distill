# Distillation handoff, 2026-10-21 22:35Z (10-21 15:35 PT)

This handoff replaces `DISTILLATION_HANDOFF_20261021_0510Z.md`; read that file only for history. The writer is orchestrator session agent-project-distill-33 (session 90e76a96-1a39-48f6-b166-97ebf67b1d86) on trinity-2-8. Notation: L = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`; W = `L/devinwatch_20261004`; B = `agent/scratch/devin_lanes`. Times are PT.

## 1. User rulings in force (verbatim, newest first)

- **15:20:** "we can do per scene grouping. my hunch is that an agent will do better per question since its context isn't filled up - agents do worse the fuller their context is"
- **15:05:** "feel free to use many devin agents at once if helpful! eg on my other project we used 1000+ devin agents at once to label data over several hours"
- **14:10, T3 recipe (an answer to a choice):** "Hybrid: traces only where they don't hurt (Recommended)". Traces only for counting, relative count and relative distance; numeric types (size, absolute distance, room size) keep the parent's direct answers; plus one arm testing prior-anchored numeric traces.
- **13:30:** "we got flagged for having several jobs - but as long as they have a15_cot_... it's fine!"
- **11:55:** "i think 32 during day, 64 at night with my exceptions is a good rule." Night is 22:00-06:30 PT (the orchestrator's definition, not objected to).
- **11:40:** "keep going with T2, Irestarted the aws tunnel". The Mac runs `ssh -N … -R 42224:aws-iad-cs-002-vscode-02.nvidia.com:22 trinity`.
- **00:00:** "The previous agent crashed the node - please be sure not to crash the node! if you will launch many Devon agents, spread it across multiple nodes." "is it possible for you to get all the uh remaining Devin, you know, agents, if if they're still alive, to report to you?" "Otherwise just relaunch them."
- **Earlier rulings still bind:** remove overhead that protects neither legality, scoring nor a known corrupting defect (10-20 22:42); never ask the user to sign in the trace path; the VSI-590K Qwen-fix pipeline (drop answer disagreements, at most 2 decimals); experimenter GPU priority on Trinity; no deletion; one Git owner; no sweeping searches.
- **Banned hosts:** trinity-3-30 (crashed 10-20 22:40, refuses ssh), 3-18 (stopped answering ssh 10-21 ~09:30), 3-23, 0-28, 2-8 (this session's host is exempt), 2-23, 3-13, 3-3, 1-18. trinity-1-13 and 1-3 kill detached processes when the launching ssh closes. New Orchard IAP connections fail from trinity-2-28, 3-8, 3-18 and 0-23; they work from 2-3, 1-8, 0-8 and 2-8.

## 2. Results banked today

- **Rung 1 (9B and 27B, Orchard, C27, lenient-v2; `L/rwtrain_20261020/out/RUNG1_REPORT.md`):** ST9 (r1835 + T1 traces + replay) VSI-500 49.72 against r1835-on-Orchard 59.51 (-9.79 [-13.5, -6.0]); ST9C replay-only 56.55 (-2.96); ST27_W4 VSI 61.96 against RA17-on-Orchard 64.28 (-2.32, n.s.), VSTI 67.92 against 66.17. Orchard reproduces Trinity's r1835 on VSI (+0.27 [-0.52, +0.98]).
- **Why the traces lose (`L/rung1why_20261021/out/REPORT.md`):** style spillover. The student learns "numeric question, write a trace" and builds furniture-scale chains that land low (room size 28.6 against the control's 60.4, median pred/GT 0.65). With the think block left empty, ST9 scores 57.37, matching the control, so knowledge is intact (`RUNG1_ST9_NOTHINK_DIAG.json`).
- **T2 (2,199 trace rows + r1835 replay + anti-spillover supplement):** VSI-500 49.99 (-9.52 [-13.4, -5.8]), VSTI 59.16 (-2.52). Empty-think 55.41. Room size 37.4, absolute distance 35.2, size 47.4 in trace mode. The supplement did not stop spillover, because T2's own trace rows included numeric types (`L/rwtrain_20261020/out/t2_interim_a7/`, `T2_NOTHINK_DIAG.json`).
- **The direction sign is not a defect:** VSI-590K absolute-direction labels match GT in 48/48 checked; slice k03 had misread "counterclockwise". All 316 direction rows were KEEP. A circular 10-degree agreement rule is recommended for any v5 publication (`L/dirsign_20261021/out/REPORT.md`; admission change, needs one review).
- **Why Qwen traces are wrong (`L/qwentrace_why_20261021/out/REPORT.md`):** 65% loop or cap, 81% of those narrating mm:ss times; Qwen's mm:ss citations hit the displayed timestamps only at chance. Qwen sees 32 frames as 16 timestamped pairs ("<71.1 seconds>").
- **Premise probe (`L/premise_probe_20261021/out/REPORT.md`):** base Qwen can state appearance order (75%) and relative distance (56%); give only coarse size; hedge direction, camera motion, count and absolute distance. Its numeric and count option sets were rebuilt after shortcut leaks.
- **Rewrite audit, 40 rows so far (`L/rwaudit_20261021/out/`):** 24 clean, 16 leak post hoc information, 0 wrong. Counting 0/7 leak; relative count 4/7; relative distance 4/7. Script-drafted rows leak more (6/11 against 10/29). Gates G1-G4 (`out/GATES_T3A.md`, `work/gates.py`) catch 7/9 leaks with 0 false flags.
- **Camera restyle:** only 101 of 1,625 open-teacher camera traces survive visible-cue rewriting, because consecutive displayed views turn a median 42-46 degrees and share no trackable object (`L/camrw_k0{0,1}_20261021/out/CENSUS.json`).
- **Rows written today:** wave 1 (`L/simplerw2_k00..k09_20261021/out/rows.jsonl`) 4,295; wave 2 (`L/simplerw3_k00..k05_20261021`) about 2,800 so far; numfix (prior-anchored numeric, `L/numfix_k0{0,1}_20261021`) 1,645; camrw 101. Prior-anchored numeric traces tune their one visible adjustment to GT (prior alone 8.8% error, stated value 0.5%).

## 3. Lane map (each host has its own watchdog: `W/watch_host.sh` with `W/lanes_<host>_20261021.tsv`; trinity-2-28 uses `W/lanes_trinity-2-28_20261019.tsv`)

| Lane | Host | What and why | State 22:33Z and next action | Check |
|---|---|---|---|---|
| rwtrain_20261020 | trinity-2-3, Orchard | Trains and evaluates 9B arms on Orchard's advanced 4-GPU slot | T2C trained; its evals 159665-8 started 22:27Z. Next: T2 minus T2C, then T3a/T3b if Orchard is chosen (brief `B/rwtrain_20261020/BRIEF_T2_RUN_1.md`) | `out/HEARTBEAT.log`, `out/T2_REPORT.md` |
| aws128_20261021 | trinity-0-8 | Builds tranches: T3a hybrid (9B r1835, 27B RA17) with controls, then the style-sweep arms (`BRIEF_7.md` plus notes) | Building T3a; applies rwaudit gates G1-G4; warns if 9B T3a falls below about 1,500 traces | `out/T3A_REBUILT_V1.json`, `out/RSWEEP_ARMS_V1.json` |
| sprint_train_aws_20261014 | trinity-2-28, AWS | AWS fine-tuning path (reviewed v4 admission da9ecc88) | Staging trainer, r1835, RA17 and the T2C packet onto AWS; told to be launch-ready by 22:00 PT for the night window; T2_s18 launch on hold | `out/PROGRESS.md` |
| rsweep_{short,percept,light}_k00..k09 | 0-13, 2-18, 0-8, 2-3, 3-8, 1-8, 0-23, 2-28 | Style sweep: the same 1,000 questions (`L/rsweep_20261021/SWEEP_QIDS_1000.jsonl`, sha256 fcd11e3a) rewritten in three styles | short 612 rows (6/10 done), percept 355 (1/10), light 289 (0/10) | each `out/rows.jsonl` |
| rsweep_perceptA_k00..k02 | 0-8, 1-8, 2-3 | Same shards 0-2 in percept style by Astra, for a blind model head-to-head | 237 rows (1/3 done) | `out/rows.jsonl` |
| rwaudit_20261021 | trinity-1-8 | Independent frame-checked audit of rewrites, plus the early-vs-late context test and the blind Astra/Opus head-to-head | 120-row report due about 00:15Z; head-to-head addendum about 75 min later | `out/REPORT.md` |
| scenedispatch_20261021 | trinity-3-8 | Builds the per-scene queue, a pluggable-recipe brief and a per-host dispatcher (about 6 fresh Devin sessions per host) | Building; tests 5 scenes before scale-out | `out/REPORT.md` |
| simplerw3_k02, k03, k04 | 0-23, 3-8 | Wave-2 slices, finishing their current staging (no new top-ups) | k02 621, k03 291, k04 252 rows | `out/REPORT.md` |
| qwengen_aws_20261014 | trinity-2-28, AWS 2 nodes | Base Qwen3.5-9B traces on fresh VSI-590K questions; batches 0001-0006 | Running; holds the shared AWS master `L/qwengen_aws_20261014/work/codeaws_trinity_2_28_a15.sock` (otaws and aws_sync borrow it) | `out/HEARTBEAT.log` |
| aws_sync_20261019 | trinity-2-28 | Bounded pulls (about every 20 min) of qwengen roots into `/data2/jjyeung/agent_project_data/aws_mirror_20261019/…` | Puller `work/pull_qwengen.sh` (PID 3957347); roots in `work/pull_roots.txt` | `out/HEARTBEAT.log` |
| otorch_20261020 | Orchard | Qwen generation on Orchard's general GPU | 6,848 authenticated questions; 0 GPUs held at 22:33Z | `out/REPORT.md` |
| otaws_20261020 | parked | AWS open-teacher pilot | Paused after its fourth environment failure (libmunge missing in the container); resume via `out/NEXT_AWS_PILOT.md` and `work/RESUME_AWS_PILOT` | `out/BLOCKED.md` |
| openteacher_20261008 | trinity-1-8 (controller), 2-28 (numeric queue) | Qwen3.6-27B GT-tool teacher: displacement scale-up (reviewed PASS) on Orchard preempt job 159404; Qwen-first numeric queue | Parked; must not claim Trinity cards during the experimenter's SAM3 shortage | `out/ATTEMPT59_STATE.md` |

Done today, no action: simplerw, simplerw2_k00..k09, simplerw3_k01/k05, numfix_k00/k01, camrw_k00/k01, qwentrace_why, rung1why, dirsign, premise_probe, rev_aws128 (verdicts ST9, ST9C_W4, ST27_W4, T2, T2C), rev_otdisp2.

## 4. Infrastructure

- **AWS:** route `ssh -J trinity.vision.cs.cmu.edu code-aws`; marker `L/CODE_AWS_CONTROL_RESTORED_20261021`. Cap file `L/CODE_AWS_GPU_CAP`, flipped by `L/aws_cap_scheduler.sh` (detached on trinity-2-3, PID 2221408; `L/aws_cap_scheduler.alive`; a user exception goes in `L/CODE_AWS_GPU_CAP_OVERRIDE`). Distillation used 2 nodes (qwengen) at 22:30Z. Job names must start `a15_cot_jjy_distill_`.
- **Orchard:** `ssh -F …/claude_orchard_setup_20260922T0700Z/work/ssh_orchard_config orchard`. Advanced QoS allows one 4-GPU job per user; general allows one 1-GPU job; preempt has an ETA of days.
- **Git:** a single Git-owner subagent ran every commit over ssh on trinity-0-8 (36 requests today). Receipts sit in each lane's out/.

## 5. What survives this session and what dies

- **Survives:** every Devin lane and per-host watchdog; the cap scheduler; Orchard and AWS jobs; the aws_sync puller; openteacher's controller and numeric queue.
- **Dies:** this session's alert watcher (`scratchpad/alerts_watcher.sh`; filters DONE alerts from rsweep/simplerw3/numfix and STALE alerts within 15 min of a relaunch), the Git-owner subagent, and the lanemsg bindings to session 90e76a96.
- **Successor actions, in order:**
  1. Run `lanemsg --orchestrator adopt` on each active lane in section 3, and read each lane's `mail/outbox/new/`.
  2. Re-arm an alert watcher on `W/ALERTS.log` (skip BLOCKED; drop STALE within 15 min of a RELAUNCHED line).
  3. Start a new single Git-owner subagent (git only over ssh on trinity-0-8).
  4. Read T2C's result; read T3a's manifest; check sprint is launch-ready; at 22:00 PT train T3a, T3b and the sweep arms on AWS (6 nodes at night) and Orchard.
  5. When scenedispatch's test passes, scale the per-scene wave using the sweep's winning style.

## 6. Open user decisions

- Whether to keep investing in traces if T3a and the sweep also lose to direct answers (the 10-12 "traces, not answer-only" ruling is now hybrid).
- Camera motion: the 32 sampled frames rarely support it; denser frames or a motion signal would be a research decision.
- Optional `~/.ssh/config` ControlMaster for code-aws (affects other projects).

## 7. Do not redo

- Do not train another all-type trace tranche: rung 1 and T2 both lost about 9.5 VSI points, by the same mechanism.
- Do not restyle the open-teacher camera traces again.
- Do not re-audit direction signs.
- Do not reuse the premise probe's original numeric or count option sets; both leak.

## 8. Footguns learned today

- **Launch shells:** an ssh `bash -c` launch shell whose command line names lane paths fools the watchdog's pgrep; end remote launch commands with `; exit 0`, then kill any leftover `bash -c cd /home/jjyeung/agent_project_distill` shell. `ssh host 'pgrep -f watch_host.sh'` matches itself.
- **Model outage:** Devin's Astra provider failed for hours (01:30-04:00 PT); every slice hit the relaunch cap. Lanes now relaunch on Opus 5.5. Check `devin*.out` tails for "provider … not available" before debugging.
- **Watchdog semantics:** a lane whose REPORT ends DEVIN_LANE_DONE is never woken by WAIT_FOR_FILE. A finished Devin `-p` session can linger and block relaunch. Wake a done lane with a newer BRIEF file; the watchdog relaunches from the newest one.
- **Records:** cap every record sent over ssh at 1 MB, with references by path and sha256 (otaws once shipped 146 MB).
- **AWS endpoint:** the tunnel lands on the login node, not a compute node.
- **Git checks:** the Git owner reports when it did not verify a lane's "unchanged" claim; diff those yourself (`diff -r` between package versions).
