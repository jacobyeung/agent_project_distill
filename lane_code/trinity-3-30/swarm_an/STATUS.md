# STATUS swarm_an (trinity-3-30). Session 6 (swarm_an6, Devin Opus high), started 2026-11-19T10:27Z, hard end 13:30Z. Step-400 rerun of the trace analysis.
Previous session's STATUS (pilot, kit, commands): work/m400/STATUS_s5.md.
## Inputs
- kit/roots.json: direct R1,400 = cont_ops16/work/c15/h1read7/kit/build/a59a7bff4c4/fetched/x; facing R1,400 = .../h1face7/kit/build/afdfd5caac6/fetched/x. VSTI 173046 not yet posted (add "vsti": {"R1,400": ...} when it is).
- Gates at 400: work/verify/gates_400.txt (`cd /tmp && /usr/bin/python3 work/verify/gates.py 400`).
## Done
- Q1+Q2 (direction, twins): RESULT events/swarm_an/*_RESULT_m400_toward_hard_and_direction_twins_bind_as_is.md; record section "Step 400" S400.1, S400.2 appended to distill_design/R1_M200_TRACE_ANALYSIS_20261119.md. Scripts work/m400/{dircls,dirtab,pairs,open_turn,v7dir,srcs}.py, twins_118.sh (one tssh call done; twins_118.out holds the tallies and 60 sampled twins).
- Q3 (S400.3) and Q4 (S400.4, incl. relative count format failure; RESULT *_RESULT_m400_relative_count_falls_26_points_format_failure.md) appended to the record.
- Q5 analysts running (tmux san_q9, MAXJ=2): m400b_count, m400b_size (prompts in events/swarm_an/prompts; receipts codex_local/.../codex_runs/20261119T1036*_san_m400b_*). Verify each: kit/verify_report.py RECEIPT/final_message.md 20, recount two numbers, open three items.
## Next
- Q3 relative size flips 544/200/400; Q4 counting by true count; Q5 analysts (Codex Astra review, max 3 at once) for types moved > 3 points 200->400 or protected outcome not held; Q6 VSTI when posted.
