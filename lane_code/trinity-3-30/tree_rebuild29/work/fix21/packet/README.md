# n35 review packet: kit w35, seal ea058fed0495be92fd22c71546fd1bbab449970c566319fc857ddd2a6a551591 (fix21, 2026-11-22 06:50Z)

The kit is 7e23bbdd on tree db42866f (T-mil plus the 1800 s group timeout), with milestones [100,200], the arming on the task-A-passed selection c672ad47, and five kit changes: init links, a disk plan check, metrics publishing, the wrapper jn8.sh, and the extended rehearsal (a separate artifact). It is sealed and mirrored, and it is not installed.

- Kit: trinity-1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w/w35/final/n_go. Tar W/w35/s35_n_go.tar is 5,980,160 B, sha256 3c3b91ebda00a4278f4e50ffe0774d79233c2413482e0d202dd95e7811f2b404.
- Mirror: trinity-3-30:/scratch/jjyeung/n30_mirror/tree_rebuild29/w35/s35_n_go.tar has the same sha256 on both ends, and `sha256sum -c` of the extracted kit is all OK. The extracted copy is fix21/kfinal/n_go.
- Install uploads (from the same build): final/u_da19bb3a... is the code record and final/u_c672ad47... is the selection. Both are in the mirror folder w35/final/.

## Criteria and evidence
1. **Built with the kit's tools, from 7e23bbdd (seal checked).** I used in/b35.py (script_b35.py).
   - The tree is in/tree35.py 'timeout' (script_tree35.py) rebuilt from the base kit's tar with the tree's own inventory/archive/check_archive. It reproduces the sealed db42866f tar f5db525f byte for byte on trinity-1-18 (out_tree35.log, out_final_suite.out).
   - Every rewritten capsule uses the writer that reproduces its 7e23bbdd bytes.
   - launch_r1.build.verify(kit) on the new tree equals the seal ea058fed (out_BUILD35.json).
2. **Changed members** (DIFF_vs_7e23bbdd.txt, with decoded diffs):
   - Changed: b/pc.py, k/7.json, k/a.json, k/c.json, k/c0.json, k/h.json, k/j.json, k/n.json, k/p.json, k/r.json, BUILD.json, SHA256SUMS.txt.
   - Added: b/il.py, b/dp.py, k/t_db42866fd9e8d009.tar.
   - Removed: k/t_e047002134f979bd.tar.
   - Unchanged: k/y.json (112 sessions), k/s.json, k/l.json, k/g.json, k/8.json, every other b/ file.
3. **Tree db42866f** (T_mil_to.diff b84c5da4, TREE_SEAL.json, T_mil_tests.log, T_mil_to_tests.log; n_review1l GO 0428Z and 0553Z):
   - r1_training.py:98 accepts a nonempty ascending subset of P's six milestones.
   - carrier_c1_run.py:2874/2876 move the default group from 900 s to 1800 s.
   - k/a.json source, k/7.json and k/c0.json (code record da19bb3a) and k/p.json (code_sha256, the uploads entry and pin_paths) follow the tree.
4. **Configuration** (k/c.json and k/n.json): milestones and recipe.milestones [100,200], checkpoint_disk_guard.planned_weight_exports 3, plus the code pin. Nothing else changes; r2_config.refresh_recipe is not used.
   - Every reader of the milestones, run with the tree's functions on CPU (out_mreaders.json): validate :98 PASS; recipe_for [100,200]; plan == guard (entry.check_host_runtime disk_plan True); exports only at 100, 200 and the stop.
   - compare_configs against P's prepare config PASS (out_cc_new.json; head_init, effective_camera and the preparation key are stubbed alike on both sides). Its interval and wall controls REFUSE.
   - The upload planner reads only k/y.json, which is unchanged: 112 sessions, of which m400-m1000 (16) are unused.
5. **Arming** (task A strict diff PASS 0642Z): k/h.json routing_selection, k/r.json routing_selection and staged_pins[0], and k/p.json (uploads entry 10,997 B and pin_paths) go from a49f117f to c672ad47b28d05d81e524baddb6d164f0f41c0b23a8cf0a1f49bfd045e93ec46.
   - Checked by b35 against the bytes of X/o/174415: regenerated_sha256 e9b6b268, receipt e3598dcd, generated rows.sqlite 5e35c3ce, base DB 4e8e6c04 (837,255,168 B, in the uploads), routing_base ca0616db = r.json, rows 43,101, row_id bdd91b75, row_bytes 802414c8, P regeneration 876be23d.
   - pin_paths is consistent with the uploads and a49f117f is gone (arm_check line in out_final_suite.out).
   - The selection build reads cfg recipe only for max_routing_suffix_tokens, not the milestones, and the host check compares only regenerated_sha256 (entry.py:277-288).
6. **Init links by the kit** (b/il.py; k/j.json before t.py, after rv.py). They are derived from v.json's init_artifact pins and persisted_files, hashed, never replace an existing entry, refuse by name and log both readlinks and hashes. out_til.json: OK, idempotent, and nine named refusals.
7. **Disk plan check** (b/dp.py; k/j.json right after staging, and again at training start).
   - Uses the tree's own plan() and Budget, check()'s byte formulas, and the measured pair that reproduces 174246's 6,027,674,886,604 B (self-checked).
   - After staging it refuses unless free > plan + 300 GB; at training start the bar is 0. Both numbers go into the job log.
   - out_final_suite.out: 5,717.5 GB free PASS, plan 5,218,717,972,092, margin 498.8 GB. The bar edge refuses at +299.98 GB and passes at +300.03 GB. 7e23bbdd's config refuses (-310.1 GB, 174246 reproduced). A guard mismatch refuses R1_DISK_PLAN_DIFFERS.
