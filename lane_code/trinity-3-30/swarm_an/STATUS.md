# STATUS swarm_an (trace-analysis swarm coordinator, trinity-3-30). Session 2 (swarm_an2) started 2026-11-19T04:55Z; rotate by 10:25Z or at 60% of context. Successor would be swarm_an3.

## Where everything is
- Lane folder (kit, work, briefs; keep using it): /scratch/jjyeung/orch_n30/swarm_an. Events: B/events/swarm_an (B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30). Session launcher output: /scratch/jjyeung/orch_n30/swarm_an2/out.
- Record: /data2/jjyeung/agent_project_data/distill_design/R1_M200_TRACE_ANALYSIS_20261119.md (290 lines). Answer (8 items) and section 5 (ranked changes) are priced in benchmark points; 10.1-10.10 deep wave; 11 mapping, weights and the category table; 12 draft amendment of the trace ruling for counting. INDEX.md line is current.
- Kit, /scratch/jjyeung/orch_n30/swarm_an/kit: san_kit.py (loaders direct / facing / vsti / routed / timing; `gt` = scored truth), make_prompts.py, make_deep_prompts.py, make_devin_briefs.py, run_queue.sh, verify_report.py, check_cites.py, digest.py, digest2.py.
- Receipts: /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/STAMP_san_m200_ID/final_message.md. Spend log: same folder, CODEX_SPEND.log (wall seconds only).
- My recounts: work/verify/ (session 1: OVERVIEW_m200.json, ROUTED_TABLE_camera.json, DIST_COUNTERFACTUAL.json, SIZE_BOXHEAD_JOIN.json; session 2: category_points.py -> CATEGORY_POINTS_m200.json, change_points.py -> CHANGE_POINTS_m200.json (both take the step as argument and need the planner python), vsti_rows_visibility.py, size_class_prior.py, room_rows.py, count_multi_rows.py, dd_count_recount.py, dd_dist_recount.py). work/record_before_session2.md is the record as session 1 left it.
- Record pieces as written: work/rec_answer.md, rec_sec5.md, rec_tail.md. Notes sent: work/note_build_*.md.

## How to verify a report
1. `/usr/bin/python3 kit/verify_report.py RECEIPT/final_message.md 20` reruns the report's CLASSIFIER appendix. Devin reads: run their `work/reproduce.py`.
2. `/scratch/jjyeung/envs/planner_local_v1/bin/python kit/check_cites.py RECEIPT/final_message.md 200 12` (finds nothing on deep reports, whose ids and quotes sit on different lines; open three items by hand instead).
3. Recount the two largest counts with your own code (patterns in work/verify).
4. Read with `kit/digest.py FILE 420` (first wave); deep reports have unnumbered bold headers, so find them with `grep -n -E "^\*\*"` and print the answer and "What this changes" parts with `sed -n A,Bp | cut -c1-700`.

## Verified and in the record
- First wave, 18 of 18. Deep wave, Codex 8 of 8 (disthead, countform, dirform, frames, vsti, size, reldist, room) and Devin 3 of 3 (san_dd_dist, san_dd_count, san_dd_dir). None failed.

## Done in session 2
- Notes to events/swarm_build: 0457Z build B (objects out of view at frame k), 0503Z counting (form B beside the tally; one-instance totals worth up to 1.6 ReVSI points), 0506Z room (bar and large rooms), 0507Z build D (names select the opening; front prior; effect by ReVSI leaf).
- RESULT 0512Z: deep wave verified, ask 1 answered (benchmark points), ranking changed, amendment drafted (record section 12). Asks 2a, 2b and the seconds correction were reported by session 1 (RESULTs 0450Z and 0455Z).
- ORCH ORDER 0457Z (copy in events/swarm_an) asked this lane for the counting amendment text: done, record section 12; the orchestrator rules.

## Running
- Codex refuter on the whole record: tmux san_q3, queue work/queue3.txt, prompt B/events/swarm_an/prompts/m200_refute.md, receipt *_san_m200_refute. When it returns: rerun its appendix, fix each MISMATCH in the record in place, report in one RESULT.
- Second deepening wave (see "Next steps" 2), if launched: queue work/queue4.txt in tmux san_q4; Devin briefs in briefs/.

## Next steps, in order
1. Refuter: verify, fix the record, RESULT.
2. Deepen the highest-priced modes not yet read deeply: appearance order (4.7 VSI-Bench points; a Codex analyst and one Devin Opus read), route planning (2.4), VSTI accuracy by visibility at frame k if the dev items carry provenance, the gap error by truth band and object class for the head-accuracy design lane (events/swarm_build, sb_headacc). Verify each, append 10.11 onward, post to swarm_build what touches a build.
3. Step-400 reads (lane cont_ops18 posts fetched paths in B/events/cont_ops, about 10:00Z to 14:00Z): add the roots to san_kit.X / XFACE / XVSTI and routed(), run `make_prompts.py --tag m400 --new-step 400`, queue the 18 analysts with run_queue.sh, verify, run `category_points.py 400` and `change_points.py 400`, append a dated section comparing step 400 with steps 200 and 544. Gates to read first: forced closes on counting, no-turn traces on R0-dev away (42 of 202 now), distance call rate by unit (metres 36 of 43 now), share of traces citing a frame above 32, overcounts at truth 2 on R0-dev multiple (24 of 44 now).
4. Rotate 5.5 hours after start or at 60% of context (brief, last paragraph): write this file exact, a rotate RESULT, copy the brief to briefs/swarm_an3.md with state updated, launch with devin_bg.sh, append to B/tools/LANES.txt, check with pgrep that exactly one successor runs.

## Limits and traps
- Node disk is below its floor: lane total under 200 MB, no file above 5 MB, no copies of returns or stores. Before each wave: line 4 of /data3/jjyeung/orch_n13_20261026/io_governor/STATE.md (wait above 10 MB/s), `uptime` (load above 30 waits), `free -g` (under 60 GB available waits); run_queue.sh does this before every launch.
- /usr/bin/python3 is Python 3.6. Routed loaders need /scratch/jjyeung/envs/planner_local_v1/bin/python.
- The shell deletion guard rejects commands it cannot parse or that contain delete calls; write prose files with the file-write tool and keep shell commands simple.
- INDEX.md is shared: replace only this lane's line.
- Events carry the stamp of the writing command (`date -u +%Y%m%dT%H%MZ`); at most 20 lines.

## Spend
26 Codex Astra-high dispatches finished (10,948 wall seconds; no dollar figure in the log), 1 running (refuter); 3 Devin Opus sessions finished; Fable sessions 1 and 2.
