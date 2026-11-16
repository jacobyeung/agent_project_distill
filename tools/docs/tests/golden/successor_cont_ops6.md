# Lane cont_ops7 (successor on trinity-1-3): successor of lane cont_ops6

Read first, in order: section "Key Trinity Cluster Rules" of `/home/jjyeung/.claude/CLAUDE.md`, then `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md`. They bind and win over this brief; this brief states only what is specific to the lane.
Lane folder `/scratch/jjyeung/orch_n30/cont_ops7` on trinity-1-3. Events `B/events/cont_ops`. Session limit 2026-11-17T02:46Z (UTC); rotate before it as the lane rules say.

## Budgets (inside these, act without asking)
| Budget | Value | Inside it | Above it |
|---|---|---|---|
| Lane folder | 20 GB | act without asking | QUESTION event with your default, then continue on the default |
| Free space on trinity-1-3 `/scratch` | at least 300 GB | write without asking | stop writing; BLOCKER event |
| IO class | governed | every stream above 20 MB registers with the IO governor as the lane rules say, all streams of a step at once | anything beyond the class: QUESTION event with your default |
| Session | until 2026-11-17T02:46Z | work without asking | RESULT `rotate` with STATUS.md exact |

Limits: none beyond the budgets above.

## Role
You continue the work of lane cont_ops6. Its STATUS.md is the state: resume from it, and never redo a step it marks done. Read the newest `*_ORCH_*` events in the events folder before acting; a ruling there wins over the predecessor's brief.

## Predecessor
- Brief: `B/briefs/cont_ops6.md`
- STATUS: `B/events/cont_ops/STATUS.md`
- Rotate event: none given; look for the newest `*_RESULT_rotate*.md` in the events folder

## Folders the predecessor used
- `/scratch/jjyeung/orch_n30/cont_ops`
- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops`
- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools`
- `/data2/jjyeung/agent_project_data/distill_design`
- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_d0r`

## Next step, from the predecessor's STATUS (verbatim)
- Watch: tmux `cont6_watch` runs work/d0/jobB/c6/loop7.sh, one ossh call of c6/q3.sh every 10 min (30 polls, to ~15:20Z): all my squeue jobs with partition, .steps/.w.steps, gcs_359fcc3c_m*.done, filtered .err, last 4 metrics rows (four-rank means computed on Orchard), df of r/63e57182. Latest c6/q3.out, history c6/q3_hist.txt. The project metrics file is flushed about every 10 min.
- 10:51Z: steady 140 s/step (step 19 at 10:41:33Z), VQA 0.40, no non-finite. RESULT 1051Z job_b_rate: m50 ~11:55Z, m100 ~13:55Z, m200 ~17:50Z, m400 ~01:40Z Nov 17, leg ends near step 515. Refining RESULT no longer owed.
- RESULT 1020Z job_b_first_steps SENT: admission + gate + steps 1-3 PASS (check c6/check_out.json, exit 0). Expected at 150 s/step: m50 ~12:00Z, m100 ~14:05Z, m200 ~18:15Z, m400 ~02:35Z Nov 17; 24 h leg ends near step 480-500. Owed: one refining RESULT near step 20 (~10:45Z) only if the estimates move.
- RESULT 1029Z read_kit_fixes SENT (fix round 2 done: DIFF_FIX1.patch reconstructed sha 30b614cc, DIFF_FIX2.patch sha b839252d vs snap/readk_fix1.tar sha 34ccc385, 53 tests OK, pins evidence/FINAL_PINS.json sha 07582397, f1f2.py 15e66c80, orchard_launcher.py 9068f83e). ORCH launches a second reader; submit condition (a) = its CONFIRMED file in events/review_d0r/.
- Read submit (brief item 3): (a) MET 10:54Z: events/review_d0r/CONFIRMED_read_kit.md (review_d0r2; pins evidence/FINAL_PINS.json 07582397). A3 I verified against D0's own gcs_359fcc3c_m1.done (105 B; parse_done accepts it for step 1, refuses step 100; copy c6/m1.done). m100 PREPARED 11:04Z: token ae3be05b81a (c6/TOKEN_m100), readk/kit/build/ae3be05b81a/ (BATCH.sh, CONFIG.json step 100). ORCH RUL...
- Admission at 09:44Z (binding.json, attempt_170111.json in $KB/runs/359fcc3c/; copy c6/attempt_170111.json: first_step 1, init m544 sha 1d6eeb28, resume null).

## Task: the predecessor's Do, unchanged unless the orchestrator edits it below
1. Job B's first steps, now: one small poll every 5 minutes through tools/ossh.sh (the predecessor's poll loop and check script are named in STATUS.md): in-job admission, the native first-step gate on all four ranks, then steps 1 to 3 through early_loss_check_d0.py with the VQA reference 2.049. An ALARM, an admission refusal or a failed first-step gate: scancel 170111 and a BLOCKER with the job's last lines (the GO authorizes it). A WARN: a RESULT line. When step 3 has passed: one RESULT event named job_b_first_steps with each loss beside its reference, seconds per step, and the times you expect m1, m50, m100, m200 and m400.
2. The read kit (work/d0/readk): fix round 1 answered the reader's A1 to A3 and B1 to B3. One more round by Codex: the verdict logic must equal the AMENDED stop rule word for word (F1 failing at step 200 or later stops; at step 200 the leg stops if the point estimate of away accuracy is not above step 544's 38 / 20 / 6 on all three levels; at steps 400, 600 and 800 it stops if away accuracy fell below the previous read's on at least two levels while F2 has not passed; F2 in the lower-bound reading with the point-estimate reading beside it is reported and stops nothing; verdicts STOP or CONTINUE with the reason; step 100 gives none), with tests at every boundary. Then one RESULT event named read_kit_fixes with the diff of both rounds against the reviewed kit, the tests and the new pins. I launch a second reader on it.
3. Submit the step-100 read when: that reader's CONFIRMED file is in /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_d0r/, the .done marker of the step-100 export exists, and no job of ours runs on general. Wall time: the shortest honest one (about 01:45:00), the job's clean stop inside it. RESULT with the job id; then the read's numbers as they return (step 100 gives no verdict). The same for step 200 and later reads; a verdict from the script comes to me in a RESULT before anyone acts on it. Lane trin_read3 may read the same exports on a Trinity card if one frees: if its packet arrives first, score it with the same script and say which reader produced it.
4. Watch the run with one small poll every 10 minutes after step 3: steps, losses, exports landing on GCS, project free space. Anything outside the registered rules is a BLOCKER, not a decision of yours.
5. The LEG-S1 continuation packet stays unsubmitted: it needs the user's yes.

## Why
TODO(orchestrator): fill in.

## Do (orchestrator's additions)
TODO(orchestrator): fill in.

## Done when
The predecessor's task is done and one RESULT event says so, or your session limit is near and the RESULT `rotate` and STATUS.md let the next successor resume.
