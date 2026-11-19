# n_ops2 STATUS (successor resumes from this file alone)
Updated: 2026-11-19T22:21Z by n_ops2 (Devin Opus high, trinity-3-30, started 20:42:53Z, hard limit 02:42Z).
Brief: B/briefs/n_ops2.md. B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Events: B/events/n_ops. Predecessor state: /scratch/jjyeung/orch_n30/n_ops1/STATUS.md (watcher, sessions, pointers; still exact).
## State
- Launch not submitted. tree_rebuild16 (successor of 15 at 22:50Z) owns kits, discovery and launch. Discovery job on 24m2c (due ~00:50Z) submits ~01:00Z; launch after kit review + rehearsal + n_review1b PASS + ORCH GO (no fixed forecast yet). Rotation plan: ~00:40Z, before the discovery submission (limit 02:42Z); if discovery is submitted earlier, rotate after its first 30 min, by 02:10Z at the latest.
- Watcher tmux nops_mon alive (pane pid 432537), mon/job=0 (auto-detect), sleep 120. 20:41Z: proj_free_G 362; advanced RUNNING 173258, 173333, 173243 (cont_ops21 / k1fwd1; must yield within 5 min of N's submission).
- Sessions file okh7/x_22c714e1/n_s/sess.json sha256 15c543a1...f800 (minted 18:59Z, expires ~11-26 18:59Z). Ledger: n_ops1/work/ORCHARD_LEDGER.jsonl.
- n_review2 brief exists (B/briefs/n_review2.md, 6299 B, 20:08 local). Start it when prep passes ~75%.
- Kit check (work/kitcheck_tpl.sh) owed when 24k's launch kit is uploaded.
## Next
- Every <=10 min: read mon/last.line, ALERTS.txt, new files in events/n_ops, events/tree_rebuild, inbox.
- At submission: write job id to mon/job, sleep 60, ledger line, confirm name/resources/advanced yield, RESULT job start.
- ORCH ORDER 2157Z: tree_rebuild15 submits a DISCOVERY run (kit q of 24k union, preempt, 48 CPU, 800G, 4 h); I watch it with the launch watcher, report preparation progress (time prep at 48 CPUs) and every refusal with log lines. It claims and gates nothing.
- parse.py change 22:05Z: file mon/noadv disables ADV_OTHERS (discovery job is not on advanced). Tests 32/32, replay 91/0 flags. Backup n_ops2/work/parse.py.bak_2205. For the discovery job: write its id to mon/job, touch mon/noadv, sleep 60. After it ends: mv mon/noadv to mon/noadv.used, write 0 (or N's id) to mon/job.
- WATCHER NOW DUAL (22:19Z): tmux nops_mon runs /scratch/jjyeung/orch_n30/n_ops2/work/monloop2.sh (replaces n_ops1/work/monloop.sh, same mon dir and parse.py). ONE ossh call per interval covers mon (launch job, n_ops1/work/mon, autodetect on advanced) and mon2 (n_ops2/work/mon2: job, sleep, last.line, hist.txt, ALERTS.txt, raw/, extra.sh, noadv already touched). mon2/job=none -> mon only. Interval = min(mon/sleep, mon2/sleep). Restart if dead: `tmux new-session -d -s nops_mon "bash /scratch/jjyeung/orch_n30/n_ops2/work/monloop2.sh"`. Tested 22:19Z with mon2/job=173236 (split OK, FAILED flagged as expected).
- ORCH ORDER 2208Z: discovery (preempt) and launch (advanced) run in parallel; if discovery refuses at a stage the launch job has not passed, I cancel the launch job at once ON tree_rebuild15's WORD. Discovery job id -> mon2/job (sleep 60 early).
