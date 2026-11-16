# b01_d0guard STATUS (trinity-3-30) — a successor resumes from this file alone
Updated by the b01_d0guard Devin lane (successor, started 12:22Z, session ends by 18:20Z). Brief: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/b01_d0guard.md -> queue brief .../orch_n30/briefs/qs/01_d0_native_guard_kit.md. Rules: ~/.claude/CLAUDE.md Trinity rules, .../orch_n30/tools/CLAUDE_LANE_RULES.md, LANE_RULES.md. Lane folder /scratch/jjyeung/orch_n30/b01_d0guard (this node); events EV=.../orch_n30/events/b01_d0guard/. Finish or rotate by 22:30Z. No Git, no deletion, no GPU, no Orchard submission without an ORCH GO naming the job.

## Layout
- guard_kit/report/: guard_read.py (item 2 of the brief, built by this lane), inputs/ (brief-02 parser unit_from_question.py 274f04a0..., DISTANCE_LIST_DEVS1_150.jsonl 028273ec..., TASKS.jsonl a2f3fdbd...), tests/test_guard_read.py (27 tests), tests/mutants.py (25 mutants), tests/fixtures/R1_544_COMPACT.json.
- guard_kit/build/: Codex build G1 of the kit itself (item 1: C8r + export parameter, one native arm, identity proof, canary, naming, packet). BRIEF.md there; Codex gpt-6-astra high dispatched 11:52Z (codex_stdout.log; receipts under agent/scratch/codex_runs/*b01_guardkit*). Its STATUS.md and out/ are the build's state.
- work/from113/: read-only copies from trinity-1-13 native_r2 (sub/, builds/01_c8, builds/02_c8r, work/obj, np226, pyextra, p9, full_c8r return). work/from13/readk: D0 read kit (export stager) from trinity-1-3 cont_ops. work/v1c: VSTI kit V1c mirror. work/ret544: job 170056 return extracted. work/c8r_code: C8r code tar extracted.
- out/: selftest (guard_read on 170056 vs itself), tests/ logs.

## Done
- guard_read.py: self-pair on job 170056's R1.json gives zero differences on every type, means equal the record (camera 82.333/94.667/75.667, metre 61.628, distance 29.867, room 53.889); out/selftest/GUARD_READ.md. 27 tests OK (out/tests/guard_read_tests.log). Mutants 25/25 killed (out/tests/guard_read_mutants.json).
- QUESTION lane_size (default: lane up to 12 GB here; ~7.3 GB used).
- Codex G1 (guard_kit/build/) finished 12:11Z NOT READY: components + 90 unit checks + 25/25 report mutants; blockers in build/out/RELEASE_BLOCKERS.json (candidate training closure, production integration, naming, whole-worker rehearsal). code_g1.tar dab2e6fb..., inputs_g1.tar 880b6ac4...
- D0 candidate closure fetched 12:38Z read-only from Orchard x_f5c353f7 (runs/359fcc3c/inputs, m1+m50 artifact.json, binding.json, k/d6827df0.json, 7.json, routes, exclusions, launch/4/staging): work/d0closure/closure_359fcc3c.tar sha256 41bb90d0418ab37715ae66358e875cb4f337f7a63349df4d96498c6452cda964, extracted x/, CLOSURE_FILES.sha256. Trainer tar on Orchard k/t_b01ce449beffe35b.tar 845b1789... = local copy. m50 artifact differs from m544's only in config/run-seal/tensor/step/trained-group fields; initial hashes chain to m544 finals. QUESTION 1233Z candidate_closure (default: read-only copy allowed).
- Orchard login gcloud (even with CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud) returned rc=120 on `gcloud storage cat`; not needed now (artifacts are files in runs/359fcc3c/m<STEP>/).

## In flight
- Codex G2 finished 13:18Z NOT_READY (guard_kit/build2/events/20261116T1318Z_RESULT_final.md): closure admission PASS with unchanged C8r restoration checks (out/CLOSURE_ADMISSION.json, RESTORATION_TEST.json), dual staging/coordinator/canary/admission/packet implemented, 124 checks pass, 25/25 mutants. code_g2.tar 15d144c0..., FAMILY 6a1d5c22.... Open: naming inside signed metadata/trainer paths; whole-worker; review.
- Whole-worker rehearsal outside the sandbox (I run it): fixed bwrap 0.4 mountpoint bug with split_mounts() in build2/out/rehearsal/run_whole_worker.py (original kept as run_whole_worker.g2_orig.py). Run 2: namespace + staging PASS, proof failed: p1cpu lacks torchvision. Run 3 uses /scratch/jjyeung/envs/pdtest_v1 (py3.12.13, torch 2.10, torchvision 0.25, transformers 5.12.1) via run_whole_worker_tv.sh; logs out/whole_run3.log, result in newest build2/out/rehearsal/whole/<hex>/RESULT.json.

## Next
1. When G2 ends: rerun its tests; run out/rehearsal/run_whole_worker.sh outside the sandbox (userns works on this node: `unshare -Ur true` OK); check DIFF.md / PIN_CLASSIFICATION.md / NAMING.md / RUN.md.
2. If blockers remain and time allows (m200 export ~17:50Z; m200 stop-rule read has general first from 17:30Z), dispatch a fix round G3 with the exact failures.
3. Write out/GUARD_KIT_READY.md, mirror kit over IB to a second node /scratch/jjyeung/n30_mirror/b01_d0guard/, STATUS to EV, RESULT asking ORCH for the cross-family refute review (DIFF.md, pin classification, guard_read.py) and stating the one-reader mapping (guard_read.py scoring/rule functions importable by b04).
4. Submission needs: review, list sha in the init-rule record, ORCH GO naming the job.
