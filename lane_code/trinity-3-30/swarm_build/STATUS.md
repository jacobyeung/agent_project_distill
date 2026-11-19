# swarm_build STATUS (successor resumes from this file alone)
Updated: 2026-11-19T06:28Z by swarm_build2 (Devin Opus high, trinity-3-30, started 05:40Z; rotate by 11:10Z or 60% context to swarm_build3).
Brief: B/briefs/swarm_build2.md. Orders in force (B/events/swarm_build/*ORCH*): 0404Z, 0433Z (row builds, up to 6 Codex on 1-18), 0426Z/0459Z (aws_fetch fetches; never ssh code-aws/Mind), 0451Z (NOT_PRESENT; frame pool; K1 union), 0457Z (head accuracy first), 0515Z (rank by benchmark points; OI/LR/direction rows; VSTI spec; audit fix), 0528Z (frame-pool join first), 0536Z (direction = rows_r1 half-turn twins <=8,000, reviewed by 11:00Z for build 22; VSTI 6,827 rebuilt + REMOVE after review, 4,420 lost-raster rows: drop unless a type <1,000; regen not ordered, record gap), 0546Z GO (head-accuracy: Codex review of record, 3 kits built + Cursor cross-review + CPU dry run; GPU pricing authorised on trinity-1-18 under conditions: record review no BLOCKING, kit reviewed + dry run, 2 nvidia-smi idle readings 1 min apart, <=2 cards, <=16 GPU-h total, vnice + tmux, INBOX_TO_NONTRAINING_ORCHESTRATOR note first, main preempts).
R = trinity-1-18:/scratch/jjyeung/orch_n30. Scripts/prompts: trinity-3-30 /scratch/jjyeung/orch_n30/swarm_build/work/{sh,prompts}; build launch scripts with python + base64 prompts (see sh/w5.sh, w6.sh). Codex queue: tmux sb_codexq runs R/sb_queue/codexq2.sh: append "label" or "label:ws" to R/sb_queue/queue.txt, prompt at R/<ws>/prompts/<label>.md (task + COMMON.md [+ ROWCOMMON.md]); launches while <6 swarm_build Codex and >100 GB avail. Cursor: tmux session per review from R/<ws> with AGENTS.md (copy R/sb_cursor_probe/AGENTS.md) + PROMPT.md; cursor.log only fills at the end (check workspace files for liveness). ssh only via B/tools/tssh.sh trinity-1-18 'bash -s' < script.

## Running at 06:28Z (queue cap 4 Codex, nice 10, 8 threads; GPUs on 1-18 taken: post a QUESTION with GPU need when a kit is ready)
| item | builder | tmux | next |
|---|---|---|---|
| Cursor reviews | sb_drev6 (direction twins D6, tar 265b03ac), sb_brev4 (VSTI B4, tar ff3ee17e; also REMOVE_FINAL per ruling 0607Z item 4), sb_pfrev (pose family proof), sb_rkrev (room kit) | same | D6/B4 -> tree_rebuild11 build 22 (by 11:00Z); posefam record text -> tree_rebuild11; roomkit GO -> GPU QUESTION |
| sb_kbox2 (torch env; v2 spec exists: KIT_SPEC_box_ladder_k1_v2.md) | Codex | sb_kbox2 | Cursor review |
| sb_rlfix (tower path kept per ORCH ANSWER 0620Z item 3; score_item parity) | Codex | sb_rlfix | Cursor re-review |
| sb_ktow (tar 7438d6f5), sb_kobj (dry run BLOCKER: no torch, missing direct/scorer exports, 2 ambiguous qids; track BLOCKER file) | done v1 | - | v2 patch pass when sb_headacc2 posts tower/object v2 specs (fix env too) |
| head-accuracy fix lane sb_headacc2 | Devin Fable xhigh trinity-3-30 pid 3528233 | - | box v2 posted; tower/object v2 + REVIEW_RESPONSE -> Codex re-review sb_harev2 |
| 64-frame N sb_f64 | Cursor | sb_f64 | dry run evidence mem_n32_8/mem_f64_8; Codex review when done |
| Fable sb_countdesign pid 3439690 (to ~08:09Z) | - | - | - |

## Done this session
- sb_fpjoin: 0/0/0 admitted on (a)/(b)/(c); R1 routing/VQA receipt-supported only (FPJOIN_REPORT.md, tar 2eb541e1). On sb_fprev ACCEPT: close BLOCKER 0526Z, add section to distill_design/STORE_V7_ROOM_AUDIT_20261119.md, init_m544 disclosure.
- Camera gate text B/events/swarm_build/GATE_CAMERA_CALL_RATE_V1.md (6f0da488): per type >=143/150 held-out calls, <=2 misses per wording. Registrable after sb_arev2.
- sb_rowA2 camera rows 6,000 (tar 6e0fb408), held-out 900 + scorer patch; sb_rowB3 VSTI 8,186 rows (tar 8ef3308f; v3 family 836 <1,000 so drop default needs a proposal); sb_rowLR 72 rows (576 short; tar 7d26bc3d); sb_auditfix (tar 1d6badbe).
- Verdicts: sb_harev REJECT (13 findings); sb_brev3 REJECT (2 blockers); sb_afrev v7 row-for-row + 2 gaps; sb_recrev ACCEPT WITH FINDINGS (fetch list to events/aws_fetch 0601Z). sb_rowD5 gate: easy 3,664 + hard 2,182 exact, medium 2,665 ambiguous. sb_rowOI 1,008 rows (504 singleton totals + 504 controls; tar R/sb_rowOI/out). sb_regenscope PARTIAL. Verdict texts: work/verdicts1.txt.
- sb_fprev ACCEPT WITH FINDINGS -> BLOCKER 0526Z closed; record section + INDEX written. sb_arev2 ACCEPT WITH FINDINGS -> rows to tree_rebuild (0614Z), held-out+patch to cont_ops (0614Z), gate text ready. sb_rlrev GO AFTER FIXES. sb_auditfix2 done (16 tests). sb_kbox stopped (no torch). aws_fetch: ancestry list 0601Z, R1 row-level list 0614Z. R0DEV_LOOKS.md created. Verdicts: work/verdicts1.txt, verdicts2.txt.
- 06:26Z: sb_rowD6 8,000 twins PASS (gate 5,846/5,846; medium refused: 2,665 pairs, 29,124 rows); sb_rowB4 8,050 rows, 0 false citations, 0 scene-gate refusals; sb_posefam: N's BENCH filter drops all 23 (admitted-order hash MISSING); sb_roomkit S0/S1/S1b + 22 tests pass. Camera gate registered (events/r1_ops/REGISTERED_GATE_CAMERA_CALL_RATE_V1.md); ANSWER 0620Z copied to cont_ops. Record CAMERA_WORDING_ROWS_GATE_20261119.md + INDEX.
- RESULTs 0548Z, 0602Z, 0615Z posted. u2.json exists at R/sb_k1list/out (build 21 binds it).
## Done earlier (predecessor; events 0445Z-0540Z)
Evidence survey + review; v7 audit 0/0/0/0 + K1 union; reader v3 handed to cont_ops18; own-arm kit (awaits GO); counting candidates (rowT, rowF, rowC2, rowC3: need grammar amendment); RL kit sb_rlkit; room design; held-out camera items.
## Waiting
NOT_PRESENT delta (tree_rebuild11 build 22); aws_fetch ancestry files (a60f3a9f, step-200 membership config).
## Spend
CODEX_SPEND.log on 1-18: 27 lines at 05:41Z, about 16,000 s wall (no dollar field). Cursor ~16 sessions. Devin Fable 3.
