# swarm_opt STATUS (swarm_opt3 from 11:44Z 2026-11-19, trinity-3-30)
Lane folder /scratch/jjyeung/orch_n30/swarm_opt (trinity-3-30): work/o = Orchard reads (look1/look2), work/prompts = every Codex/Cursor prompt + 1-18 scripts (shipped by `tar cf - scratch/jjyeung/orch_n30/swarm_opt/work/prompts | bash B/tools/tssh.sh trinity-1-18.ib 'tar xf - -C /scratch/jjyeung/orch_n30/so_in && bash .../prompts/<script>'`), work/res = fetched reports/verdicts, work/ncore = N core b19 untar (read only). Events B/events/swarm_opt (OPT_QUEUE.md = per-item numbers). Design record distill_design/TRAINING_LOOP_SPEED_20261119.md (+ INDEX line).
## Models
- NEVER Sol (ORCH ORDER 0849Z; codex_local.sh refuses it). Builders gpt-6-astra (work/prompts/cap.txt=2 per ORCH 1234Z until tree_rebuild12 names build 21h, then 3); reviewers Cursor Opus via work/prompts/cursor_start.sh <name> <prompt> on 1-18 (`agent -p -f --sandbox disabled --trust --model claude-opus-5-5-xhigh`, AGENTS.md = CURSOR_AGENTS.md; verdict REVIEW_VERDICT.md in its folder). Codex sandbox forbids sockets: gloo tests run by the lane in tmux on 1-18.
## Queue runner on 1-18: work/prompts/qrun.sh (queue.txt: name|workspace|prompt|model|marker; starts one per call while running < cap.txt). Ship prompts + run poll: `cd / && tar cf - scratch/jjyeung/orch_n30/swarm_opt/work/prompts | timeout 300 bash B/tools/tssh.sh trinity-1-18.ib 'tar xf - -C /scratch/jjyeung/orch_n30/so_in && bash /scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts/poll118o.sh'` every 10 min. Sol provenance: RESULT 0903Z lists which packages Sol touched and their Astra/Cursor redo.
## Items (1-18 workspaces /scratch/jjyeung/orch_n30/<name>; queue work/prompts/queue.txt, cap.txt=2 (ORCH 1234Z: max two Astra at once until tree_rebuild12 RESULT names build 21h); poll script work/prompts/poll118ap.sh (auto-starts reviews when fixes end); fetched verdicts in work/res/rv3/)
1. tick.sh: DONE v3 (sha 5e26c7a4).
2. launch + mode p: HANDED OVER (RESULT 1142Z). Nothing owed unless tree_rebuild12 asks.
3. step: HANDED OVER patches_b21 (RESULT 1327Z). Kit: Cursor so_cr_step5 GO for continuation (RESULT 1410Z + COPY tree_rebuild). so_step_fix5 QUEUED (LOW: audit cap 520->576, pooled replay/kill rule; kit+NOTE only) -> Cursor so_cr_step6 (auto) -> RESULT final NOTE path to tree_rebuild/r1_ops.
4. read: Cursor so_cr_read5 GO AFTER FIXES (MEDIUM step-600 BATCH.sh lacks cont_ops wrap_batch; LOW pins, NOTE steps, gate profile) -> so_read_fix5 RUNNING 13:56Z -> Cursor so_cr_read6 (auto in poll118ap) -> NOTE to cont_ops.
5. pack: Cursor so_cr_pack_a4 GO AFTER FIXES (MEDIUM verify receipt stale on metadata-only changes) -> so_pack_a_fix4 RUNNING 14:07Z -> Cursor so_cr_pack_a5 (auto) -> NOTE to cont_ops.
6. git: DONE. Round-4 land_kit.py 29dd347d + GIT_OWNER.md installed 13:26Z (backup work/git_backup_r3_1326Z); sync_health f4b0cc83, dry_count 14fd0d44, loop tmux sync_health with LCS_REVIEW2_FIXES=1. Residual LOW accepted (RESULT 1328Z); no more rounds.
7. record only: DONE (OPT_QUEUE row from R1_M200_TRACE_ANALYSIS_20261119.md).
## Corpus leftovers (ORCH ORDER 0827Z; /scratch/jjyeung/orch_n30/corpus/LEFTOVER.md)
- (1) corpus tool: INSTALLED 13:14Z (RESULT 1317Z + COPY events/cont_ops); alias proof clean (0 devrows ids in 6 files). Open LOW for a later round (native row without arm; no arm declaration partial refuses) - not queued.
- (3)+(4) so_corpus_lost PARTIAL: 1 proposed lost entry (out/LOST_LINES.jsonl), 3 adapter gaps, ORCHARD_ONLY_INPUTS.md (26 IDENT archives 383 MB recorded). Fetched to work/res/corpus/.
- (2) analysis tar built work/analysis_tar/analysis_20261119.tgz (7 MB, 506 members) HELD (ORCH 1244Z: no corpus work on 3-30 until user frees space); training tars after step-600 reads (QUESTION 1222Z default).
## Open questions: QUESTION 1222Z corpus leftover (2) training/analysis tars (default 12:50Z: analysis tar once if <20 MB, else governed; training after step-600 reads).
## Older: events/swarm_opt RESULT 0949Z xstore_partial (cross-run native change? default park).

- Wave-2 PARTIALs: so_corpus_fix round 3 (six findings fixed; byte impact for 7 published reads needs absent returns), so_corpus_lost (retained reads + one reported loss; three pilot returns and Orchard task paths unresolved), so_pack_a_fix RUNNING.

- Corpus second copy DONE: gs://cmu-gpucloud-jjyeung/dtc19/c2_20261119.tar 670,085,120 B sha256 9a804903... (RESULT 1131Z); DATA_MAP line + HOWTO section written. Mind leg once after step-600 reads (ORCH). Truncated gs://.../dtc19/c_20261119.tar in REMOVAL_CANDIDATES.
## Next: 10-min polls; each verdict/ending -> next step per item above; RESULT 12:08Z posted (reviews summary). End without successor when only outside things remain >20 min (ORCH 0636Z).
