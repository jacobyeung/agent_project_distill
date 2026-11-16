# b01_d0guard STATUS (trinity-3-30) — a successor resumes from this file alone
Updated by the b01_d0guard Claude lane. Brief: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/b01_d0guard.md -> queue brief .../orch_n30/briefs/qs/01_d0_native_guard_kit.md. Rules: ~/.claude/CLAUDE.md Trinity rules, .../orch_n30/tools/CLAUDE_LANE_RULES.md, LANE_RULES.md. Lane folder /scratch/jjyeung/orch_n30/b01_d0guard (this node); events EV=.../orch_n30/events/b01_d0guard/. Finish or rotate by 22:30Z. No Git, no deletion, no GPU, no Orchard submission without an ORCH GO naming the job.

## Layout
- guard_kit/report/: guard_read.py (item 2 of the brief, built by this lane), inputs/ (brief-02 parser unit_from_question.py 274f04a0..., DISTANCE_LIST_DEVS1_150.jsonl 028273ec..., TASKS.jsonl a2f3fdbd...), tests/test_guard_read.py (27 tests), tests/mutants.py (25 mutants), tests/fixtures/R1_544_COMPACT.json.
- guard_kit/build/: Codex build G1 of the kit itself (item 1: C8r + export parameter, one native arm, identity proof, canary, naming, packet). BRIEF.md there; Codex gpt-6-astra high dispatched 11:52Z (codex_stdout.log; receipts under agent/scratch/codex_runs/*b01_guardkit*). Its STATUS.md and out/ are the build's state.
- work/from113/: read-only copies from trinity-1-13 native_r2 (sub/, builds/01_c8, builds/02_c8r, work/obj, np226, pyextra, p9, full_c8r return). work/from13/readk: D0 read kit (export stager) from trinity-1-3 cont_ops. work/v1c: VSTI kit V1c mirror. work/ret544: job 170056 return extracted. work/c8r_code: C8r code tar extracted.
- out/: selftest (guard_read on 170056 vs itself), tests/ logs.

## Done
- guard_read.py: self-pair on job 170056's R1.json gives zero differences on every type, means equal the record (camera 82.333/94.667/75.667, metre 61.628, distance 29.867, room 53.889); out/selftest/GUARD_READ.md. 27 tests OK (out/tests/guard_read_tests.log).
- QUESTION lane_size (default: lane up to 12 GB here; ~7 GB used).

## In progress / next
1. Mutant run (out/tests/guard_read_mutants.json): every mutant must be killed.
2. Wait for Codex G1 (guard_kit/build/STATUS.md, events/*_RESULT_final.md). Then: rerun its tests, run the operator rehearsal outside the sandbox per its out/rehearsal/RUNBOOK.md, check DIFF.md / PIN_CLASSIFICATION.md / NAMING.md.
3. Write out/GUARD_KIT_READY.md (hashes, DIFF, tests, pin table, time/disk), mirror the kit over IB to a second node (/scratch/jjyeung/n30_mirror/b01_d0guard/), STATUS to EV, RESULT event asking ORCH for the cross-family refute review of DIFF.md, pin classification and guard_read.py.
4. Submission of any guard read needs: that review, the list sha in the init-rule record, an ORCH GO.
