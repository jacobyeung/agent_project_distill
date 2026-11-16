# Distillation orchestrator handoff manifest, 2026-11-16T10:54:25Z (orchestrator: Claude Code session in tmux distill_orch on trinity-3-30, cwd /scratch/jjyeung/orch_home_distill)

A successor gets full state from THIS FILE plus the design records it names. The running log of every ruling of the night is the tail of ORCH_STATE_SNAPSHOT_20261115T1811Z.md (search it; do not read it whole). Goal, standing rulings and the older do-not-redo list: ORCH_STATE_SNAPSHOT_20261115T0930Z.md. Design records: /data2/jjyeung/agent_project_data/distill_design/ (INDEX.md). trinity-2-18 and trinity-2-28 are unreachable; nothing on their /scratch can be read.

## User rulings of this session, verbatim
- 2026-11-15 (start of session): "You now run on trinity-3-30, in tmux session distill_orch, as a fork of your trinity-2-28 session. trinity-2-28 stopped answering at about 11:15 EST: TCP and the SSH banner respond, but every login hangs. Its /scratch (orch_n28) and your three Devin lanes there (evalx26, k1_ops2, recover_map) are unreachable; treat them as lost, as with trinity-2-18. Re-read /scratch/jjyeung/orch_home_distill/CLAUDE.md and your newest ORCH_STATE_SNAPSHOT. Relaunch the lost lanes on healthy nodes other than 2-18 and 2-28, spread across nodes (USER-RULING 2026-11-14). Probe 2-28 at most once every 10 minutes; if it answers again, stop the older orchestrator process there before acting on any lane, and append that stop to /data3/jjyeung/orch_n13_20261026/STOP_NOTICES.md."
- 2026-11-15, relayed by the main orchestrator as the user's words to it (INBOX_TO_DISTILL_ORCH_20261115T175713Z): "If you now have more time and resources, um you can let distillation train models now. And I was and to use Orchard"
- No answer has been received to any question asked this session.

## Tools
B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. B/tools/launch_remote.sh <lane> <seconds> [min free GB] starts a Devin Opus-high lane on the node it runs on; for another effort: bash B/tools/devin_bg.sh <lane> <brief> <model> <seconds> on the node (claude-opus-5-5-max was used for the design lane). B/tools/evwait.sh 900 is the event loop: run it in the background, read its output file on the notification, re-arm after every firing; it exits at once on *_QUESTION_* / *_BLOCKER_* / inbox files, batches RESULT events, probes trinity-2-28 every 10 minutes (prints N28_ANSWERS if it logs in). B/tools/ossh.sh is the shared Orchard connection. Briefs B/briefs/<lane>.md; events B/events/<folder>/; my answers there are *_ORCH_*.md. Lane rules: B/tools/LANE_RULES.md.
Health checks: lane alive = ssh <node> 'pgrep -u jjyeung -af briefs/<lane>.md' (trinity-3-30: pgrep locally); lane state = tail -n 25 B/events/<folder>/STATUS.md and ls -t B/events/<folder> | head; Orchard = bash B/tools/ossh.sh 'squeue -u $USER -h -o "%i %j %P %T %M %l %R" | grep a15_cot_ap' (jobs named jjy_* on advanced belong to the main project, not to us).

