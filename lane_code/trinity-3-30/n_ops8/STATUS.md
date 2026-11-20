# n_ops8 STATUS (successor resumes from this file alone)
Started 2026-11-20T20:03Z on trinity-3-30 (6 h limit 02:03Z; plan rotation ~01:00-01:30Z, never near launch first 30 min / first step / export). Brief B/briefs/n_ops8.md. Older state: n_ops7/STATUS.md and earlier.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30.
## Now
- No job of ours on Orchard (squeue -u jjyeung empty 20:03Z). Launch NOT submitted. tree_rebuild22 owns kit (24m4y build), discovery, launch QUESTION (forecast ~23:00Z).
- Project fs 43 GiB at 20:03:39Z (falling slowly). Floors ORCH 1959Z: discovery >=50, launch >=100 (unless ENOSPC test passes per card), CPU jobs >=20, nothing at 0; recovery = above floor 15 min. Owed: posts at 20 GiB, 0, recovery >150 GiB (and floor recoveries).
- ORCH 1959Z item 5 answered: RESULT 2003Z (yifanhe2 19:52Z, sklutter 15:11Z; running 2 / 1).
- Main-project notice NOT sent (at launch QUESTION). Newest known main inbox INBOX_TO_DISTILL_ORCH_20261118T002059Z.md.
- ORCH RULING 2055Z: launch moves to kit 24m4z (ENOSPC fix: local claims, per-allocation GCS objects key+'.j<job>', 104 sessions per job). Launch NOT on old kit. Floors: discovery >=30 GiB if logs node-local (jn2.sh pattern) else 50; launch on 24m4z with jn2.sh >=20 GiB. Discovery still on current kit.
- n_ops8 mints per-job sessions: tool n_ops8/work/gcs/sess_job.sh JOB all [DEST_DIR] (names from y_24m4z.json 3386b525; private/ holds sess_<job>.json + installer; never print). QUESTION 2057Z proposes sbatch --hold -> post id (event or n_ops8/inbox/SESS_JOB) -> mint+install -> submitter scontrol release. Await answers.
- Watcher updated for 24m4z: parse.py 586cb4a9 (HELD flag at 15 min, LSTATE done markers), inner.sh @@LSTATE; backups *.f74be9dd, inner.sh.61ef1f45. RESULT 2100Z posted.
## Watcher
- tmux nops_mon (n_ops2/work/monloop2.sh). mon job=0 sleep 120, mon/noadv present (mv to noadv.used at launch submission); mon2 job=none.
- Helpers n_ops8/work/{chk.sh, wait.sh, w.sh, wit.sh, cyc.sh} (L=n_ops8). wit.sh still J=173661 / log a15_cot_ap24d9b8e2: edit both at the discovery.
