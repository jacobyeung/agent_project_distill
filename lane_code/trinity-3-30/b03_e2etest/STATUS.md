# STATUS b03_e2etest (EAT-1 acceptance test), trinity-3-30
Owner: Devin successor lane since 12:22Z 2026-11-16 (rotate by 18:15Z). Percent done: ~90% (build, baselines, RUN.md, mirror and design record done; the refute review and the b6 rerun are open). In flight: nothing (no tmux, no Codex, no governor streams, no Orchard jobs).
Brief: B/briefs/b03_e2etest.md -> B/briefs/qs/03_e2e_acceptance_test.md (B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30). L = /scratch/jjyeung/orch_n30/b03_e2etest. Env: /scratch/jjyeung/envs/p1cpu (torch 2.11 cpu, transformers 5.12.1).
Rulings in force: ORCH 1227Z (room size is direct; a room call goes unserved and its rate is printed); ORCH 1228Z (no checkpoint events; events only for questions, blockers, final results and rotate); ORCH 1155Z (ReVSI first; frame count 32/64 as a parameter; SFT first; ruling 5: fixed math = unprojection + printing head outputs; unit conversion or answer reformatting outside the model fails).

## Done
- Kit L/eat1 (file sha256 list L/work/EAT1_FILES.sha256): run.py, hook.py (split LM entry supported), scan.py (+A3.unit_conversion, raise-only `if` validation exempt), allowlist.json (PROPOSED; pre-ruling copy L/work/allowlist_pre_ruling5.json), closure.py, artifact.py, adapters/{c8r_tiny,gf1_tiny,c8r_native}.py, toy/, tests/.
- Tests: `cd L && EAT1_TMP=$L/work/tmp /scratch/jjyeung/envs/p1cpu/bin/python -m unittest eat1.tests.test_eat1` -> Ran 16 OK (L/work/test_run_5.log; 13:31Z: added the planted head_method variant, and the model-code exemption now covers plain constants only). Latest tiny runs: L/work/c8r_tiny/run6 and L/work/b5_gf1_tiny/run4, with clause results identical to the earlier runs.
- L/out/BASELINE_C8R.md (+ _FINDINGS.md): tiny run L/work/c8r_tiny/run5 (A2/A3/A4 FAIL, A1/A5 PASS on the tiny path); static scope L/work/c8r_static/SCOPE_TIER1.txt, 45 files, 965 findings.
- L/out/BASELINE_A2_TREE.md (+ _FINDINGS.md): b5 tree L/work/nextleg/b5/work/tree_r1 (tar sha bc31a06d); 33 files, 571 findings; tiny runs L/work/b5_tiny/run1 and L/work/b5_gf1_tiny/run2 (GF-1 A1/A5 PASS).
- L/out/RUN.md (GPU operator recipe, about 2.5 h on one H100 at 32 frames), L/out/EAT1_READY.md.
- Mirror (current): L/work/mirror/b03_e2etest_eat1_v1c.tar sha256 016990fe77f4abef3c44cfc94e60e5dad66554681c834bd55bbc2842ea687c18 = trinity-1-18:/scratch/jjyeung/n30_mirror/b03_e2etest/b03_e2etest_eat1_v1c.tar (checked 13:33Z). v1 and v1b are superseded (REMOVAL_CANDIDATES.md).
- Design record /data2/jjyeung/agent_project_data/distill_design/EAT1_ACCEPTANCE_TEST_20261116.md + INDEX.md line.
- RESULT event eat1_ready (asks for the cross-family refute review).
## Next
1. Watch B/events/b03_e2etest/*_ORCH_* and L/inbox for the review verdict; fix what it finds (each fix gets a planted-violation test), rerun tests, then re-mirror as _v2.
2. When build 6's final package lands (B/events/tree_rebuild/STATUS.md names it), rerun the static scan with SCOPE_READ.txt mapped to the b6 tree and both tiny adapters with tree=<b6>, and update BASELINE_A2_TREE.md §4.
3. The GPU EAT-1 run waits for an ORCH GO naming the card or job (RUN.md); c8r_native.py has not run on a GPU (14:08Z: every nomdg, perception, common, routed and evalpath name it uses exists in code_c8r and the tree), so run one item first.
## Open questions (defaults in force)
- The 7 interpretation points in out/EAT1_READY.md go to the reviewer. Default: as built.
