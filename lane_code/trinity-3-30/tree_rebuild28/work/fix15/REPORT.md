# fix15 REPORT: training-start rehearsal (lane tree_rebuild28); now for job 174246 on kit 7e23bbdd
STATUS 21:51Z: READY FOR 174246. The coordinator's 2147Z message (new job 174246, kit 7e23bbdd) is handled: every 174198 reference is now 174246; the stand-in acceptance and the launch take $Q_NS paths, as kit 7e23bbdd's k/j.json does; the Trinity test on a fake job folder in the 7e23bbdd layout PASSED (CPU only); the s/o_*.sh scripts and RUN.md are rebuilt. No Orchard call since 18:28Z (174246 is pending). I used no GPU and wrote nothing into any job folder, X/n or X/o.

## Adaptation to job 174246, kit 7e23bbdd (21:47-21:51Z)
- Kit: the local mirror n30_mirror/tree_rebuild28/fix17/s34_n_go.tar (163cf197), extracted to fix15/kit34; seal 7e23bbdd, k/j.json 2ca9c9bd, decoded 9f7a02bb (fix15/dec/j34.sh). Against 929ab213's shell the only changes are the five python steps' paths ($Q_NJ -> $Q_NS on lines 421, 429, 432, 436, 441) and a comment. tk_env, tk_bwrap, the Q_NS/Q_NJ binds (line 410), the live bind and Q_E4 are unchanged, and t.py, e.sh, u.py, rv.py, z.py and l.py are byte-equal to 929ab213's.
- Changes in rh/: go.sh passes $Q_NS and $Q_NS/v.json to accept.py and $Q_NS/p and $Q_NS/v.json to t2.py (fix16's note on lines 105 and 115); the default job is 174246 in go.sh, stop.sh and pre.sh (scratch /tmp/a15_rh_174246); pre.py reads the tree under $Q_NS. L.sh's sandbox is unchanged apart from its header comment. test/mkfake.py writes the fake pins under /tmp/q_22c714e1. s/mk_orchard.sh and s/mk_pre.sh default to 174246. The 174198 versions are kept in fix15/old174198/.
- Trinity test 4 (trinity-1-18, 21:48:39Z, rd/t4.out), on a fake job folder 990035 in the W/w34/n_go layout (seal 7e23bbdd, j.json 2ca9c9bd):
  - The stand-in acceptance passed, writing /tmp/q_22c714e1/p/rv.json, p/pr.json and v.json in scratch only; the fake job folder's p still holds just i, plan.json, q and s.
  - The launch line got /tmp/q_22c714e1/p and /tmp/q_22c714e1/v.json and ran four CPU ranks on rendezvous localhost:29517.
  - Every rank ran the tree's authenticate() on /tmp/q_22c714e1/p/s (a real directory, no symlink) and got the kit's seal sha256:9d2bbb8a.
  - pre.sh's probes: the scratch paths were writable, and RESULT.json, r.json, j.sh, p/s and p/q/f refused writes (EROFS).
  - Cleanup proof empty; no process left. The same dry run on trinity-3-30 passed first (21:48Z).
- Rebuilt: s/o_start.sh (sha256 1ff06c09), o_poll.sh, o_stop.sh, o_pull.sh, o_pre.sh (optional CPU pre-check once 174246 RUNS); checksums in rh_SHA256SUMS.txt. Mirror: trinity-1-18:/scratch/jjyeung/n30_mirror/tree_rebuild28/fix15/fix15_rh_174246.tar, sha256 d34fed59 on both nodes.
- Not yet checked on 174246's node, because it is pending: the job folder names, free GPUs and TK_JOB_START. go.sh reads them at the start, and its guards refuse to start if anything differs. One read-only CPU srun (s/o_pre.sh) can check the layout once p/s exists.
- Fake folders added to REMOVAL_CANDIDATES.txt: trinity-3-30 /tmp/a15_rh_990034 and /tmp/q_22c714e1_990034; trinity-1-18 /tmp/a15_rh_990035 and /tmp/q_22c714e1_990035.

## Earlier work for 174198 (kit 929ab213); the method is unchanged
## Files
- fix15/rh/ (shipped to the node's /tmp/a15_rh_174198/rh): go.sh (driver), L.sh (sandbox), accept.py (acceptance stand-in), t2.py, e2.sh, u2.py (launch line, rank shell, rank script), sum.py (summary.json), stop.sh (stop with proof), pre.sh + pre.py (CPU layout pre-check). Checksums in fix15/rh_SHA256SUMS.txt.
- fix15/s/o_start.sh (sha256 f291370c, ship and start in one call), o_poll.sh, o_stop.sh, o_pull.sh; rebuild with s/mk_orchard.sh after any change to rh/.
- fix15/RUN.md: command, durations, stop, success. Test material: fix15/test/, outputs fix15/rd/ (n1.out, n2.out node checks; t1-t3.out Trinity tests).
- Mirror: trinity-1-18:/scratch/jjyeung/n30_mirror/tree_rebuild28/fix15/fix15_rh.tar, sha256 869abbb6 on both nodes.
- Design record: /data2/jjyeung/agent_project_data/distill_design/N_174198_TRAINING_START_REHEARSAL_20261121.md (INDEX line added).

## What runs after a PASS in the job (read from jn7.sh 98edfd9e, kit 929ab213: decoded k/j.json, b/rv.py, t.py, e.sh, u.py, a.py, z.py, pc.sh)
- jn7.sh -> job.sh -> x.py (z.bootstrap writes N/j.sh from k/j.json and runs it with Q_ROOT=/tmp/q_22c714e1_174198, Q_NS=/tmp/q_22c714e1, Q_KIT=X/n, TK_KIT_HOME=N/h, TK_JOBDIR=N/j).
- j.sh runs every step in bwrap with the job folder read-write at Q_ROOT, Q_NS and Q_NJ=/tmp/jjyeung/q_22c714e1, plus NX at X, NR at X/runs, TK_JOBDIR, and the live folder X/o/174198/live. Steps: a.py q -> d.py -> h.py -> rv.py (nice, 8 threads) -> t.py (8 threads).
- rv.py waits up to 7200 s for X/n_r/review.json; on PASS it writes p/rv.json, sets cfg.r1_training.review, writes p/pr.json (sync_preparation), rewrites v.json in place, writes REVIEW_ACCEPTED.json to the live folder.
- t.py: seal, GO, then `python -s -B -m torch.distributed.run --standalone --nnodes=1 --nproc_per_node=4 --no-python /bin/bash b/e.sh python /tmp/jjyeung/q_22c714e1/p /tmp/jjyeung/q_22c714e1/v.json`; e.sh execs u.py; u.py checks RESULT (ADMIT, init_milestone 400), identity, world_size 4, then verify_staging, admit, train(cfg).
- Publishers, all outside the sandbox: pc.py --loop and --loop-small (upload sessions; they watch N/p/q/r on the host), j2.py (periodic session), j6.py (live mirror every 120 s), ep.py, o.py, j7.py (evidence, final publish, hold). Inside the sandbox the only publish path is the live folder bind on /project.
- Rendezvous: --standalone means c10d on localhost:0, an ephemeral port chosen when the job's t.py starts (not visible before). The workers' MASTER_PORT is a second free port chosen by torch's agent, in both the job and the rehearsal.

## The rehearsal (ORDER 1757Z item 1)
- Layout: the job folder read-only at /tmp/q_22c714e1_174198, /tmp/q_22c714e1 and /tmp/jjyeung/q_22c714e1; p/s a bind of the real directory. The kit's bwrap is 0.9.0, which has no --overlay, so the upper layer is bind-composed: scratch folders under /tmp/a15_rh_174198/run_<UTC>/w with every job entry bound read-only into them, level by level (top, p, p/q). Scratch holds v.json (a copy), p/rv.json, p/pr.json, p/q/r, j, cache, tmp, rp (= X/runs), X/o, X/ck and the live folder. The frame map is the kit's (Q_E4 -> /tmp/jjyeung/q_22c714e1/p/q/f/<sha256 of X/data2root>). L.sh refuses any writable bind whose source lies outside the run folder.
- Environment: j.sh's own (lines 12-63, tk_env, tk_pythonpath c, OMP 8 for the two steps), with Q_ROOT/Q_NS/Q_KIT/TK_KIT_HOME/TK_JOBDIR/TK_JOB_START read from the running j.sh (TK_JOB_START 17:52:32Z). The sandbox values reach bwrap through --setenv; the host-side driver keeps its own scratch TMPDIR and caches, so no host command writes into the job folder.
- Acceptance: accept.py, run as j.sh runs rv.py, applies rv.run's receipt checks and its PASS branch with the kit's own rv functions at the job's paths, on a stand-in record whose evidence key is A15_REHEARSAL_STAND_IN_NOT_A_REVIEW. It lives only in scratch.
- Training: t2.py = t.py with the c10d rendezvous spelled out on localhost:29517 (the driver picks the first free port from 29517, below the ephemeral range); e2.sh = e.sh; u2.py = u.py with train(cfg, smoke_steps=2) and logging wrappers (stages, each optimizer step's stream means, finiteness, step time, peak memory; every exception with its traceback).
- Publishers: none started (pc.py loops, j2.py, j6.py, ep.py, o.py, rd.py do not run). Pointed at scratch: the live folder, X/runs, X/o, X/ck, the run output p/q/r. The smoke length writes no checkpoint, export or step-0 export; stop.request is pc.py's file and is never written.
- Guards: refuses to start unless WAITING_REVIEW.json is present, the job's start has not begun (no n_r/review.json, p/rv.json, t.log, REVIEW_ACCEPTED or REVIEW_REFUSED), j.sh is the kit's inner shell, four GPUs are visible with under 1 GiB each and no compute process. During the run it stops the ranks within 5 s if any start marker appears.
- Stop and proof: budget 800 s after the start, srun timeout 870 s with KILL 20 s later; the cleanup TERMs the process group and every process marked A15_RUN=<run> (torch starts workers in new sessions, so a group kill alone misses them), KILLs after 10 s, then logs the marked processes left, the ps lines naming the run, GPU memory and compute apps. stop.sh does the same on demand.
- Logs: run_<UTC>/log (go.log, accept.log, ev_rank0-3.jsonl, smi.csv every 2 s, t.raw.log unscreened, t.log screened by the kit's l.py, proof.txt, job_before/after.txt); summary.json (ranks up, time to first step, losses per stream and rank, finiteness, step time, peak GPU MiB per GPU and the tree's peak allocation per rank, errors with tracebacks).

## Trinity tests (ORDER item 2; no GPU)
- Fake job folder (test/mkfake.py): the kit layout from W/w33n/n_go (seal 929ab213, j.json b718d5d9), the real tree extracted at p/s as a.py extracts it, a fake config whose code pin is the kit's own source seal k/7.json, pins named under /tmp/jjyeung/q_22c714e1. bwrap 0.4.0 and the CPU venv p1cpu stand in for the kit's.
- trinity-1-18 test 1 (18:23Z, rd/t1.out): bwrap mounts built (322 args); acceptance stand-in PASS at the job paths (p/rv.json, p/pr.json, v.json written in scratch only; the fake folder's p has no rv.json or pr.json, its v.json unchanged); t2.py's launch line ran torch.distributed.run on four CPU ranks with rendezvous localhost:29517; all four ranks ran u2.py's checks and the tree's authenticate() under the layout: PASS, commit sha256:9d2bbb8a (the kit's seal), tree path /tmp/jjyeung/q_22c714e1/p/s/.../carrier_c1_run.py, no symlink; cleanup proof empty.
- trinity-1-18 test 2 (18:27Z, rd/t2.out): stop.sh on sleeping ranks: all marked processes and both drivers gone in 18 s; driver budget (45 s): ranks stopped, nothing left. (In test 1, my test script called stop.sh without the fake job number, so that one stop test ran into its 240 s budget and cleaned up by itself; test 2 redid it correctly.)
- trinity-1-18 test 3 (18:31Z, rd/t3.out), the final rh: dry run PASS on four ranks, authenticate sha256:9d2bbb8a; pre.sh probes: scratch paths writable, RESULT.json, r.json, j.sh, p/s and p/q/f refuse writes (EROFS); nothing left.
- Not testable without GPUs: model load, fla check, NCCL, the two steps, GPU memory; nvidia-smi sampling and the GPU guards ran only on the node checks.

## Node checks on 174198 (ORDER item 3; two srun --overlap calls, CPU only, 18:09Z and 18:28Z; rd/n1.out, rd/n2.out)
- orchard-community-3, kernel 6.17.0-1016-gcp, 48 CPUs, 1842 GB memory, /tmp free 5.4 TB, four H100 80 GB at 0 MiB with no compute process; my step sees CUDA_VISIBLE_DEVICES=0,1,2,3.
- Job folder /tmp/q_22c714e1_174198 is a real directory; /tmp/jjyeung exists on the host and /tmp/q_22c714e1 does not (the namespace names exist only inside the sandbox). At 18:28Z p/ held i and s (a real directory), p/q not yet; the live folder X/o/174198/live exists; X/n_r does not exist.
- Kit bwrap: /project/community/jjyeung/cp4tk_rt/kit/bwrap, bubblewrap 0.9.0, no --overlay; overlayfs is in the kernel but unusable through this bwrap.
- Ports: nothing listens in 29500-29539.
- Layout pre-check on the real job folder (pre.sh, 379 bwrap args): the tree's authenticate() on 174198's extracted p/s returns sha256:9d2bbb8a; probes landed only in scratch; the host job folder has none of them. One probe read "OPENED FOR WRITE" for p/q/RESULT.json only because p/q did not exist yet, so the scratch p/q was empty and the probe created the file in scratch; the host has no such file.

## Expected time (RUN.md)
Guards, layout and acceptance 10-60 s; the rank-0 preparation check about 250 s after the launch (fix14's measurement on 174134); model load and the two steps never measured (my guess 3-8 min); hard stop 800 s after the start; everything ends within 15 min.

## Risks
- A write the job's sandbox allows but my layout does not (an unknown path under h/, x/, live_spool or s/): EROFS with its traceback in summary.json. That would be a false failure of my layout, not of the kit.
- sqlite databases in WAL mode on a read-only bind would not open in mode=ro.
- If the model load or the steps are slow, the 800 s budget may end before step 2; summary.json then shows each rank's last stage.
- The four ranks load the model inside the job's 800 GiB memory cgroup, as the real start will (anon 3.6 GiB at 18:26Z).

## Housekeeping
- REMOVAL_CANDIDATES (fix15/REMOVAL_CANDIDATES.txt): fix15/kit/n_go/b/__pycache__ (made by my local reads; fix15/kit2 is the clean copy); on trinity-3-30 /tmp/a15_rh_99001{5..9}, /tmp/q_22c714e1_99001{5..9}; on trinity-1-18 /tmp/a15_rh_990015, /tmp/a15_rh_990025, /tmp/q_22c714e1_990015, /tmp/q_22c714e1_990025 (fake test folders, each under 15 MB); on the node /tmp/a15_rh_174198/pre_* (probe files; they end with the job).
- At 18:19Z the rm_guard hook queued one deletion command of mine in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md (fake test folders on /tmp of trinity-3-30). It is obsolete: discard it, do not run it.
- Orchard calls: 18:09Z and 18:28Z (19 min apart). Trinity ssh: trinity-1-18 at 18:23Z, 18:27Z, 18:30Z, plus the mirror at 18:31Z.