8. **Metrics** (b/pc.py): metrics_<attempt>.jsonl.gz goes to X/o/<job>/live every 300 s, outside copy.json's 50 MB budget, with a 45 MB cap of its own (keeping the newest whole lines). Before this change the metrics left the node only until about 9 MB. out_tmet.json: a 76.8 MB worst-case file gives a 28.7 MB gz with an exact round trip; the cap path passes.
9. **Wrapper jn8.sh** (sha256 2de401bd4370b13ebaf50663f7f1bbd9f924c1fd5f90b1762dbd76662388c684; JN8_vs_jn7.diff).
   - After the training start it also holds while p/q/r has no completed checkpoint, export or run report. TERM/USR1 and success stay unheld. HOLD.txt names the phase train_pre_save.
   - out_jn8.log (exact bytes in bwrap with stubs): pre-save HOLD, stop no hold, saved no hold, exported no hold, pre-training HOLD, success no hold. jn7 control (out_jn7.log): pre-save no hold.
10. **Extended rehearsal** (not in the kit; fix21/rh_ext, rehearsal_REPORT.md, rehearsal_rh.diff).
    - After its two steps it runs the trainer's own checkpoint, persistence milestone, export and milestone on four ranks under the default group, then the kit planner against a local recorder with no network.
    - It writes about 270 GB to the node's /tmp and does not clear it, leaving about 229 GB at the first real save.
    - It prints PERSIST_SECONDS with DANGER above 800 s or 1600 s. All CPU tests pass, including the dry run as fix15 test 4.
11. **/project during training** (fix21 REPORT, ORDER 0556Z): the training sandbox sees the real /project read-only, and every writer during training is a separate process that catches the error and retries. A full /project is not fatal. A job keeps at most about 0.2 GiB resident and writes under 22 GB in all. Checkpoints and exports go to GCS through the sessions.
12. **Earlier fixes intact** on the final kit (out_*): tchk33 old REFUSE vqa(division) / new PASS; T1-T6 (T3 PASS, T4 control REFUSE); frames A and B all as expected; ut2 ALL PASS (with the new pc.py); st34 static all_ok; py_compile; bash -n; no __pycache__; tmil and the gloo timeout harness (out_tto_gloo_timeout.log).

## ORDER 1857Z item 4: earlier steps that read what each change touches
| change | touches | steps that read it | shown by |
|---|---|---|---|
| tree db42866f (:98 and the group timeout) | tree seal, tar, k/a.json, k/7.json, k/c0.json, k/p.json code pins, s1_pool.implementation() | every step: a.py (extract, verify), the proof (authenticate, routing selection, admit, witness, handover), d.py, h.py, rv.py, u.py/t.py; the timeout only in train() | the tree's own tests (identical before and after), the gloo harness, mode r #2 on db42866f (174415, from the start of the proof through the regenerated selection), task A strict diff PASS |
| milestones [100,200], guard exports 3 | configuration identity (k/c.json, k/n.json), plan | admit, check_host_runtime disk_plan, routing selection (does not read them), witness compare_configs, handover, trainer schedule, upload planner (y.json) | readers table (out_mreaders.json); selection digest from mode r #2, rows 5e35c3ce unchanged |
| arming c672ad47 | k/h.json, k/r.json, k/p.json selection pins | the host selection check (entry.check_host_selection), plan_payload staging (p.json uploads and pin_paths) | task A strict diff PASS; b35's arming checks; pin_paths consistency (arm_check) |
| j.sh preflight dp.py | reads k/a.json, k/c.json, the tree tar; writes TMPDIR temp and dp.log | none | dp tests |
| j.sh il.py links (after rv.py) | two symlinks under the job's rp (X/runs in the sandbox) | only t.py ranks 1-3 at load_model (n_review1k 0246Z/0250Z) | til tests; option H in 174246 (four ranks loaded) |
| j.sh dp.py train | reads v.json, p/s; writes dp2.log | none | dp train tests |
| b/pc.py metrics | X/o/<job>/live metrics files | nothing in the kit reads them | tmet; ut2 ALL PASS |
| new b/il.py, b/dp.py | kit seal | every seal check | verify = seal; st34 |
| jn8.sh | wrapper hold | no kit step | jn8 matrix with jn7 control |

## Open points (not shown on CPU)
- The real S, E, persistence and tar times, and NCCL under 1800 s on the GPU node: the rehearsal reports them at the gate.
- dp.py's bytes use the measured 174246 pair. The trainer's own guard at the first save remains the binding check; dp is the early estimate of it.
- The stop window: the stop save at 22.6-23.0 h leaves 3,600-5,100 s for two persistence passes and 1,625 s of upload.
- Metrics gz size at real scale is not measured; the worst case on random floats is 28.7 MB.
- Mode r #2's disclosed refresh receipt point (n_review1l RESULT 0642Z item 6) is the reviewer's to rule.
