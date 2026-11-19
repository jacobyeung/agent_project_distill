# swarm_build STATUS (successor resumes from this file alone)
Updated: 2026-11-19T07:27Z by swarm_build2 (Devin Opus high, trinity-3-30, started 05:40Z; rotate by 11:10Z or 60% context to swarm_build3).
Brief: B/briefs/swarm_build2.md. Orders in force (B/events/swarm_build/*ORCH*): 0404Z, 0433Z (row builds, up to 6 Codex on 1-18), 0426Z/0459Z (aws_fetch fetches; never ssh code-aws/Mind), 0451Z (NOT_PRESENT; frame pool; K1 union), 0457Z (head accuracy first), 0515Z (rank by benchmark points; OI/LR/direction rows; VSTI spec; audit fix), 0528Z (frame-pool join first), 0536Z (direction = rows_r1 half-turn twins <=8,000, reviewed by 11:00Z for build 22; VSTI 6,827 rebuilt + REMOVE after review, 4,420 lost-raster rows: drop unless a type <1,000; regen not ordered, record gap), 0546Z GO (head-accuracy: Codex review of record, 3 kits built + Cursor cross-review + CPU dry run; GPU pricing authorised on trinity-1-18 under conditions: record review no BLOCKING, kit reviewed + dry run, 2 nvidia-smi idle readings 1 min apart, <=2 cards, <=16 GPU-h total, vnice + tmux, INBOX_TO_NONTRAINING_ORCHESTRATOR note first, main preempts).
R = trinity-1-18:/scratch/jjyeung/orch_n30. Scripts/prompts: trinity-3-30 /scratch/jjyeung/orch_n30/swarm_build/work/{sh,prompts}; build launch scripts with python + base64 prompts (see sh/w5.sh, w6.sh). Codex queue: tmux sb_codexq runs R/sb_queue/codexq2.sh: append "label" or "label:ws" to R/sb_queue/queue.txt, prompt at R/<ws>/prompts/<label>.md (task + COMMON.md [+ ROWCOMMON.md]); launches while <6 swarm_build Codex and >100 GB avail. Cursor: tmux session per review from R/<ws> with AGENTS.md (copy R/sb_cursor_probe/AGENTS.md) + PROMPT.md; cursor.log only fills at the end (check workspace files for liveness). ssh only via B/tools/tssh.sh trinity-1-18 'bash -s' < script.

## Running at 07:15Z (queue R/sb_queue/codexq3.sh: <3 Codex by unique label, nice 10, 8 threads; model-capacity deaths -> requeue "<label>r:<ws>" with resume note in R/<ws>/prompts/<label>r.md; GPUs on 1-18 taken: GPU QUESTION when kit reviewed; ORDER 0636Z: poll every 10 min only; waiting >20 min only on others -> STATUS + RESULT + end without successor; ORDER 0654Z: one more spec revision + one third review, then open findings go to orchestrator as a list; K1-train-only parts run now)
| item | builder | tmux | next |
|---|---|---|---|
| direction twins sb_rowD7 DONE (8,000 away twins, leak 50.0%, tar 94fdbbcb; native Rooms leaves 7,771 pairs unresolved, tiered map pinned) | - | - | Cursor review sb_drev7 running -> tree_rebuild11 build 22 by 11:00Z |
| sb_kbox4r (ws sb_kbox4): serving-geometry reference, K1-train pricing, SCALE_PROVENANCE.md (+E3), GUARD_VS_READER.md (ruling 0719Z items 3-4) | Codex | sb_kbox4r | post tables; then ktow2 dry run, selrefit, kobj gathering |
| sb_selrefit (ruling 0719Z item 2) | Codex queued | - | READ_REQUEST -> QUESTION if refit wins |
| sb_rkfix DONE (38 tests; GPU ~0.09+0.09 h) | - | - | Cursor re-review sb_rkrev2 running -> GPU QUESTION |
| sb_kobj3: tracking cannot run on CPU (SAM 3 predictor needs CUDA, iopath missing); gathering waits on kbox4 exports | - | - | tracking -> GPU QUESTION (1.3 GPU-h, stop 1.75) |
| sb_f64revr, sb_rlfix2r | Codex | same | act |
| sb_headacc2 (Fable pid 3528233) | inbox: harev2 REJECT, ORDER 0654Z, RULING 0719Z | - | final revision -> third review sb_harev3 -> open list to orchestrator |
| VSTI rows sb_rowB4: NOT bound (RULING 0719Z item 1); candidate in READY_QUEUE | - | - | - |
| sb_countdesign Fable pid 3439690 (to ~08:09Z) | - | - | - |

## Done this session
- sb_fpjoin: 0/0/0 admitted on (a)/(b)/(c); R1 routing/VQA receipt-supported only (FPJOIN_REPORT.md, tar 2eb541e1). On sb_fprev ACCEPT: close BLOCKER 0526Z, add section to distill_design/STORE_V7_ROOM_AUDIT_20261119.md, init_m544 disclosure.
- Camera gate text B/events/swarm_build/GATE_CAMERA_CALL_RATE_V1.md (6f0da488): per type >=143/150 held-out calls, <=2 misses per wording. Registrable after sb_arev2.
- sb_rowA2 camera rows 6,000 (tar 6e0fb408), held-out 900 + scorer patch; sb_rowB3 VSTI 8,186 rows (tar 8ef3308f; v3 family 836 <1,000 so drop default needs a proposal); sb_rowLR 72 rows (576 short; tar 7d26bc3d); sb_auditfix (tar 1d6badbe).
- Verdicts: sb_harev REJECT (13 findings); sb_brev3 REJECT (2 blockers); sb_afrev v7 row-for-row + 2 gaps; sb_recrev ACCEPT WITH FINDINGS (fetch list to events/aws_fetch 0601Z). sb_rowD5 gate: easy 3,664 + hard 2,182 exact, medium 2,665 ambiguous. sb_rowOI 1,008 rows (504 singleton totals + 504 controls; tar R/sb_rowOI/out). sb_regenscope PARTIAL. Verdict texts: work/verdicts1.txt.
- sb_fprev ACCEPT WITH FINDINGS -> BLOCKER 0526Z closed; record section + INDEX written. sb_arev2 ACCEPT WITH FINDINGS -> rows to tree_rebuild (0614Z), held-out+patch to cont_ops (0614Z), gate text ready. sb_rlrev GO AFTER FIXES. sb_auditfix2 done (16 tests). sb_kbox stopped (no torch). aws_fetch: ancestry list 0601Z, R1 row-level list 0614Z. R0DEV_LOOKS.md created. Verdicts: work/verdicts1.txt, verdicts2.txt.
- 06:26Z: sb_rowD6 8,000 twins PASS (gate 5,846/5,846; medium refused: 2,665 pairs, 29,124 rows); sb_rowB4 8,050 rows, 0 false citations, 0 scene-gate refusals; sb_posefam: N's BENCH filter drops all 23 (admitted-order hash MISSING); sb_roomkit S0/S1/S1b + 22 tests pass. Camera gate registered (events/r1_ops/REGISTERED_GATE_CAMERA_CALL_RATE_V1.md); ANSWER 0620Z copied to cont_ops. Record CAMERA_WORDING_ROWS_GATE_20261119.md + INDEX.
- 06:38Z: sb_kbox2 blocked (geometry mismatch); sb_rlfix done (34 tests, 110 formats match score_item; claimed-arm serving table binding MISSING).
- 06:50Z: sb_brev4 ACCEPT (REMOVE_FINAL c9b593ec), sb_pfrev ACCEPT (RECORD_TEXT e1429ccd): both handed to tree_rebuild (0650Z). sb_drev6 REJECT (template leak) -> D7. sb_harev2 REJECT (7 blocking) -> sb_headacc2 inbox. sb_f64 Cursor done.
- 07:05Z: sb_kbox3 root cause (table S4/G1 vs serving own-depth scale; 2 captures guard); sb_ktow2 dry run blocked only on A0 rows; sb_kobj2 dry run PASS; sb_rkrev GO AFTER FIXES; sb_rlrev2 GO AFTER FIXES (decode via A4 reader). swarm_an4 K1 paths answered (its inbox). Verdicts: work/verdicts3-5.txt.
- RESULTs 0548Z, 0602Z, 0615Z, 0655Z, 0713Z posted. Spend 47 Codex jobs / 37,148 s wall at 06:52Z. u2.json exists at R/sb_k1list/out (build 21 binds it).
## Done earlier (predecessor; events 0445Z-0540Z)
Evidence survey + review; v7 audit 0/0/0/0 + K1 union; reader v3 handed to cont_ops18; own-arm kit (awaits GO); counting candidates (rowT, rowF, rowC2, rowC3: need grammar amendment); RL kit sb_rlkit; room design; held-out camera items.
## Waiting
NOT_PRESENT delta (tree_rebuild11 build 22); aws_fetch ancestry files (a60f3a9f, step-200 membership config).
## Spend
CODEX_SPEND.log on 1-18: 27 lines at 05:41Z, about 16,000 s wall (no dollar field). Cursor ~16 sessions. Devin Fable 3.
