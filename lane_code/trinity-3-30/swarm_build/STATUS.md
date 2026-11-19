# swarm_build STATUS (successor resumes from this file alone)
Updated: 2026-11-19T04:15Z by swarm_build (Devin Opus high, trinity-3-30; started 04:02Z; rotate by 09:30Z or 60% context). Brief: B/briefs/swarm_build.md.
Builds run on trinity-1-18 under R=/scratch/jjyeung/orch_n30/sb_<task>; my scripts and prompts: trinity-3-30 $L/work/{sh,prompts}. ssh only via B/tools/tssh.sh (one call/min, batched). Codex receipts: trinity-1-18 R/codex_local/agent/scratch/codex_runs/<stamp>_<label>; spend log there CODEX_SPEND.log (no lines yet).

## Running
| item | builder | tmux @1-18 | workspace | started | deliverable |
|---|---|---|---|---|---|
| 1 component evidence (9 records) | Codex astra high | sb_evidence | R/sb_evidence | 04:05Z | out/EVIDENCE_REPORT.md, out/records/, out/gaps/, out/sb_evidence_records.tar |
| 2 alias map + room audit v7 | Codex astra high | sb_alias | R/sb_alias | 04:05Z | out/ALIAS_AUDIT_REPORT.md, ROOM_AUDIT.json, sb_alias.tar |
| 4 call-rate/usage reader | Codex astra high | sb_callrate | R/sb_callrate (inputs in/ = cont_ops out3 A/A4/B/B4/B5/bases + out3s + dist_diag q1, 298 MB) | 04:07Z | out/CALLRATE_REPORT.md, sb_callrate.tar |
| 6 64-frame N variant | Cursor opus-5-5-xhigh (probe READY 04:08Z) | sb_f64 | R/sb_f64 (log cursor.log; check every 10 min) | 04:10Z | out/F64_REPORT.md, sb_f64_kit.tar |
| 3 room head design | Devin Fable xhigh, trinity-3-30 pid 3313949 (10800 s) | - | trinity-3-30 /scratch/jjyeung/orch_n30/sb_roomdesign | 04:06Z | distill_design/ROOM_HEAD_DESIGN_20261119.md + INDEX; B/events/sb_roomdesign/KIT_SPEC_room_pricing.md only if a head can beat 63+5 on R0-dev (note in its inbox 04:12Z per ORCH NOTE 0404Z) |

## Waiting
- Item 5 own-heads read: QUESTION 0408Z in events/cont_ops (own-arm setting). Default at 06:00Z: build from out3/A, unlaunched until confirmed.
- Item 7 RL kit after items 1-5. Item 8 after swarm_an's record (target 07:30Z).
- Rank (ORCH NOTE 0404Z): 1, 2, 4, 5, 3 (design pass decides if anything gets built), 6, 7, 8.
- Owed after builds: independent review per kit (other family: Codex reviews Cursor, Cursor/Opus reviews Codex), CPU first-batch run, mirror to B/events/swarm_build/ops_mirror (<50 MB) and IB mirror to a second node; records posted to events/tree_rebuild for binding; BLOCKER at once on any R0/withheld-80/BENCH v2 hit.

## Events sent
tree_rebuild 0403Z RESULT takeover; cont_ops 0408Z QUESTION own arm; sb_roomdesign 0412Z note.
