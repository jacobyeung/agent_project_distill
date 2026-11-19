# STATUS swarm_an (Devin Fable xhigh, trinity-3-30) — coordinator of the trace-analysis swarm on R1 step-200 reads
Started 2026-11-19T04:03Z. Rotate by 09:30Z or at 60% context.

## Kit (reusable for step 400)
- Loader: /scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py (reads returns in place; direct/facing/vsti/routed; reproduces SUMMARY.json and the accepted routed scores).
- Prompt generator: kit/make_prompts.py -> B/events/swarm_an/prompts/m200_<id>.md (18 analysts). For step 400: add the roots to san_kit.X/XFACE/XVSTI and routed(), run `make_prompts.py --tag m400 --new-step 400`.
- Queue runner: kit/run_queue.sh <queue file> in tmux `san_q` (max 5 Codex Astra high, governor/load/memory gate before each launch; log out/queue.log; stop with work/STOP_QUEUE).
- Receipts: /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/<stamp>_san_m200_<id>/final_message.md

## Reading of the returns (verified from files)
- report/B2048.json and ON16k.json hold per-item scores only. Traces are in <fam>/a0/results/0/items_a0.jsonl (full 16k generation) and results/budget_2048/0/items_a0.jsonl (scored arm; for a force-closed item its text is only the answer). a7 has no report folder.
- Step 544 dev-S1 and facing twins exist only as the B2048 arm (evalx27/.../merged); step 544 R0-dev has ON16k text plus scores in ITEMS.jsonl.
- VSTI: acb2faedd41 = step 544 base (run 469ddece); a35f73e87f0 = R1 step 200.
- D0 step 200 (ae470417b41) and H1-1 step 100 (a24ea1a1936) builds hold no trace files here (scores only): no trace dose comparison from them.

## Queue 1 (launched 04:11Z): count, dir_hard, rel_dist, routed_dist, rows_a, dir_med, vsti_a, size, app_order, rows_b, facing, dir_easy, routed_disp, routed_rot, route, vsti_b, vsti_c, cot_cost
Verified reports: none yet. Spend: see CODEX_SPEND.log (wall seconds only; no dollar figure).

## Next
1. Verify each report (two largest counts recomputed, three cited items opened); first RESULT with the five highest-priced findings.
2. Devin deep reads (max 3) where a routed placement/usage failure or a mode above 1 point needs it.
3. Record /data2/jjyeung/agent_project_data/distill_design/R1_M200_TRACE_ANALYSIS_20261119.md + INDEX.md line; synthesis RESULT (target 07:30Z).
4. Step-400 reads (cont_ops, 10:00Z-14:00Z): rerun the analysts, append a dated section.
