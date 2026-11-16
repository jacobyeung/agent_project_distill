# End-to-end reader (brief 04): reviewed GO for the parity read; read waits for a card

Lane b04_e2ehook, trinity-3-30, 2026-11-16. Code `/scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/`, parity kit `parity_kit/` (README has every command), heads `heads/scale`, `heads/selector`, tests `tests/`, proofs `out/proofs/`. GPU copy on trinity-1-13 `/dev/shm/jjyeung/b04/host2`.

## Outcome
The reader serves every camera call from the in-call G3T tower, the own gravity head and the own depth head (scale = median(own depth / G3T depth) over confident grid points), and serves ground/gap through a stage-1 socket: in-call SAM 3 on the raw name, the runtime's candidate producers with each name featurised alone, the learned selector head with a null slot, plain unprojection of every mask pixel, a min-area box. Room calls are unserved and counted. One `generate` entry, one prefill, the KV cache continues through every forced response token, and the audit refuses any data file, code file or native open outside the manifest and every write.
- "In the forward" means operationally: the hook fires after a call's last token is sampled and before the next LM forward (ORCH 1440Z). Head responses are printed in step 544's trained v3.14 format by the pinned tree formatters; the model converts units and writes its answer itself.
- Selector run_iso passes B6's kill bar; the learned scale head misses its bar and is not used in a claimed read.
- K1's SAM 3 cache contains an alias table (26% of instances from alias prompts); the shipped selector never sees alias instances.

## Reviews (Codex GPT-6 Astra, high; receipts under agent/scratch/codex_runs/)
| Review | Verdict | Disposition |
|---|---|---|
| 20261116T140434Z_b04_review_e2e | NO-GO, 9 findings | 2-9 fixed; 1 recorded as the operational definition above |
| 20261116T150929Z_b04_review_fixes | NO-GO: 2 (aliases under other names), 7 (quote window) | fixed: any-name rebinding of native openers, quote state over the whole text |
| 20261116T155033Z_b04_review_parity | GO AFTER FIXES: asset authentication, journal provenance, runtime identity, fence length | fixed (Codex fix build 20261116T162411Z_b04_fix_parity; fence by the lane) |
| b04_review_delta | GO | all four hold; no new blocker |

## Proofs and tests (35 tests + 53 kit tests pass: `cd L && TMPDIR=$PWD/work/tmp /scratch/jjyeung/envs/p1cpu/bin/python -B -m pytest -q -p no:cacheprovider tests/`)
| Check | Result | Evidence |
|---|---|---|
| Hook vs job 170056 | 927/927 call texts and positions equal; forced ids equal on all 462 comparable responses (465 ground/gap/room responses kept only digests in R1) | out/proofs/REPLAY_170056_{suffix,nosuffix}_v5.json |
| Tiny-model e2e, every call type | 1 prefill; cache continues; loader refuses outside and changed files; perturbing a head changes only its responses | tests/test_tiny_e2e.py |
| Review regressions | native openers, writes, outside .pth refused; per-name features independent of call order; cap 30; every mask pixel lifted; no depth gate; quoted calls skipped, long calls found; response at the cap complete and cached; selector training never opens held-out tables; frame count is a parameter (sealed GeometryContract is 32-only: xfail) | tests/test_review_fixes.py |
| Stage 1 vs training tables | head inputs equal to < 1e-9 on a real K1 capture | tests/test_stage1_k1.py |
| EAT-1 (lane b03 harness, current code) | A1 PASS; A2 PASS (one entry per item, 0 injected tokens); A3 FAIL: shape and canvas constants (call window, 0-1000 canvas, pose 9, lift floor 0.3, selector feature eps) and sealed-tree constants; A4 FAIL: 7 static findings, all in the sealed tree (routed_candidates 'rejected', box_v313 'not seen'/'box unavailable'; tree build 7); A5 i and iii PASS, ii FAIL only for the SAM 3 byte-buffer stand-in | out/proofs/EAT1_DYNAMIC_v6/EAT1_REPORT.json |
| Real step-544 model, CPU, trinity-1-13 | restore + load in 62 s; one object-distance item end to end (SAM 3 off: ground unserved, the model answered from the video, score 0.8; prefill 439 s, G3T 589 s, total 1464 s) | 1-13 /dev/shm/jjyeung/b04/host/b04_e2ehook/parity_kit/host_results/cpu_first_c |

