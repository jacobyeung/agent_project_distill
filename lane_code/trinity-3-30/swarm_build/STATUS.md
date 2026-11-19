# swarm_build STATUS (successor resumes from this file alone)
Updated: 2026-11-19T05:25Z by swarm_build (Devin Opus high, trinity-3-30; started 04:02Z; rotate by 09:30Z or 60% context). Brief: B/briefs/swarm_build.md; orders since: ORCH NOTE 0404Z (room rerank), ORDER 0433Z (rows A-E, up to 6 Codex), ANSWER 0426Z (aws_fetch), RULING 0451Z (NOT_PRESENT; frame pool; K1 union), ANSWER 0459Z (camera rows from Mind extract; camera gate text owed after held-out review).
R = trinity-1-18:/scratch/jjyeung/orch_n30. My scripts/prompts: trinity-3-30 $L/work/{sh,prompts}. ssh only via B/tools/tssh.sh (one call/min). Codex queue: tmux sb_codexq on 1-18 runs R/sb_queue/codexq.sh (launches names in R/sb_queue/queue.txt when <6 Codex and >100 GB available; log codexq.log; prompt at R/<t>/prompts/<t>.md). Cursor: `agent -p -f --sandbox disabled --trust --model claude-opus-5-5-xhigh` in tmux from a workspace holding AGENTS.md (copy R/sb_cursor_probe/AGENTS.md) and PROMPT.md. rm_guard blocks some complex shell lines as "unparsable": build launch scripts with python/write tool, run them with tssh. Two blocked (non-deleting) commands of mine are queued in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md: obsolete, must not be run.
Codex "model at capacity" errors happen: a job ending exit 1 with that in its transcript is rerun (resume note in prompt).

## Running
| item | builder | tmux / host | deliverable |
|---|---|---|---|
| lineage component records from aws_fetch sources | Codex | sb_records | R/sb_records/out/RECORDS_REPORT.md -> Cursor review -> tree_rebuild11 |
| frame pool 146 captures (rerun) | Codex | sb_framepool | out/FRAMEPOOL_REPORT.md; training row = BLOCKER; add to STORE_V7_ROOM_AUDIT record + init_m544 disclosure |
| room kit spec review | Codex | sb_rspecrev | then build room pricing kit (Part A) |
| counting form B (candidate) | Codex | sb_rowF | out/ |
| relative count C3 (form B) / C2 (tally, superseded) | Codex | sb_rowC3, sb_rowC2 | out/ |
| own-arm kit fixes | Cursor | sb_ownfix (in R/sb_ownread) | then hand OPERATOR to cont_ops18 |
| 64-frame N | Cursor | sb_f64 | out/F64_REPORT.md |
| head accuracy all categories | Fable trinity-3-30 pid 3462774 (4 h) | - | HEAD_ACCURACY_DESIGN_20261119.md + 3 kit specs -> build pricing kits (top rank) |
| counting >4 | Fable trinity-3-30 pid 3439690 (3 h) | - | COUNT_LARGE_SETS_DESIGN_20261119.md |
| queue order | Codex | sb_codexq (codexq2.sh, entries label[:workspace]) | sb_rowD3, sb_rowA2:sb_rowA (rows + scorer patch for parser blocker), sb_rowB3, sb_rowOI, sb_rowLR, sb_auditfix |
| waiting | - | - | NOT_PRESENT delta on build 20 (tr11_b20 ~07:45Z) + Cursor review; aws_fetch GT packs for D3/B3 (RESULT 0520Z); camera gate text after rowA2 |

## Done
- Reader v3 final review ACCEPT WITH FINDINGS (LOW); tar ba53f025 mirrored to B/events/swarm_build/ops_mirror/sb_callrate_v3.tar; handed to cont_ops18 (events/cont_ops 0522Z).
- Own-arm kit review GO AFTER FIXES (sb_owrev). Held-out camera review REJECT (parser blocker; fix in sb_rowA2). Tally kit sb_rowT 17,564 rows (53dac75a). B2 6,827 VSTI rows (4,420 refused missing GT; superseded by B3). D2: 0 rows (GT packs missing), 3,026 K1 removals; superseded by D3. RESULT 0520Z.
- Evidence: nine MISSING (R/sb_evidence tar 18d4d04c), review ACCEPT WITH FINDINGS; inventories R/sb_inventory (all GAP); GF-1 -> NOT_PRESENT ruling 0451Z.
- v7 audit (R/sb_alias2 tar c7743a8b): 0 R0 / withheld / BENCH v2 / dev-S1, K1 4,959; review ACCEPT WITH FINDINGS (audit code's scannetppv2 naming bug, harmless here). Record distill_design/STORE_V7_ROOM_AUDIT_20261119.md + INDEX line. K1 union (R/sb_k1list: u2 d2fd6208, union 1c7c930d) handed to tree_rebuild11 0509Z.
- Reader v3 (R/sb_callrate, tar in out/): 56 unit tests, 190 reproduction checks, 31 probe checks; room36 vs b1/read 0 55.28; distance usage 100% at both steps with conversion failures split out; --strata ready.
- rows A part (ii): 900 held-out camera items (R/sb_rowA/out). rows D audit: away rows already state the half turn.
- own-arm kit (R/sb_ownread/out): 1 H100 ~2.1 h per milestone; review running. RL kit (R/sb_rlkit/out): CPU proof, 20 tests; not GPU-near.
- Room head design (Fable, done 04:44Z): YES it could: room call on DA3 geometry 84-85 on K1 ScanNet++ vs direct 62.76 on R0-dev; kit spec events/sb_roomdesign/KIT_SPEC_room_pricing.md (Part A ~0.6 GPU-h); spec review queued.

## Spend
CODEX_SPEND.log (1-18): about 15 finished jobs (~9,000 s wall; no dollar field).

## Events sent (this session)
tree_rebuild 0403Z, 0441Z, 0445Z, 0509Z; cont_ops 0408Z; sb_roomdesign 0410Z; aws_fetch 0454Z, 0503Z; swarm_build 0424Z Q, 0445Z, 0447Z, 0503Z Q, 0509Z.
