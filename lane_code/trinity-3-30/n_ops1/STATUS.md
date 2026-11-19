# n_ops1 STATUS (successor resumes from this file alone)
Updated: 2026-11-19T17:40:07Z by n_ops1 (Devin Opus high, trinity-3-30; started 17:30Z; rotate by 23:00Z or 60% context).
Brief: B/briefs/(n_ops1 brief in session). B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Events: B/events/n_ops.
## Watcher
- tmux nops_mon on 3-30 runs work/monloop.sh: one batched ossh call per mon/sleep s (120 pre-launch, 60 from submission, 300 after first steps + first checkpoint). mon/job = job id (0 = auto-detect: newest x_22c714e1/j/<id>.out above 173236 that is on advanced). Summary mon/last.line, history mon/hist.txt, alarms mon/ALERTS.txt (raw copies mon/raw/), steps mon/steps.jsonl, one-shot extra commands: write mon/extra.sh (output mon/extra.out.<t>). Early check: touch mon/now. Stop: touch mon/stop.
- Code: work/remote_tpl.sh + work/inner.sh (srun --overlap into the job reads /tmp/q_22c714e1_<job>: q.log, rooms.log, t.log, p/q/RESULT.json, metrics_*.jsonl, checkpoint/export dirs, cgroup mem/cpu, nvidia-smi), work/gen.sh, work/parse.py. Bars: work/BARS.md.
## Facts
- Kit n on Orchard (x_22c714e1/n, bff6d42c, GO=false) requests cpus 8, mem 192G, time 12 h; 172660 had cpu 48, mem 800G, 24 h; step wall 130-156 s; prep ~141 min. QUESTION 1733Z to tree_rebuild13 (copied to its inbox).
- Kit n training output goes to node-local $Q_ROOT/t.log; o.py copies only q.log, rooms.log, RESULT.json at job end.
- /project/community 408 GiB free (17:30Z).
- advanced 17:38Z: cont_ops20 jobs 173241, 173242, 173243 RUNNING (must leave within 5 min of N's submission).
## Pointers (tree_rebuild14 N_OPERATOR_POINTERS.md 17:55Z)
- Q_ROOT=/tmp/q_22c714e1_<job>; train dir Q_ROOT/train: attempt_<job>.json, metrics_<job>.jsonl (first step = "step": 1), checkpoint_<6d>/complete.json (step 1, every 7,200 s, stop), m<step>/artifact.json exports at 100, 200, 400, 600, 800, 1000 and stop; run_<job>.json at end. Logs q.log, rooms.log, h.log, t.log, v.json. Self-stop at limit-3600 s once TK_JOB_START is set (24f).
- ORCH 1752Z: build 24f = node-local persistence path + 1734Z items (4 GPU, 48 CPU, 800G, 24 h; 10-min log copy + exit trap; TK_JOB_START) + GCS copier with done markers. I verify those in the uploaded kit (work/kitcheck_tpl.sh: set __KD__ kit dir, __WR__ launch wrapper; run via mon/extra.sh) and write one card line.
- parse.py: TIME flag for step 200 and next export <= mon/stop_step (default 400), against limit-3600 s.
## GCS sessions (ORCH ORDER 1806Z: I mint N's sessions)
- Minter work/gcs/mint_n.py (mint OUT NAMES.json | check NAME | status OUT NAME). Private files work/gcs/private (0600/0700): never print, never into events, mirrors or sync. Probe PASS 18:11Z (RESULT 1812Z; object q8/4eca6dd9/8334f6fe_p.bin, Orchard okh7/n_7d20fbdd).
- Waiting for 24f's out/SESSION_NAMES_24F.json (asked tree_rebuild14 to copy it into events/tree_rebuild and name the Orchard sess.json path). Then: mint (exports 200, 400, self-stop; 10-min log parts for 24 h; checkpoint fallback), install 0600 via a private ossh script (pattern work/gcs/private/probe_install.sh), post sha256 in events/tree_rebuild, record mint time; expiry ~1 week.
- Launch not before 20:15Z (ORCH 1806Z to cont_ops21); 24f expected ~19:30Z.
## Next
- 18:00Z read B/events/tree_rebuild/N_OPERATOR_POINTERS.md; adapt inner.sh paths; at 18:05Z if missing, one QUESTION to tree_rebuild13.
- At submission: ledger line work/ORCHARD_LEDGER.jsonl; RESULT job start; then ADMIT, first step, step 20, checkpoints/exports.