## Heads on K1 (held-out rooms, paired room bootstrap 10,000 draws, seed 20261116)
| Head | Metric | Head | Bar arm | Diff | Verdict |
|---|---|---|---|---|---|
| Selector run_iso (6d97c524) | top-1 / AUC, raw names, names alone | 59.9% / 0.942 | refit logistic 59.2% / 0.941 | +0.6 [-2.7, +3.9] / +0.001 [-0.008, +0.012] | PASS |
| Scale (a90b5216) | distance MRA | 61.3 | S4+G1 62.9 (oracle 65.6) | -1.6 [-4.1, +1.1] | FAIL |
Reports: heads/selector/SELECTOR_HEAD_REPORT.md, heads/scale/SCALE_HEAD_REPORT.md; selector numbers heads/selector/work/SELECTOR_HELDOUT_iso.json.

## Parity read (636 dev-S1 items of job 170056, step 544, trinity-1-13)
Kit: `parity_kit/gpu_113.sh CARD ARM NAME [KEYS]` runs inside a bwrap view that shows /dev/shm/jjyeung at /scratch/jjyeung/b04shm (the sealed SAM 3 tower accepts only /scratch paths). Arms: own_depth (claimable) and scale_head. Keys: keys_smoke.txt (one per question type), keys_part{0,1,2}of3.txt. `parity_kit.compare` gives the room-paired table against 170056 and camera call agreement, labelled within noise because Trinity has no fla kernels. Not yet run: it waits for an ORCH_CARD.

Interim (stopped 18:29Z, 51/636 keys of own_depth p0; host withdrawn): distance 30.6 old vs 21.4 new, -9.2 [-19.1, +0.6], 28 rooms; 14/98 grounds lost (`not seen`), boxes 2.2x old volume (median), 16/49 gaps unanswered vs 3. Files: out/proofs/PARITY_own_depth_p0_51rows.jsonl, out/proofs/PARITY_P0_51_DIAG.txt.

K1 lifting price (CPU, E3 harness copy with GT masks, 1-18 /scratch/jjyeung/orch_n30/b04host3/lift_price/harness): held-out S4+G1 deployed 66.3; shipped every-pixel lifting 25.4 (-40.9 [-46.5,-35.2]); bestspread (best frame, stencil spread <= median) 65.7 (-0.6 [-3.1,+1.5]; registered bar CI low >= -3.0 missed by 0.1). The shipped reader is unchanged pending ORCH.

## Known defects
- Portrait frames: routed_features.resize stretches every mask to the 480x640 canvas, in the selector's K1 tables and in the call alike; dev-S1 has 12 of 84 portrait captures (14 of 636 items).
- 64-frame reads need tree build 7 (the sealed GeometryContract and ProfileGeometry.has are 32-only).
- The kit's restore omits the stage-1 depth init (heads.pt restores every private-depth tensor strictly) and loads the base from the step-544 shards; non-weight assets are authenticated against the job's original model manifest.

## Hashes (sha256 prefixes)
e2e_reader: artifact 5b4a4fe5, callhook 044caa0f, core dbbda5b8, generate 4101148f, geometry 93039228, grounding 47ab8435, parity 813e8111, real 7726e90f, servers 3cd2e6db, stage1 dc9c9189. parity_kit: stage_restore df892303, run_parity 30628243, compare f1845e41, provenance 8502c903, build_manifest dc1ffbaa. Weights: selector run_iso 6d97c524, scale run1 a90b5216. Step-544 heads.pt 8bb5e151, artifact.json 1d6eeb28. EAT-1 report 6c810929.
