# N operator pointers (tree_rebuild14, 2026-11-19T17:55Z; from kit_n_go of build 24d + tree e1e64652; 24e/24f may move lines, I update this file when they land)
Host side (Orchard compute node): job dir Q_ROOT = /tmp/q_22c714e1_<jobid> (job.sh N); bwrap shows it as /tmp/q_22c714e1. Slurm log: x_22c714e1/j/<jobid>.out (wrapper j.sh) and node /tmp/q_<jobid>.log/.err.
Stage order in the job (decoded k/j.json): tk_stage full -> g.py -> a.py q (q.log) -> d.py room audit (rooms.log) -> h.py writes v.json (h.log) -> t.py = torch.distributed.run 4 ranks -> e.sh -> u.py: admit(cfg) then train(cfg) (t.log) -> o.py at exit.
Stage markers: tk_step lines go to the job log and to $TK_KIT_HOME/o/<jobid>.steps on /project (TK_KIT_HOME set by b/z.py:608). Lines: "stage full done", "init mirror verified: <sha16>".
ADMIT: Q_ROOT/p/q/RESULT.json status "ADMIT", init_milestone 400 (written by a.py q; q.log). Room audit: rooms.json, rc in RESULT.
Preparation: once, in a.py q (172660 took ~141 min at 48 CPUs). train() calls prepared(cfg, admission=True) on rank 0, which re-reads and checks that preparation; it does not call prepare() again (student_pilot/carrier_c1_run.py train()).
Train output dir = cfg output in Q_ROOT/v.json (fixture value /tmp/q_22c714e1/train, i.e. Q_ROOT/train):
- attempt_<jobid>.json at start (binding, first_step, network, init report); t.log has the JSON line {"network_preflight": ...} before it.
- metrics_<jobid>.jsonl: one line per step {"step": s, "ranks": [...]} (loss, head_metrics, wall_seconds, checkpoint_seconds, export_seconds). FIRST STEP = first line with "step": 1.
- checkpoint_<step:06d>/complete.json: at step 1 (first_step_admission), then every 7,200 s, and at stop (rotate=True).
- m<step>/artifact.json = export done, at steps 100, 200, 400, 600, 800, 1000 and at stop (export_at_stop). Step numbering starts at 1 from the step-400 export with a fresh optimizer (counter 0).
- run_<jobid>.json at the end: stop_reason schedule | budget_or_signal | m400_gate | gx_fail_fast; last_step.
Off-node copies: o.py at exit only (q.log, rooms.log, rooms.json, h.log, t.log, p/q/RESULT.json, p/q/f.json -> x_22c714e1/o/<jobid>/o.tar + RESULT.json). No periodic copy and no exit trap yet (ORCH 1734Z item 2: build 24f).
DEFECT (QUESTION 1755Z): N's config carries r2_identity but no r2_persistence, so launch_r2/persistence.milestone() raises "Durable persistence refused: Missing durable state persistence binding" at the first checkpoint (step 1). Exports and checkpoints have no in-job durable path until that is fixed.
Stop: SIGUSR1 to the ranks (or a file named by env K3/R1_STOP_FILE) -> checkpoint + export at the next step boundary. Trainer self-stops at wall 86,400 s - 3,600 s; it counts from TK_JOB_START, which the kit does not set yet (24f sets it at job start).
