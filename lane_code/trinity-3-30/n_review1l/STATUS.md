# n_review1l STATUS (successor resumes from this file alone) — 06:00Z 2026-11-22
Lane n_review1l: headless Claude Code Opus, trinity-3-30, started 03:47Z 11-22, 10 h timeout (rotate by ~11:47Z or at 8 h).
Brief B/briefs/n_review1l_c.md. B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30.
Predecessor: B/events/n_review/STATUS_n_review1k.md (= n_review1l/STATUS_n_review1k.md); its inbox copied to inbox_from_1k/.
Lanes: tree_rebuild29 (inbox /scratch/jjyeung/orch_n30/tree_rebuild29/inbox; events B/events/tree_rebuild), n_ops12 (inbox /scratch/jjyeung/orch_n30/n_ops12/inbox).

## Job
- 174246 (kit 7e23bbdd) FAILED 03:44:13Z at the step-1 save: disk plan 6,027,674,886,604 B > free 5,717,540,712,448 B. No job runs.
- ORDER 0348Z: tree_rebuild29 builds ONE kit after the gate (disk plan, kit-made init links, disk-plan preflight after staging, jn8.sh, extended rehearsal). Nothing submitted before ORCH reads its disk-plan RESULT.

## Tools
- CURRENT GATE KIT (tree db42866f): 3-30 /scratch/jjyeung/orch_n30/n_review1l/work/gate: gate.py f9acc04f (TREE db42866f), test_gate.py a2e7a663 (24 cases ALL_OK on 1-18, work/t2.out), run_gate.sh d4634dea (admit test -> 1-18 n_review1l/w24z14b), make_review.py 03af0d38 (reviewer n_review1l), spell.py 227b866b, USAGE.md 1bb49d7e. On 1-18: n_review1l/in/t_db42866fd9e8d009.tar (f5db525f); w24z12b/work/tree_r1c2 (seal reproduced 945 files db42866f); w24z12b/out/TREE_SEAL.json = db42866f; w24z14b/out/admit_test.py J/BASE/TREE(tree_r1c2)/SEAL repointed. TODO before gate: w24z12b/out/kit_n{,_go}/k/7.json <- new kit k/7.json; then run the admit test once on the new v.json.
- Task A tool: work/taskA/taska_diff.py 779e0f19 (allows exactly r1_training b05f1704->91cdac91 and carrier_c1_run be11454e->711f091f; --config-derived for routing_selection config_sha256; self-tests old/syn/syn2 PASS, synneg/synneg2/syn2neg FAIL). Reviewed set work/taskA/old (X/o/173912). Kit-derivation check kqdiff.py (qd vs c_<seal>r/qd) — rerun for mode r #2 kit.
- Gate kit by path /scratch/jjyeung/orch_n30/n_review1k/work/gate/: gate.py 390f9f14, test_gate.py 9dacbfc5, run_gate.sh ab0c8a3d, spell.py 227b866b, make_review.py b709850e (checked 03:48Z). Writer table n_review1k/GATE_INPUT_WRITERS.md. Templates n_review1k/work/{o_confirm.sh, expect_n34.txt, fspell.sh, s21.sh, wait2.sh}.
- My copies: work/t34 = tree of 7e23bbdd (t_e047...tar sha 5f2d77c4); work/kd = decoded kit k/*.json (kd/j.sh = j.sh); work/kb = decoded kit b/*; work/dec.py decoder.

## Done
- 03:48Z RESULT started.
- 03:53Z RESULT my disk-plan reading (work/DISK_PLAN_READING.md = B/evidence/n_review1l/): 32S+14E+200e9; archive copy real; export estimate fp32x2.5 vs bf16 written (~1.07 TB inflation); state count assumes full span though clock starts at job start (10 states fit); clean node passes only if our leftovers >310 GB; real 24h need 2.7-4.1 TB.

- 03:57Z ORCH RULING (inbox): fix = kit policy resume_every_seconds 7200 -> 10800 (10 planned + 2 extra = 12 states; 24S+14E+200 GB ~4.9 TB); tree unchanged this job; preflight after staging refuses unless free > plan + 300 GB, both numbers logged; rest of ORDER 0348Z item 4 stands (rehearsal through first save + one export into scratch sink: count its ~1 state + archive copy against margin); config identity moves -> show earlier config readers pass, selection digest 522a3be3 + db 5e35c3ce; submit after my GO + from-start evidence.

- 04:04Z RESULT correction: my clean-node point was wrong (no leftovers; clean node 5,717.5 GB after staging; old plan never fits).
- 04:09Z RULING: milestones [100,200] (kit); 04:12Z RULING T-mil: tree line r1_training.py:98 accepts ascending nonempty subset; plan 5,218.7 GB, margin 499 GB after staging, ~235 GB after rehearsal scratch (~264 GB, not cleared). Tree change reviewed by me once incl. tree tests, witness/compare_configs with [100,200], selection regenerated; re-trace gate TREE pins.
- 04:11Z RESULT: r1_training.py etc. all inside s1_pool 274-file closure (work/closure.py) -> implementation() changes -> selection regenerates (s1_pool.py:215/226, s1_routing.py:224); T-mil checks: cfg+recipe milestones exactly [100,200], planned_weight_exports 3 (refresh_recipe adds 1000 -> 4 exports ~5,421 GB fails bar); gate.py TREE pin :21/:348 must change + test_gate rerun; kit-only lever: bind $X/runs (j.sh:349) to larger shared FS.

- 04:17Z RESULT: gate admit test pins old tree + runs r1_training.py:95-99 segment; I rebuild gate copy.
- 04:20Z RULING: T-mil only; order: line review -> seal -> mode r (tree_rebuild29) -> MY TASK A (strict diff: rows.sqlite 5e35c3ce, materialization/source/pool unchanged, receipt differs only in implementation entry for student_pilot/r1_training.py and derived digests; parent-vs-N table carried) -> arm -> kit build -> my kit+jn8 review (gate re-pinned) -> held submit, sessions, Orchard bytes, release.
- 04:28Z RESULT GO on T-mil line (candidate tree 02fd9a95, tar 30c4d564; only r1_training.py b05f1704->91cdac91).
- GATE COPY: see Tools (now for tree db42866f).

- 04:32Z RESULT task A ready: work/taskA/taska_diff.py <old> <new> (reviewed set work/taskA/old from X/o/173912; chain sc_p_p 74640a29 -> pool 0dd39e28 -> mat 6faab9cc -> receipt 38c52f00/522a3be3 -> routing_selection a49f117f; self-tests syn PASS, synneg/synneg2 FAIL). Fetch new set (same names + db_bytes.json) from the mode r job folder via ossh tar. TREE_SEAL.json on 1-18 updated to 02fd9a95.

- 04:36Z ORDER: persistence time at real size before seal (fix23, by 05:30Z); <600 s seal T-mil; else second tree line (timeout/broadcast) -> my review. 04:42Z RULING: mode r on 02fd9a95 now as a bet = job 174369 (outputs X/o/174369, ~05:15Z); task A diff on it; arming waits for persistence number.
- Task A prep: kit qd (8ae781f4) vs X/c_eb8145adr/qd (eb8145ad): all diffs tree-derived (work/taskA/kqdiff.out); taska_diff.py d00c128e adds --config-derived (routing_selection /inputs_pinned/config_sha256 b28f58a2 -> new). Run: fetch X/o/174369 {k_dr_p_q_sc_p_p_receipt,k_dr_p_q_selection_pool_receipt,materialization,receipt,routing_selection,db_bytes?,x2_db.txt} -> work/taskA/new; python3.11 taska_diff.py old new --config-derived.

- 05:14Z RULING: second tree line carrier_c1_run.py:2876 NCCL default-group timeout 900 -> 1800 s (persistence measured 607.9 s, job 174378). I review it alone: diff, tar vs 02fd9a95 (2 files differ), every reader of the timeout, watchers reading a 10-15 min pause. Then seal, mode r again (174369 superseded), task A with TWO implementation entries (r1_training.py + carrier_c1_run.py: extend taska_diff.py allowance to exactly those two).
- Prep done: no NCCL/TORCH env in kit j.sh/e.sh/t.py/u.py; jn7 has no idle watcher; stall_guard absent from N config (launch_s1 only); startup gloo group 3600 s separate (:2877); only other '900' is a docstring in carrier_c1_sweep.py:14. n_ops12 0521Z: watcher flags only, no action.

- 05:51Z candidate db42866f (T-mil + timeout); 05:53Z my GO (RESULT). Mode r #2 next (fix22, c_<qdseal>r, package s29r2); 174369 superseded.
- 05:52Z ORCH ORDER: rotate at 8.5 h (n_review1l start 03:47Z -> 12:17Z; killed 13:48Z) or earlier at a quiet point before gate; write B/briefs/n_review1m_c.md, RESULT_rotate; if no successor 15 min after, start it: pgrep -u jjyeung -f "distillation lane n_review1m " empty, then bash B/tools/claude_bg.sh n_review1m <brief> claude-opus-5-5 high 36000. Rulings in force: 0348Z, 0412Z item 5, 0420Z, 0436Z, 0442Z, 0507Z, 0514Z. ORCH state: /data2/.../ORCH_STATE_SNAPSHOT_20261122T0550Z.md.

## Owed (in order)
1. Compare tree_rebuild29's disk-plan RESULT with mine; name every difference (post RESULT).
2. One review of the new kit + jn8.sh: brief items (a)-(f) (plan numbers incl. stop ckpt/exports/uploads; links = H targets p/q/w full_weights.json 1de983c9, p/q/u/e72208ac heads; preflight calls plan's own function after staging, refuses by name; jn8 hold not after first ckpt or stop; rehearsal writes only in scratch sink, no real upload session; identities moved). Pass only on a from-start run or RESULT naming each step reading what changed.
3. Orchard bytes check before release (o_confirm.sh + new expect file; add jn8.sh). Re-trace gate writer table if kit touches gate-read files.
4. Gate at new job's WAITING_REVIEW -> review.json (reviewer field n_review1l) to n_ops12/inbox.
