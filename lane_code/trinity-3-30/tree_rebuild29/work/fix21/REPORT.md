STATUS 2026-11-22T05:58Z fix21: tree db42866f SEALED and mirrored. The TEST kit on db42866f (seal 5d2e9b5d, not for review) passes the full suite on trinity-1-18. The rehearsal is DONE. ORDER 0556Z is answered. The final kit seal, tar, mirror and packet wait for task A and the arming.

# fix21 kit w35 build report
## Item 1 (held)
- ORCH RULING 0409Z named milestones [100,200]; the sealed tree refuses any list but [100,200,400,600,800,1000] (student_pilot/r1_training.py:98, called from carrier_c1_run.validate:69-72, which runs in s1_admission:168, rehearsal.py:28 and trainer entry 471/672/2849/3091). Coordinator ordered HOLD 04:1xZ.
- Side note: r1_persisted.py:122 requires the init artifact step in recipe_for(cfg)['milestones'], but there cfg is P's persisted config (records['config']), so N's milestones do not reach it.

## T-mil tree change (ORCH RULING 0412Z; prepared, not sealed)
- Closure: the tree's own p3_provenance.source_files([student_pilot/s1_pool.py]) on 9d2bbb8a gives 274 files, the same set as for carrier_c1_run.py (k/7.json sources, 274). It contains student_pilot/r1_training.py, checkpoint_space.py and r1_handover.py, so s1_pool.implementation() (s1_pool.py:93-95) moves under T-mil, T-int and T-est alike. The coordinator was told at about 04:20Z.
- First draft (tb/t2, superseded by RULING 0420Z's line; see the final patch below). Patch (tb/t2/TREE_DIFF.patch), line 98 of student_pilot/r1_training.py:
  `if not recipe['milestones'] or recipe['milestones'] != sorted(set(recipe['milestones'])) or not set(recipe['milestones']) <= {100, 200, 400, 600, 800, 1000}:`
  It refuses an empty list, a value outside P's six, a wrong order and a duplicate.
- in/tree35.py (tree's own inventory/archive/check_archive): the old tar is extracted, the inventory digest equals 9d2bbb8a, and the archive writer reproduces tar 5f2d77c4 byte for byte. After the patch, only r1_training.py changes (b05f1704 -> c8ae2906). New source seal 6fa18a6e1d7d8306d7317688447da24b0aef7e202b45171ad5765440d7d61226; new tar k/t_6fa18a6e1d7d8306.tar sha256 416115a19ca9aeeed5e952662810a051d918333326285441111f7b03a6d91d03 (2,807,757 B), check_archive ok.
- Tests of the function (in/tmil_test.py; the tree's own r1_training.validate on decoded k/c.json; pinned reads before line 98 stubbed): rd/tmil_old.json and rd/tmil_new.json.
  - Full validate, new tree: six PASS; [100,200], [400,1000] and [200] PASS; empty REFUSE R1_MILESTONES_DIFFER; [100,300] REFUSE R1_MILESTONES_DIFFER. [100,1200], [200,100] and [100,100,200] REFUSE earlier in recipe_for ("Final mode needs integer steps and increasing milestones").
  - Line 98 alone (recipe_for passes the list through), new tree: the four subsets PASS; empty, outside 300, outside 1200, wrong order and duplicate all REFUSE R1_MILESTONES_DIFFER.
  - Old tree (control): only the six PASS.
- compare_configs (in/cc_test.py, the tree's own r1_handover.compare_configs(P prepare config b08fe50c, N = job 174246 live v.json 06fd61be), both read from Orchard): three things are stubbed to one value on both sides because they read Orchard-pinned receipts and none reads the recipe: head_init, effective_camera, and the preparation key.
  - Old and new tree: 174246 as run PASS; milestones [100,200] with guard exports 3 PASS.
  - Controls: interval 10800 and wall 64800 REFUSE P_EXPORT_CONFIG_DIFFERENCE:recipe.
  - P's own recipe milestones are [400, 600].
- The full witness (p_opener_witness.produce) needs P's published closure (donor()), so it cannot run off Orchard. Its comparison step is the compare_configs call above.

## T-mil final line (RULING 0420Z), for n_review1l
- work/fix21/T_mil.diff, sha256 19a1cb6a70c94fbdb277512ae1f4577620dedf62855c20c56a68d2c6e840f3ae. It replaces line 98 only with the ORCH's suggested line, verbatim. Line 99 and the line count are unchanged.
- Candidate tree (tb/t3): seal 02fd9a95ebd9719c596b39ac80e5247b92c1d6673d6cc2f4956c70b902718041; tar t_02fd9a95ebd9719c.tar, sha256 30c4d56426af1a3c4f7420430ab4771e38476863394b1cb059c5fc305332fff2, 2,807,778 B. r1_training.py goes from b05f1704 to 91cdac91. Not sealed or posted.
- Tests: work/fix21/T_mil_tests.log.
  - validate, new tree: six, [100,200], [400,1000] and [200] PASS. Empty and [100,300] REFUSE R1_MILESTONES_DIFFER. Descending, duplicate and [100,1200] REFUSE earlier, in recipe_for. With recipe_for passing the list through, all five bad lists REFUSE R1_MILESTONES_DIFFER at line 98.
  - Old tree: only the six pass.
  - The 20 existing test files that import r1_training give identical per-test outcomes on the old and new tree. The 15 failures and 13 collection errors are environmental and the same on both.

## Readers of the milestones (RULING 0420Z item 3), shown on CPU by the tree's own functions (test/mreaders.py, rd/mreaders.json; TEST kit kt/test2)
| reader | where | with [100,200] |
|---|---|---|
| R1 validate | r1_training.py:98, via carrier_c1_run.validate:69-72 (s1_admission:168, rehearsal.py:28, trainer 471/672/2849/3091) | PASS on k/c.json and k/n.json (new tree) |
| recipe | carrier_c1_sweep.recipe_for:82-92 (final mode) | [100,200] for c, n and v; P [400,600] |
| disk plan | checkpoint_space.plan (len(set(milestones)) + export_at_stop), launch_r1/entry.check_host_runtime:160-166 (R1_DISK_PLAN_DIFFERS) | plan == guard {14, 2, 3, 200e9, 1}; check_host_runtime disk_plan True; 5,218,717,972,092 B |
| trainer export schedule | carrier_c1_run.py:2359 (m0), 2438-2440 (budget), 2456 (export) | no m0; exports at 100 and 200; stop export kept (export_at_stop true) |
| handover compare | r1_handover.compare_configs:183-184 (recipe minus mix and milestones; top-level milestones is a HANDOVER_VARIABLE_KEY) | PASS for v and n against P (three Orchard-pinned reads stubbed on both sides) |
| witness | p_opener_witness.produce:43 (reads milestones only through compare_configs) | as compare_configs |
| P's init step | r1_persisted.py:122 (recipe_for of P's persisted config) | reads P's [400,600]; 400 still in it |
| upload planner | kit b/pc.py: objects and sessions from k/y.json only; exports() labels m<step> if in y.json, else mstop/B/C | k/y.json unchanged: 28 objects x 4 = 112 sessions, as now. m100, m200, the stop export, ck00-ck15, ckstop, o and u are used; m400, m600, m800 and m1000 (16 sessions) go unused. n_ops12 mints from k/y.json as before |
| other publishers | kit ep.py, o.py, rd.py, j2/j6/j7 (jn8) | do not read milestones |
| kit proof scripts | z.py export_identity / bound400, pl.py | hash n.json (its identity moves) but compare no milestone value |
| gate | n_review1l's gate (not in the kit) | not seen by fix21; n_review1l re-pins it |
| not on N's path | r2_config.refresh_recipe (only via r2 configure/apply_native, gf1), launch_s1/build.py:100 (build time), carrier_c1_sweep.capped_steps and carrier_c1_run.py:141/2343 (pose_only), ddp_checkpoints run_control checkpoint_milestones (another key), decoupled_* | not run for N |

## Kit w35 TEST build (in/b35.py; not final, not sealed for review)
- Base kit 7e23bbdd: local copy fix15/kit34/n_go, equal to W/w34/n_go by seal. support.cap reproduces every rewritten capsule of the base byte for byte, and the j.json raw capsule writer reproduces 2ca9c9bd.
- Changes:
  - New tree tar replaces k/t_e047002134f979bd.tar.
  - k/a.json source = {tar path, sha256, tree_sha256}.
  - k/7.json code record (files and sources entries for r1_training.py, tree_sha256, commit, archive), checked against the new tree's own inventory.
  - k/c0.json, the job's source_code.json, gets the same update; its new decoded sha256 is 1b5bab59...
  - k/p.json: code_sha256 and the pin_paths and uploads entries 53faadaa -> 1b5bab59 (129,141 B).
  - k/c.json and k/n.json: milestones and recipe.milestones [100,200], checkpoint_disk_guard.planned_weight_exports 3, and the code pin (c -> new k/7.json, n -> u/1b5bab59...). Nothing else changes; refresh_recipe is not used.
  - k/j.json: preflight and links, below.
  - New members b/il.py and b/dp.py.
- Install consequence: X/n/u/<new c0 sha256> must hold the new code record bytes (z.py:472-475 copies every p.json upload from n_root/u) before the job stages.
- Not changed: k/h.json routing_selection pin (a49f117f) and k/y.json. The selection pin and what feeds it change after mode r, which is the coordinator's run.
- launch_r1.build.verify(new tree) returns the seal; py_compile 34/34; bash -n passes on j_new.sh and every kit .sh; no __pycache__.

## Item 2: init links by the kit (b/il.py, j.sh before t.py)
- Runs in the sandbox after rv.py passes and before t.py. It reads v.json's init_artifact pin and r1_training.persisted_files and hashes the artifact. The artifact's full_weights and heads paths give the two raw names: parent of full_weights.json, and heads.pt. Each must lie under <mount>/runs and becomes a symlink to the staged copy that persisted_files names by sha256.
- It hashes full_weights.json and heads.pt against their pins, checks that every manifest member exists, never replaces an existing entry, and logs both readlinks and hashes (il.log and a tk_step line).
- Refusals, each by name: INIT_LINK_PERSISTED_FILES_MISSING, _ARTIFACT_PIN_MISSING, _ARTIFACT_TARGET_DIFFERS, _PIN_MISSING, _TARGET_MISSING, _TARGET_DIFFERS, _MEMBER_MISSING, _OUTSIDE_RUNS, _EXISTS, _UNRESOLVED.
- Test (test/til.py, rd/til1.json): OK and an idempotent rerun pass. These refuse by name: missing heads pin, missing artifact pin, no persisted_files, heads target missing, heads target differs, shard missing, existing other link, existing real directory, raw path outside runs.

## Item 3: disk plan checks (b/dp.py)
- Right after staging (j.sh, before g.py, every mode except r): the tree's own plan() and Budget run on k/c.json, with the tree taken from the kit's sealed tar (sha checked, extracted to TMPDIR). Free space is statvfs of $Q_NS, the job folder, which is the output's filesystem. The job refuses unless free > plan + 300 GB.
- At training start (after il.py): the same on v.json and the job's tree p/s, with free space taken at cfg output (p/q/r). The bar is 0, because the save needs only that the plan fits (RULING 0409Z item 3).
- Both print free, plan and margin as one JSON line in dp.log / dp2.log, and tk_step puts that line in the job log.
- Bytes: check()'s formulas with the measured pair M = 110,246,315,968 and X = 40,421,000,132 (fix20). dp.py self-checks that the pair reproduces 174246's 6,027,674,886,604 B exactly. It also requires cfg guard == plan(recipe_for(cfg), copies 1), the same assertion as entry.py.
- Tests (test/tdp.py patches statvfs):
  - Preflight: free 5,717,540,712,448 PASS, plan 5,218,717,972,092, margin 498,822,740,356. Free plan+299.98 GB REFUSE DISK_PLAN_INSUFFICIENT; free plan+300.03 GB PASS. The real local disk REFUSES.
  - Control: the base kit 7e23bbdd's config gives plan 6,027,674,886,604 and margin -310,134,174,156, which REFUSES, reproducing 174246's failure.
  - Train mode: v.json as run (six milestones, old tree) REFUSE at 5,717.5 GB. v.json [100,200] PASS, margin 498.8 GB. At 5,453.5 GB free (after the rehearsal's ~264 GB) PASS, margin 234.8 GB. [100,200] with guard exports 7 REFUSE R1_DISK_PLAN_DIFFERS.
- Margins for the log and the card: 498.8 GB after staging (bar 300 GB holds by 198.8 GB); about 235 GB at the first real save after the rehearsal's uncleared ~264 GB.

## Item 4: wrapper jn8.sh (jn8/jn8.sh sha256 2de401bd...; diff jn8/JN8_vs_jn7.diff, 41 lines)
- Change: once training has started (t.log or p/rv.json), the hold still applies unless the trainer output p/q/r holds a completed checkpoint (checkpoint_*/complete.json), an export (m*/artifact.json) or a final run report (run_*.json). Stop exits (TERM/USR1, J7_SIG) and success stay unheld. HOLD.txt names the phase train_pre_save.
- Note: job.sh's tk_live_finish writes live_spool/stop.request on every exit, so that file cannot mark a stop. The stop is the signal.
- Test (test/t_jn8.sh): the exact wrapper bytes run in a bwrap root, with a fake folder at the X path, stub nvidia-smi (4 H100), stub kit and stub job.sh per case.
  - jn8 (rd/jn8_t1): pre-save exit HOLD (phase train_pre_save), released by RELEASE, rc 1. Stop (TERM to the wrapper) no hold, rc 143. Saved checkpoint no hold. Export written no hold. Pre-training failure HOLD (phase child), as jn7. Success no hold.
  - jn7 control (rd/jn7_ctl): the pre-save exit is not held, everything else is the same.

## Tree seal (n_review1l GO 20261122T0428Z)
- Sealed unchanged from the candidate: work/fix21/sealed_tree/ (tar, TREE35.json, T_mil.diff, T_mil_tests.log, TREE_SEAL.json 52a389bb, SHA256SUMS).
- Mirrors, each passing sha256sum -c: trinity-1-18 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w35/tree/ (over IB) and trinity-3-30 /scratch/jjyeung/n30_mirror/tree_rebuild29/tree_02fd9a95/.

## Item 6: Trinity CPU suite on the TEST kit (trinity-1-18, 04:30-04:31Z; script s/test1.sh = s/body35.sh plus the stage_test1 inputs; output rd/test1.out and rd/t18/test1/)
- Build: tree35 rebuilt from W/w34/n_go reproduces the sealed tar 30c4d564 byte for byte. b35 TEST kit W/w35/test1/n_go has seal c8b23aef18a984206c3f16db781b8d149eee2667a441f260ad566497a79cf97c (TEST only, not for review). verify(new tree) equals the seal; capsule writers reproduce the base; py_compile ok; bash -n ok; no __pycache__.
- fix17's kit tests, all still passing:
  - tchk33: old REFUSE vqa(division), new PASS.
  - t1_33: T3 PASS 800/400, T4 control REFUSE, ok true.
  - fu34 frames: A all as expected; B in bwrap all as expected.
  - ut2: ALL PASS.
  - st34 static: all_ok (the five steps a, d, h, rv and t take $Q_NS only; Q_NJ only in its three places; il.py and dp.py name neither).
- New tests:
  - tmil old/new and compare_configs old/new, as on 3-30.
  - mreaders rc 0.
  - dp preflight: 5,717.5 GB free PASS, margin 498.8 GB; the 300 GB bar REFUSES at plan+299.98 GB and PASSES at plan+300.03 GB. The 7e23bbdd control REFUSES at 6,027,674,886,604 B. Train mode with [100,200] PASS; guard 7 REFUSE.
  - til: ok, idempotent, and the nine refusals.
  - jn8 hold matrix as on 3-30; jn7 control as on 3-30.

## Install notes for the final kit (draft; final packet after task A and arming)
- The member list changes: k/t_e047002134f979bd.tar leaves the kit, and k/t_02fd9a95ebd9719c.tar, b/il.py and b/dp.py join it. z.seal and launch_r1.build.verify compare every file in the kit folder with SHA256SUMS.txt, so the old tar left in X/n/k makes every step refuse with E13 or R1_KIT_CONTENT_DIFFERS. The install must move it out of X/n (a move, not a deletion), or install into a fresh folder.
- New upload: X/n/u/<sha256 of the new decoded k/c0.json> (129,141 B; TEST value 1b5bab59..., final value from the final build) before the job stages (z.py:472-475).
- Upload order: members first; BUILD.json, then SHA256SUMS.txt last; then the post-install seal check (b/v.py) on Orchard.
- jn8.sh goes beside jn7.sh as X/jn8.sh; the submission uses jn8.sh.

## ORDER 1857Z item 4: which earlier steps read what each change touches
| change | touches | steps that read it | shown by |
|---|---|---|---|
| tree line r1_training.py:98 | tree seal, tar, k/a.json, k/7.json, k/c0.json, k/p.json code pins, s1_pool.implementation() | every step: a.py (extract, verify), the proof (authenticate, routing selection, admit, witness, handover), d.py, h.py, rv.py, u.py/t.py | the tree's own tests (T_mil_tests.log); mode r on the sealed tree (fix22, from the start of the proof); task A strict diff (n_review1l); the job's own proof |
| config milestones [100,200], guard exports 3 | configuration identity (k/c.json, k/n.json), plan | proof: admit, check_host_runtime disk_plan, routing selection, witness compare_configs, handover bind_target and continuation identity; trainer schedule; upload planner (k/y.json, unchanged) | readers table above (CPU, tree's functions); mode r and task A for the selection (rows must stay 5e35c3ce) |
| j.sh preflight dp.py (before g.py) | reads k/a.json, k/c.json and the tree tar; writes only TMPDIR (temp dir) and dp.log | no later step reads dp.log | tdp tests (pass, bar edge, refuse, 7e23bbdd control) |
| j.sh links il.py (after rv.py, before t.py) | creates two symlinks under X/runs (the job's rp) | only t.py's ranks 1-3 at load_model (n_review1k 0246Z/0250Z reader audit); earlier steps ran with rp empty | til tests; option H in 174246 (links worked, four ranks loaded); the rehearsal makes the same links |
| j.sh dp.py train (after il.py) | reads v.json and p/s; writes dp2.log | nothing reads it | tdp train tests |
| b/il.py and b/dp.py added | kit seal | every seal check (z.seal, verify) recomputes from SHA256SUMS.txt | verify(new tree) equals the seal; st34 static |
| jn8.sh | wrapper hold only | no kit step | t_jn8 matrix, with the jn7 control |

## ORDER 0436Z item 4: the leg's metrics
- Today: the trainer writes p/q/r/metrics_<attempt>.jsonl. The only publisher that copies it is b/pc.py small() (the --loop-small process, every 600 s, and once at the end), which writes into X/o/<job>/live/ under copy.json's single 50 MB budget. Logs get 40 MB and the metadata share is 50 - 40 - 1 MB - markers, about 9 MB. Any metrics file above that is listed as "omitted: copy byte cap". The exit archive o.tar (b/o.py, 50 MB, uploaded to the GCS object o) holds logs and results but no metrics. No checkpoint or export upload carries the metrics either (they sit at the run folder's top level).
- So the losses leave the node only until the file passes about 9 MB, roughly the first 50 steps at P's 0.19 MB a step. A job that dies at hour ten leaves its metrics only on the node's /tmp.
- Fix (kit only, b/pc.py; new/b/pc.py, 52 diff lines):
  - New Copier.metrics(): each metrics_*.jsonl is gzip-compressed (whole lines only) to X/o/<job>/live/metrics_<attempt>.jsonl.gz with a metrics.json record (bytes, sha256, kept and omitted bytes).
  - The copy sits outside copy.json's budget, which is unchanged, with its own cap METRICS_CAP of 45 MB per file. A file whose compressed copy exceeds the cap keeps its newest whole lines and records the omitted head bytes.
  - It is called after every small() and alone in between, so the cadence is 300 s (METRICS_SECONDS). The full small copy stays at 600 s, and the final small() at the end also writes it. Publication is to X only; there is no GCS object for metrics, because k/y.json and the sessions are unchanged.
- Test (test/tmet.py, rd/tmet1): a synthetic 76.8 MB metrics file of random floats gives a 28.7 MB gz (ratio 2.7, the worst case for random floats; real logs compress at least as well). The round trip equals the whole-line prefix, and the unfinished last line is left out. With the cap set to 1 MB: a 0.91 MB gz keeping the newest 2.43 MB of whole lines, with 74.3 MB recorded as omitted. With no metrics file, nothing is written.
- At 460 steps (~87 MB raw) the gz should stay under 45 MB. X traffic is one atomic replace of up to ~33 MB every 5 min.

## ORDER 0436Z item 5: the clock for a job whose training starts 5.8 h in
- Clock stop: the trainer's clock starts at TK_JOB_START (carrier_c1_run.py:2878-2882: started is moved back by now - TK_JOB_START). The stop fires when elapsed + pending + next_cost >= 86,400 - 3,600 = 82,800 s after the job start (:2437-2444). next_cost is at most p95 300 + checkpoint 600 + export 600 s from cfg schedule, so the stop save begins between about 22.6 h and 23.0 h after the job start, and training gets about 16.8-17.2 h (about 450-465 steps at 133 s). pc.py's nominal_stop uses the same TK_JOB_START + wall - stop_before.
- Stop upload in the time left: from the stop at 22.6-23.0 h to pc.py's deadline (SLURM_JOB_END_TIME - 15 s = 86,385 s; the exit archive is reserved from 150 s before it) there are about 3,600-5,100 s. These hold the stop save (P: 65-70 s), its persistence (being measured; estimated 6-17 min), the stop export and its persistence, and then e3's 143 + 1,482 s for the uploads. That fits if both persistence passes stay below about 15 min together. Slurm's TERM comes at 85,800 s (--signal=B:TERM@600).
- Hour-zero assumptions: neither the trainer stop nor the publisher deadline assumes training started at hour zero; both run from TK_JOB_START or SLURM_JOB_END_TIME. Two counts are sized for a full 82,800 s of training and are only upper bounds for a 17.2 h window:
  - the disk plan's 14 planned states (tree; ceil(82,800/7,200) + 2; T-est is the first-boundary fix);
  - k/y.json's 16 checkpoint objects. About 10 states are really saved (first-step admission at step 1, one every 7,200 s, the stop).
- The gate's review_wait_seconds 7,200 and the 5.8 h of staging and proof come out of the same 24 h, which is why training starts late.

## Tree pins parameterized
- in/b35.py takes the tree from a tree35 output folder (TREE35.json: seal, tar, sha, changed file). A second tree line only needs in/tree35.py extended and rerun; the kit's k/a.json, k/7.json, k/c0.json and k/p.json pins follow automatically. b35.py asserts only the base tree 9d2bbb8a and its r1_training.py hash, so a second changed file will need its own loop over the recode step; that is a one-line change.

## T_mil_to: T-mil plus the default group timeout (ORCH RULING 0514Z; persistence measured at 607.9 s)
- Diff: work/fix21/T_mil_to.diff (b84c5da4), against 9d2bbb8a.
  - r1_training.py:98 as in 02fd9a95.
  - carrier_c1_run.py:2874: "(15 min)" -> "(30 min)".
  - carrier_c1_run.py:2876: `30 if cpu else 900` -> `30 if cpu else 1800`.
  - The increment over 02fd9a95 alone: T_to_increment.diff (9a905055).
- Candidate (tb/t4, built by in/tree35.py 'timeout'): seal db42866fd9e8d0090276686527e8ebd8837ab2a9401609d81039b8784187f034; tar t_db42866fd9e8d009.tar, sha256 f5db525fc8efcf69c99ec43fd29ba029f6fd54fc0465c0431780643ecf8e47d5, 2,807,774 B. Not sealed.
- Tests: T_mil_to_tests.log (8c17eccc).
  - Gloo world-4 harness (test/tto.py, rd/tto.log, scaled 1/60): new 1800 passes uploads of 607.9 and 1200 and fails at 1900. Old 900 passes 607.9 and fails at 1200.
  - 28 tree test files (startup and r1 importers): identical outcomes, old vs new.
  - With LANE_TEST_OUTPUT and R2_PROOFS set: 41 passed and 4 errors on both trees.

## Tree db42866f sealed (n_review1l GO 0428Z and 0553Z); supersedes 02fd9a95
- work/fix21/sealed_tree2/: tar t_db42866fd9e8d009.tar f5db525f, TREE35.json, T_mil_to.diff b84c5da4, T_to_increment.diff, T_mil_to_tests.log, TREE_SEAL.json, SHA256SUMS.
- Mirrors, each passing sha256sum -c:
  - trinity-1-18 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w35/tree2/ (over IB);
  - trinity-3-30 /scratch/jjyeung/n30_mirror/tree_rebuild29/tree_db42866f/, with the extracted tree in tree_clean/ (digest re-checked = db42866f).

## Item 5: extended gate rehearsal (fix21r; rh_ext/REPORT.md)
- After its two steps, the rehearsal runs the trainer's own checkpoint(), persistence milestone() (archive copy), export() and milestone() on four ranks inside train(), on the default group, with the job's Budget. Then one pass of the kit's pc.py planner runs against a local recorder, with no network.
- Scratch: about 270 GB on the node's /tmp, not cleared. Against the plan's margin, 498.8 GB after staging leaves about 229 GB at the first real save.
- go.log prints PERSIST_SECONDS with a DANGER mark above 800 s or 1600 s.
- CPU tests all pass, including the dry run as fix15 test 4 on both kits.

## ORDER 0556Z: writes to /project after training starts, and what a full /project does
The training process cannot write the real /project. j.sh's sandbox (tk_bwrap) binds every top-level host entry read-only, so the real /project is read-only. $X is node-local $Q_ROOT/x, $X/runs is node-local rp, $P is read-only node-local, and the trainer output p/q/r is node /tmp. The one writable real-/project bind is Q_LIVE = X/o/<job>/live (rv.py location()), which only rv.py writes, and rv.py finishes before t.py starts.

Every /project write during training comes from separate processes:
| writer | what, where, how often | on ENOSPC |
|---|---|---|
| jn8 j2.py (setsid loop) | j2.log/j2.err screened tails, up to 300 KB each, X/o/<job>/, every 600 s | exception caught, line in node j2.retry.log, retry next pass; job goes on |
| jn8 j6.py (setsid loop) | live mirror (mem, alarm, tails, gate.txt, df, live.json), up to 2 MB, X/o/<job>_live/, every 120 s, each snapshot a child under timeout | child exits 1, ignored; retry next cadence; job goes on |
| pc.py --loop-small (setsid, from pc.sh) | small(): markers, tails, metadata and state, up to 50 MB (copy.json), X/o/<job>/live/, every 600 s; new metrics_<attempt>.jsonl.gz, up to 45 MB each, plus metrics.json, every 300 s | Copier.attempt catches every Exception and notes it in node live_spool/retry.log; the next cadence retries (atomic() reuses its .part name); job goes on |
| pc.py --loop (uploads) | GCS only; paths() checks X/o/<job>/live, X/n_ck/<job> and X/n_s but writes neither (n_ck is never written) | attempt catches; job goes on |
| at exit only: o.py | o.tar and RESULT.json up to 50 MB to X/o/<job>/ | OSError caught, local retry.log |
| at exit: pc.py --final / --small | copy_exit, final small | `|| true` in pc.sh tk_live_finish |
| at exit: ep.py | evidence copy | errors caught (R1_EVIDENCE_COPY_FAILED), `|| true` |
| at exit: jn8 j7.py tb and hold, j2 fallback | tb.txt up to 200 KB, HOLD.txt, HOLD_END.txt, j2.fallback.log | `|| true`; no HOLD.txt means no hold ("HOLD record not written; no hold") |
| before training only | rv.py v.json and WAITING_REVIEW (X/o/<job>/live), cs.py publish (live/c4.json), j6 gate copy (up to 10 MB, X/o/<job>_gate) | before t.py; a failure ends the job before training (pre-training hold) |

- Item 2: no write to /project can kill training, so nothing needs softening. Every writer during training is a separate process that catches the error and retries at its cadence. No tree line is needed.
- Item 3: checkpoints and exports go to GCS through the upload sessions (pc.py send -> gc.py PUT on the session URLs). The session map is read from X/n_s at the publisher's start and cached on the node (live_spool/private/sess.json), and receipts and claims are node-local, so they do not depend on /project once training runs.
- GiB per whole job (ORDER 0507Z item 4):
  - Resident at the end, at most about 0.21 GB: live copy 50 MB, metrics gz 45 MB (about 33 MB expected), o.tar 50 MB, v.json and WAITING_REVIEW (KB), gate copy 10 MB, live mirror 2 MB, logs 0.6 MB, tb 0.2 MB, and mode-q receipts of about 6 MiB (174246 measured). Atomic replaces add up to 95 MB of transient space.
  - Cumulative bytes written over 24 h, worst case: live copy 144 x 50 MB = 7.2 GB, metrics 288 x 45 MB = 13 GB (3-4 GB expected), mirror 720 x 2 MB = 1.4 GB; under 22 GB in all, with at most 0.3 GB resident at once.
  - Well under 1 GiB of free /project is needed; the 3 GiB floor covers it.

## TEST kit on tree db42866f, full suite on trinity-1-18 (05:55-05:58Z; s/test2.sh = s/body35b.sh plus stage_test2; rd/test2.out, rd/t18b/)
- tree35 'timeout' rebuilt from W/w34/n_go reproduces the sealed tar f5db525f byte for byte.
- The TEST kit W/w35/test2/n_go has seal 5d2e9b5d35aaa3a13933248c94a3e905e863657b6eba49da427e11ec229e9dfe; the local kt/test5 build has the same seal.
- Changed members vs 7e23bbdd:
  - k/a.json, k/7.json, k/c0.json, k/p.json, k/c.json, k/n.json, k/j.json, b/pc.py, BUILD.json, SHA256SUMS.txt;
  - added b/il.py, b/dp.py, k/t_db42866fd9e8d009.tar;
  - removed k/t_e047002134f979bd.tar.
- The new code record (decoded k/c0.json) is da19bb3ad9e9227e12bc28161713ae6a1f2a680e559039e290caa2cff0bc6eca (129,141 B). It must be at X/n/u/<sha> before the job stages. 1b5bab59 was the 02fd9a95 record and is superseded.
- Every test passes:
  - verify(new tree) equals the seal; py_compile; bash -n;
  - tchk33, t1_33, fu34 A and B, ut2 ALL PASS (with the new pc.py), st34 all_ok;
  - tmil, compare_configs, mreaders, dp (preflight, bar edge, 7e23bbdd control, train), til, the jn8 matrix with its jn7 control, tmet (metrics);
  - the gloo timeout harness: new 607.9 PASS, new 1900 FAIL, old 1200 FAIL.
- Still owed before the final seal (the coordinator's order of work): task A on the mode r output, the arming (any new k/h.json routing-selection pin and its upload), the final b35 build with those inputs, the tar, the IB mirror, and the n35_review packet (README with criteria and the ORDER 1857Z item 4 table above, INSTALL.md with the move of the old tar and the X/n/u code record).
