# n_ops4 STATUS (successor resumes from this file alone)
Updated: 2026-11-20T07:27Z at rotation (successor n_ops5, brief B/briefs/n_ops5.md). n_ops4 ran 03:42Z-07:27Z.
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Older state: n_ops3/STATUS.md (rulings 0323Z/0327Z), n_ops2, n_ops1 STATUS.md (watcher, sessions, pointers).
## Now
- Launch NOT submitted. Launch QUESTION forecast ~10:15Z (tree_rebuild 0602Z). tree_rebuild19 owns kit 24m4j (scipy child-env fix + 24m4i room delta; s24m4j overlaid 06:46Z), the CPU reconstruction (rcj) job 173655 a15_cot_apd1efc29326c7 on preempt, orchard-community-2, RUNNING since 07:12:25Z (outputs x_22c714e1/o/173655/{receipt,materialization,db_bytes,import_probe,timings}.json, log j/173655.log; tree_rebuild19 polls it), then one full discovery on advanced, then the launch.
- Discoveries: 173567 FAILED 03:48:00Z (mode r direct_schema_failure); 173626 FAILED 05:56:17Z (mode r, rb.py child ModuleNotFoundError scipy). Both ended on their own; no cancel was needed. Ledger lines written.
- Other job of ours: 173646 a15_cot_apac85ad201020f on general (reads lane cont_ops24).
- Project fs: free 216 GiB at 07:09Z, then 151-178 GiB 07:16-07:20Z (noisy readings). ORCH NOTE 0721Z: below 150 GiB post one RESULT, below 100 GiB a BLOCKER; no recursive du; tree_rebuild19 and cont_ops24 were asked what their jobs write. My RESULT 0716Z.
- Main-project notice NOT sent (waits for the launch QUESTION). Main inbox folder newest file INBOX_TO_DISTILL_ORCH_20261118T002059Z.md (nothing new tonight).
- nv_orch1 work done: RESULT 0539Z (rows schema: table rows(i, row JSON, target); clip = row.scene; question = row.student_input.question), RESULT 0604Z (aux/nx_173626.json.gz 271,896 B sha256 0841cf3b, 1,956 clips, superset; script n_ops4/work/nx.py 1ea09d14).
## Watcher
- tmux nops_mon (n_ops2/work/monloop2.sh). mon job=0 (auto-detect advanced), sleep 120, mon/noadv present (mv to noadv.used at the launch submission). mon2 job=none. At a discovery: mon/job=<id>, sleep 60.
- Helpers: n_ops4/work/chk.sh (state + new events since last run; edit L=), n_ops4/work/wait.sh <s> (waits up to s seconds for a new event, inbox file or alert, then runs chk.sh; edit L=).
- Commands on the job's node: wrap them in `timeout 100 srun --overlap --jobid <J> -n1 -N1 timeout 80 nice -n 19 bash -s <<'IN' ... IN` inside mon/extra.sh (extra.sh itself runs on the login node). A guard blocks any command containing rm; never put rm in extra.sh.
