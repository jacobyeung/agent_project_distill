# b04_e2ehook STATUS (Devin lane on trinity-3-30, successor of the Claude lane). Updated 2026-11-16T13:35Z.
Brief: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/b04_e2ehook.md -> queue brief briefs/qs/04_e2e_reader_hook.md. Deadline 22:30Z; this Devin session rotates by ~18:15Z.
Lane folder L=/scratch/jjyeung/orch_n30/b04_e2ehook (trinity-3-30). Python: /scratch/jjyeung/envs/p1cpu/bin/python -B. Tree (read-only, imported): /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449.
## Done
- L/e2e_reader/: callhook.py, geometry.py (no guard), servers.py, grounding.py, artifact.py (manifest e2e-artifact-v1), generate.py, core.py (E2EGenerator, ORCH one-reader interface), real.py (draft, untested).
- Proof 1 token parity vs job 170056: out/proofs/REPLAY_170056_{suffix,nosuffix}.json (927/927 calls detected; forced ids equal 462/462 comparable).
- Proof 2 guard: out/proofs/GUARD_VERDICTS_DEVS1.json (sealed guard refuses 11/84, reviewed 1, new loader 0).
- Proof 3 tiny e2e CPU: tests/test_tiny_e2e.py 5 passed -> out/proofs/TINY_E2E.json.
- Scale head (heads/scale): ridge on 29 fixed-math tower features, 31 params, weights run1 a90b5216... (run2 094df94c... differs by 7.5e-17). Held-out 57 captures: within20 SH 91.2% vs S4 87.7%. Exact E3 harness on 1-18 (b04_e2ehook_sh, done 12:02Z), results pulled to heads/scale/work/out_sh, agg in work/exact_agg.txt: distance SH+G1 61.3 [54.4,67.5] vs S4+G1 62.9: -1.6 [-4.1,+1.1] -> MISSES bar (>=62.9). Oracle SO+G1 65.6.
- Selector head (heads/selector): tables 266 captures (18 excluded E3 G1, 12 failed bounded reader). Logistic refit held-out AUC .9365 top-1 62.7%; deployed .9167/62.0%. SelectorHead run1 (09c1e6ba..., trigram name, h32, null slot) AUC .9337, top-1 58.9% (-3.8 [-7.5,0.0]) -> FAIL top-1 bar. Report heads/selector/SELECTOR_HEAD_REPORT.md; numbers work/SELECTOR_HELDOUT.json. Retrain bit-identical (work/run1_retrain).
- Scale head report heads/scale/SCALE_HEAD_REPORT.md. Retrain bit-identical (work/det_a, det_b = a90b5216).
- dev-S1 CPU pricing (calls fixed at scripted arm, headline labels): tests/price_devs1.py reproduces 634/634 job scores (out/proofs/PRICE_DEVS1_old.json, identity check PRICE_DEVS1_identity.json). Scale head (out/proofs/SCALE_HEAD_DEVS1.json): displacement 82.3->73.1 (-9.3 [-14.1,-5.0]), distance 54.7->51.5 (-3.1 [-6.4,-0.6]), room unserved (ORCH 1227Z: room is direct). out/proofs/PRICE_DEVS1_scale_scale_paired.json.
- tests: tests/test_heads.py + tests/test_tiny_e2e.py 11 passed (13:04Z).
- FINDING: K1 SAM 3 cache uses prompts=dense_aliases: 26% of instances come from alias prompts (table->desk, chair->seat, lamp->light). Raw-prompt-only tables rebuilt (sl_tables.py --raw-prompts-only, 1-18 b04_e2ehook_sl/full_raw, 266 caps) -> L/heads/selector/data/caps_raw. Logistic on raw-only: held-out AUC .9422 top-1 59.9% (work/logistic_heldout_raw.json); train OOF .9271/67.9%.
- e2e_reader/stage1.py: StageOne socket (sam3_detect: raw name, K1 retention contract; routed producers; selector_inputs; SelectorHead.with_null argmax), ScaleHeadCall. real.py real_perception wired to them. assemble.py: manifest builder for the export host. tests/test_stage1_k1.py 4 passed (in-call inputs == K1 table inputs to <1e-9; ground/gap on a real K1 capture; ScaleHeadCall == head).
- EAT-1 static scan (b03 eat1.scan, proposed allowlist): out/proofs/EAT1_STATIC_SCAN.json, 101 findings in static-only mode (57 constants, mostly scale-head quantile levels; guard-verdict recording; error-response fallback in servers.py; loaders).
## Running
- 3-30 tmux b04_selraw: SelectorHead CV+train on raw-prompt tables -> heads/selector/work/run_raw (log run_raw.log). Then: SEL_CAPS=data/caps_raw SEL_TAG=_raw python -I -B eval_selector.py work/run_raw.
## Next
1. Eval raw-prompt head; update SELECTOR_HEAD_REPORT.md.
2. EAT-1 static scan of e2e_reader with lane b03's /scratch/jjyeung/orch_n30/b03_e2etest/eat1/scan.py.
3. Optional: dev-S1 price of selector / no depth cut (needs dev-S1 SAM 3 cache on 1-18).
4. out/E2E_READER_READY.md, mirror to second node, final RESULT event asking for cross-family review + one-reader mapping.
## Open questions (defaults in force)
- CPU first-batch forward of the real export needs the step-544 weights (AWS only). Default: the parity kit runs it on the export host's CPU before any GPU; this lane does not pull the export to Trinity.
