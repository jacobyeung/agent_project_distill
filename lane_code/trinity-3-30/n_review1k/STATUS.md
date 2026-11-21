# n_review1k STATUS (successor resumes from this file alone) — 19:43Z 2026-11-21
Lane n_review1k: headless Claude Code Opus high, trinity-3-30, started 2026-11-21 19:02Z, 10 h timeout (rotate by ~04:00Z 11-22). Brief B/briefs/n_review1k_c.md. B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30.
Predecessor state: STATUS_n_review1j.md here (copy of n_review1j STATUS 19:01Z; full history there). n_review1j inbox copied to inbox_from_1j/.
Lanes: tree_rebuild28 (inbox /scratch/jjyeung/orch_n30/tree_rebuild28/inbox; events B/events/tree_rebuild), n_ops11 (inbox /scratch/jjyeung/orch_n30/n_ops11/inbox). Carriers Claude only.

## Job
- 174198 (kit X/n 929ab213, jn7.sh 98edfd9e) REFUSED 18:51:51Z entry.py:288 R1_ROUTING_SELECTION_DIFFERS; HELD orchard-community-3 until 21:53:13Z. Cause (n_review1j 1854Z): frame fix run root /tmp/jjyeung/q_22c714e1 embedded in regenerated selection; rows.sqlite b2f3db7c != reviewed 5e35c3ce.
- ORDER 1857Z: tree_rebuild28 builds candidate + walks mode q from start on held node. RELEASE not before walk passes frame audit or 21:40Z, and only with ORCH answer.

## Tools
- Gate kit by path /scratch/jjyeung/orch_n30/n_review1j/work/gate/ — hashes checked 19:03Z: gate.py 1fa1048a, run_gate.sh a1c58621, make_review.py b845a1e6, test_gate.py 33015371, USAGE.md 1882a66e.
- work/o_confirm.sh + work/expect_n33.txt (Orchard byte check template; update hashes for the new kit), work/s21.sh (member check template, 1-18), work/wait2.sh <sec> (event/inbox waiter).

## Review rule (ORDER 1857Z item 4)
(a) members and bytes vs reviewed; (b) proof step list in path order, touched/untouched with evidence (from-start run or step run); (c) every regenerated+compared identity equal to reviewed (selection digest == request regenerated_sha256, rows.sqlite 5e35c3ce, materialization, config 76de3706, population/indices pins, census shas) or intentionally new with ORCH ruling; (d) no GO on evidence starting mid-proof. Four earlier fixes intact: F1, admitted census + 3 refusing controls, frame audit on staged copies, room census + protection table + K1 exposure pose 2663 / routing 841.

## Done
- 19:03Z started; gate hashes checked; RESULT started posted.
- 19:07Z tree_rebuild28 RESULT cause = fix11 a.py root $Q_NS/p -> $Q_NJ/p (agrees with 1j). 19:21Z QUESTION (to ORCH): candidate fix16 (tree_rebuild28/work/fix16: cand/b/pf.py audit_roots, cand/b/a.py, k/j.json five steps back to Q_NS). Full from-start walk started 19:19:22Z; selection check expected ~20:02Z.
- ~19:33Z my RESULT on 1921Z: acceptable in principle; Q_NJ spelling enters p/request.json + frames.json -> prepared/config_identity, not compared with a reviewed value that I found; walk must show (i) :288 digest 522a3be3, db 5e35c3ce, mat 6faab9cc, source 74640a29; (ii) every step after frame audit passes, census + K1 unchanged. Tree of 929ab213 extracted at work/k929/t (from mirror fix12 tar).

- 19:28Z ORCH ANSWER (inbox): GO for release needs (i) in full (:288 digest 522a3be3, db 5e35c3ce, mat 6faab9cc, source 74640a29) + walk early steps per ANSWER 1924Z item 3 (host selection, direction_twins, training_components, witness, model build in admit, prepare :540/:621, frame audit started and keeping frames) + my reading of every later comparison meeting frames.json/request.json (files+lines: h.py, rv.py, resume path, gate). Verdict must say in one line: (ii) steps after frame audit unshown, accepted by ORCH. At the gate report frames.json spelling.
- Reading done (19:40Z): tree s1_admission.py:173-181 (request.json compared only on resume, same p dir), :105-118 verify_frames (resolve_read(logical) vs actual; roots unused), :250-265 frames phase; production_proof.py:136-180 (admit->bind_prepared->handover->production_audit->forward->finish_host; no frames/roots compare); entry.py:27-40 temporary_paths, :277-288, :291-305 finish_host (config_identity not pinned); r1_population/r1_persisted/r1_loader/carrier_c1_run: no frames/frame_roots reference; kit b/h.py (identity(cfg) vs host config_identity, both same run), b/rv.py:270-304 (review config_identity vs value, census pin), b/cs.py, b/sv.py (no path/root compare); gate.py pins N_DB, TREE, counts; identity checks internal only.
- Gate copy n_review1k/work/gate: run_gate.sh 52c15bf7 (+ step 4 spell.py 227b866b, info only), gate.py 1fa1048a unchanged, USAGE c3ea4fec. spell.py tested on synthetic files.
- work/w1.sh: my own read of the walk's selection (tree p3_provenance.digest vs X/u/a49f117f regenerated_sha256, rows.sqlite sha, materialization, source, pool refs, host/RESULT). Run once selection exists (~20:02Z).

## Owed (in order)
1. Review ONCE tree_rebuild28's candidate for 174198 under the rule. Selection-byte change = not GO, ORCH ruling.
2. Orchard bytes confirm before each new job release.
3. Gate at WAITING_REVIEW (run_gate.sh <job> /scratch/jjyeung/orch_n30/n_review1k/gate_<job> [--local DIR]); PASS -> make_review.py -> n_ops11/inbox (installed only after ORCH answers rehearsal, ORDER 1757Z); FAIL -> BLOCKER.