## Active runs (verified by squeue and pgrep at 10:52 to 10:55Z)
| What | Where | State | Check | Next action |
|---|---|---|---|---|
| D0 training leg (first leg under the trace ruling; sealed LEG-S1 trainer, row store v5 4af43b40, warm start from step 544) | Orchard job 170111 (a15_cot_apddbe32d7), advanced, 4 H100, 24 h, running since 07:24:54Z | RUNNING; step 19 at 10:41Z, 140 s/step, VQA 2.05 -> 0.40; exports m50 ~11:55Z, m100 ~13:55Z, m200 ~17:50Z, m400 ~01:40Z 11-17; USR1 at 06:25Z 11-17 near step 515 | lane cont_ops6; B/events/cont_ops/STATUS.md; card B/events/cont_ops/PRELAUNCH_CARD_D0.md | Reads at each milestone with the reviewed kit; verdicts by distill_design/D0_STOP_RULE_20261116.md (amended 09:45Z); a STOP or CONTINUE verdict comes to the orchestrator before anyone acts. The second 24 h allocation (resume from the end slot; GCS fallback if project is full) must be submitted when the first ends, unless a verdict says STOP: not yet ordered. |
| K1 own phase (reads the step-544 depth and gravity heads on 300 captures; with the finished tower phase it tests the deployed grounding pipeline) | Orchard job 170206 (a15_cot_apb7e31d84a90c62f5), general, 1 H100, 3 h; started 10:39:56Z | NOT in squeue at 10:53Z: it has ended; outcome unknown until lane k1_ops5 reports (its first attempt 170193 failed in staging) | B/events/k1_ops3/ (newest RESULT or BLOCKER) | On success: convert, tables on the frozen 296-capture set (amendment 1) with manifest v2 (amendment 2), refit under planner_local_v1, report; e3's deployed column (record E3_BACKEND_GEOMETRY_PRICING_20261116.md holds the command). On failure: fix, reader, resubmit; general is ours one job at a time. |
| VSTI-450 native read, camera calls only (first official native read) | not submitted; kit V1c code tar dc40cf60 CONFIRMED (B/events/review_vsti/CONFIRMED_dc40cf60.md); inputs b.tar and d.tar uploading (tmux nr4_upb0, nr4_upd0 on trinity-1-3) | lane native_r5 submits ONE job under my conditional GO (B/events/native_r4/*_ORCH_GO_conditional_vsti.md as amended by *_ORCH_ORDER_submit_v1c_no_v1e.md): inputs hash-verified on Orchard, sbatch --nice=200, deadline 16:15Z | B/events/native_r4/STATUS.md | Report camera types first, then the per-type table with refused-call cost, proof outcome and frames line; record distill_design/VSTI_NATIVE_CAMERA_READ_STEP544_20261116.md. Must be off general before the D0 step-200 read (~17:50Z). |

## Lanes alive (Devin processes; limit UTC on 2026-11-16)
| Lane | Node | Limit | Task | Events folder | tmux it owns |
|---|---|---|---|---|---|
| cont_ops6 | 1-3 | 14:46 | D0 operator: watch, milestone reads on Orchard general, verdict script f1f2.py; submits a read when CONFIRMED_read_kit.md exists, the export's .done exists and general is free | cont_ops | cont6_watch |
| review_d0r2 | 1-3 | 12:35 | confirms the D0 read kit's two fix rounds; writes CONFIRMED_read_kit.md into events/review_d0r/; then exits | review_d0r | - |
| native_r5 | 1-3 | 16:20 | VSTI packet, submission under the conditional GO, watch, report | native_r4 | nr4_upb0, nr4_upd0 |
| trin_read3 | 1-3 | 15:45 | second read path on a Trinity card: 20-item proof when the base has landed and a card is empty on 1-18 or 1-3, then step-544 baseline and D0 milestones; 300 GB free-space floor on 1-3; no removal | trin_read | trr_cardpoll, trs_frrest |
| tree_rebuild3 | 1-3 | 12:16 | build 6 of the next-leg tree (contracts r6, orders T1, T3-T5, init as a pinned input, square feet as a valid direct answer unit); asks for the second review when the integrated suite passes | tree_rebuild | tree_rebuild_b6 |
| k1_ops5 | 1-18 | 10:58 (ending) | K1 operator; successor k1_ops6 to be launched on its rotate event (brief pattern: B/briefs/k1_ops5.md) | k1_ops3 | - |
A lane ends at its limit or when its task is done, without notice beyond a rotate event: launch the successor from the predecessor's brief pattern on that event. A reviewer lane exits after its verdict; a fix confirmation needs a new reader lane that writes into the folder the operator's condition names.

## Survives the orchestrator session / dies with it
- Survives: Orchard jobs; every Devin lane until its limit; their tmux sessions (builds, uploads, pollers); the IO governor and node agents (tmux iogov_agent on each node); Codex builds in flight.
- Dies: the evwait.sh background task (re-arm it: bash B/tools/evwait.sh 900 2>&1 | head -n 14, in the background); the queue watcher (bash /home/jjyeung/agent_project_distill/agent/scripts/queue_watcher.sh /home/jjyeung/agent_project/agent/agentic_information_5.0/EXPERIMENT_REQUEST_QUEUE.md 120); the 2-28 probe (inside evwait). Without an orchestrator no lane question is answered and no successor is launched: within about six hours every lane has ended. The unattended moments that matter: the D0 step-200 verdict (~18:00 to 19:30Z) and the second D0 allocation at 06:25Z on 11-17.

## Results banked this session (each has a memory note and a design record)
- Official VSI-Bench direct, step 544, six direct tasks 68.77 [66.5, 71.0] vs f17 65.60 (OFFICIAL_VSI_DIRECT_STEP544_20261115.md). ReVSI direct, five categories 64.94 [61.3, 68.4]; away 14.0 vs toward 88.3 (REVSI_DIRECT_STEP544_20261115.md).
- First native routed read, dev-S1, step 544 (Orchard 170056; NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md): programs emitted 99-100%; camera 82.3 / 94.7 / 75.7; distance 29.9, room 53.9; the student answers in metres whatever unit is asked. Paired with the parent's direct answers (confirmed): distance -9.0 [-17.0, +0.2], all on non-metre questions; no resolvable difference on metre questions; the parent trained on dev-S1 scenes.
- Design after the read and its verdict (A0_AFTER_NATIVE_READ_DESIGN_20261116.md; B/events/review_a0d/REVIEW_VERDICT_A0_DESIGN.md): keep the route table (programs for absolute distance and camera types; room direct; recovery and unit rows). The benchmark evidence for routing distance is unresolved off the selection scenes (+0.42 [-0.23, +1.08] VSI).
- E3 geometry pricing (E3_BACKEND_GEOMETRY_PRICING_20261116.md): no scale or floor rule makes room routable (63.3 vs f17 direct 63.4) or adds more than about 3 points on distance.
- K1 tower phase complete 300/300; amendments 1 and 2 registered; refit inputs recovered (K1_REFIT_INPUT_RECOVERY_20261116.md).
- D0: rows v5 admitted (D0_ROWS_ADMISSION_20261115.md); CPU proof passed both stages; job started, first steps passed. Contracts packet confirmed at revision 6; tree build 5 sealed ba346bd9.

## Pending with the orchestrator
1. K1: read the outcome of 170206; launch k1_ops6.
2. D0 reads: step 100 (~13:55Z, no verdict), step 200 (~17:50Z, verdict), 400, 600, 800, final. Decide and order the second allocation.
3. VSTI read: report the camera types to the user from the lane's RESULT; if the job stops at its deadline with items left, word for the resume job.
4. Register three drafts in B/events/amend3/ after reading them: re-freeze amendment 3, the next-leg init rule (before the D0 step-200 verdict is used for anything but the stop rule), the trace ruling 2.2 evidence line. Open choices are listed in B/events/amend3/20261116T0643Z_RESULT_amend3_drafts.md.
5. Next leg (A2 = A0 plus geometry fusion): no rows lane is running. Needed before D0 ends or stops: verified first-seen frames for counting and size (the 19,146 procedure-only rows), a share of direct room rows asked in square feet, the kit's frame-host inputs qualified (both kits say GO=false), the tree's second review. Launch a rows lane.
6. Trinity reader: order one reader on its proof RESULT (launcher, stub, camera wrapper, --link-models).
7. Memory note result-vsi-routed-official-20261113 and the trace ruling's section 2.2 still cite evidence the verdict weakened; the memory caveat is added, the ruling text waits for item 4.

## Open user decisions (asked once; never repeat unprompted)
LEG-S1 continuation yes or no (packet ready, unsubmitted); D0's 19,146 procedure-only rows (kept by default, on the card); whether the admins know trinity-2-18 and trinity-2-28 are down; removal lists (per-lane REMOVAL_CANDIDATES.md; Orchard okit temp folders; the reader lane's copies on trinity-1-3 will reach several hundred GB); one false-positive row in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md.

## Do not redo
- No direct reads of the parent or f17 on the 450 camera keys (a 41 to 72 point gap changes no decision). No scale or floor rule runs (E3). No V1e of the VSTI kit; the staged code tar is dc40cf60. No second pull of the base tar (lane trin_read3 holds it). Nothing staged on trinity-0-13 (/scratch at main's 150 GB floor) or trinity-1-13 (71 GB free). No LEG-S1 continuation without the user's yes. No official native read of VSI-Bench or ReVSI before the re-freeze; on VSTI only camera calls are served. No deletion command by any agent.

## Footguns learned tonight
- Slurm start estimates on Orchard are upper bounds: D0 started 15 hours early and a general job within eleven minutes. Have the babysitter and the read kit ready at submission.
- A registered alarm or stop bar must be checked against a measured first batch and against its sample size before launch: D0's first alarm would have cancelled the job at step 1 (new trace forms raise VQA loss twentyfold), and its facing bar was unreachable at step 200 with 50 twins per level.
- A rehearsal that swaps a fixture for the production config proves nothing about the config (K1 job 170193 died on a prose string in a verified field).
- Governor: a registered stream's root PID must never exec another program; the mover's parts run at priority 1, so urgent small streams register at 0.
- Before telling the user what a comparison means: who trained on the evaluation scenes, and which units each number covers.
