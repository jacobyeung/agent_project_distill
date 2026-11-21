# n_review1i STATUS (successor resumes from this file alone)
Lane n_review1i: headless Claude Code Opus, trinity-3-30, started 2026-11-21 06:14Z, 10 h timeout; rotate RESULT due ~15:10Z. Brief B/briefs/n_review1i_c.md (+ n_review1h.md). B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Tree lane: tree_rebuild27 (inbox /scratch/jjyeung/orch_n30/tree_rebuild27/inbox). Ops: n_ops11 (inbox /scratch/jjyeung/orch_n30/n_ops11/inbox; n_ops10 ended 14:35Z).

## Current job and what is owed
- Launch job **174134** (a15_cot_apb2edfac4, advanced, 4 H100), RUNNING since 13:06Z on orchard-community-3 (gate ~15:30Z), released by tree_rebuild27 on kit X/n = 9e809db4e0817adfad3d4ebd74fb39a6d15b39aea8f0cb129a0da5c4ecaf3405 and wrapper X/jn7.sh = 98edfd9e1f30f4ba8190702091bed87a8e4b2aa5839468b22ebec30d4b3846fd (both confirmed by me on Orchard 13:03Z). Gate (WAITING_REVIEW.json) ~2.4 h after start; rv.py waits 7,200 s, then R1_REVIEW_TIMEOUT (no training); a failure before training holds the node up to 180 min (jn7; HOLD.txt, tb.txt, RELEASE in X/o/<job>/).
- 15:00Z: 174134 HELD (jn7) after admit refused in prepare: ValueError 'Preservation/pointing receipt or division differs' (carrier_c1_run.py:542 via s1_admission.py:225; tb.txt on X/o/174134). The guard fix worked (model build passed). ORCH ORDER 1502Z: tree_rebuild27 classifies the cause on the held node and walks the rest of the path in a scratch copy; no RELEASE before 17:30Z or ORCH's answer. Expect a fix to review (files, sha256, criteria), then Orchard confirm, then a fresh held job.
- OWED at WAITING_REVIEW (n_ops11 tells at ~75% prep; or read events/n_ops/N_WATCH_STATUS.md): on trinity-3-30 run
  `bash /scratch/jjyeung/orch_n30/n_review1i/work/gate/run_gate.sh 174134 /scratch/jjyeung/orch_n30/<lane>/gate_174134`
  (if /project is full and n_ops10 streamed the files to trinity-3-30 per ORCH ORDER 1055Z: add `--local <folder>`).
  It fetches the named live files + X/o/174134_gate, runs admit_test.sh on 1-18 (into W/w24z14/work/gate_<job>_<stamp>; my default, no answer received), prints GATE lines.
  - GATE ALL PASS: `python3 -I work/gate/make_review.py <run dir> 9e809db4 <lane>/review_174134.json`; post RESULT with PASS, path and sha256; copy review.json to n_ops11/inbox for install at X/n_r/review.json (dir 700, file 600). review.json keys only verdict/config_identity/evidence (rv.py:290).
  - FAIL: BLOCKER to ORCH + tree_rebuild27 naming the point and evidence; tree_rebuild27 scancels (RULING 0211Z item 4). Judge a FAIL by hand before posting if it looks like a check assumption (e.g. f.json record count != 288, routing sha field names), and say so.
- Any new kit/wrapper change from tree_rebuild27: review once (files, sha256, criteria), then confirm Orchard bytes before release.

## Gate kit (work/gate/, copies events/n_review/evidence/n_review1i/gate/ and 1-18 n_review/r1i/gate3)
gate.py 7be0fb0b, run_gate.sh fe4dcf06 (named-file fetch, --local mode), test_gate.py c6eb3b55 (TEST ALL_OK: pass + 9 negatives), USAGE.md c79e17e3, make_review.py b845a1e6. Design record distill_design/N_LAUNCH_REVIEW_GATE_CHECK_20261121.md.
Gate inputs: X/o/<job>/live (kit writes v.json, identity.txt, e0-e7, h0, c0-c4, s0-s3, WAITING_REVIEW) + X/o/<job>_gate (jn6/jn7 copy of N/p/q/b/{population,indices,reader_filters,binding,receipt}.json, N/p/q/f.json; n_ops10 srun fallback if SHA256SUMS absent, <6 lines, or NOTES names absent/skipped).

## Verdicts posted (events/n_review, this lane)
0626Z gate inputs node-local (accepted ORCH 0630Z); 0641Z gate script; 0649Z jn6 0c0e5d3b GO; 0657Z pre-submission PASS (armed q ece78fea, n_go 3f55530c on Orchard); 0713Z RLIMIT path confirmed; 0721Z fix_rlimit b44a4915 GO; 0800Z fix_spawn 06d9a1b5 GO; 0806Z no in-place swap (E32); 0921Z 174101 reading (hash-named folder; site corrected by tree_rebuild27 to the witness); 1004Z fix_proc 4e29bdfb GO; 1209Z 174113 cause = our mg.py guard (accepted ORCH 1214Z); jn7 98edfd9e GO; fix_cuda 9e809db4 GO; Orchard confirms 0723Z, 0811Z, 1014Z, 1303Z.
Jobs: 174085 cancelled (kit swap); 174101 FAILED witness processor folder; 174113 FAILED mg.py guard in admit; 174134 current.
Task A restated PASS (n_review1h 0212Z) stands: a49f117f / 522a3be3 / 5e35c3ce / 4e8e6c04.
- 15:01Z RESULT rotate posted.
