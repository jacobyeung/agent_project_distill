The tower-frames kit passes CPU validation. No GPU work ran; GPU peaks below are reviewer estimates.
Required held-out fix: code/evaluate_v2.py:139 checks labels before consume_heldout; code/test_kit.py:253 proves the receipt stays unwritten.
Review edit 1: code/evaluate_v2.py:34 retains NO_CONVERT_EXPORT rows; code/evaluate_v2.py:70 asserts every available scale agrees within 1e-4.
Review edit 2: code/evaluate_v2.py:25 discards MISSING placeholders; code/evaluate_v2.py:129 persists added_frame_gain; scripts/finalize_v3.py:57 writes no DECISION placeholder.
Review edits 3–4: code/runner.py:19 requires a standalone GO; code/metrics.py:70 licenses C64 only through context_pays_pose.
Review edit 5: code/test_kit.py:141 and subsequent regressions cover pose sign, lifting direction, decision persistence, missing geometry, held-out guards and dense remapping.
Optional review safeguards: code/runner.py:67 checks HALTED before admission and records NOT_ADMITTED; code/kbox_hook.py:18 requires the full reference row set.
Review disclosures: scripts/finalize_v3.py:86 identifies re-formatted responses; code/README.md records selector 32/31 divisors and unscaled raw depth AbsRel.
24 GB policy: code/runner.py:75 and code/vendor/geo_bakeoff/backends.py:143 reject smaller or pre-Ampere cards; both allocation fractions retain min(1,40e9/memory).
Runtime hash coverage: code/gpu_models.py:63 loads vendored geo_bakeoff; code_pins includes its backend.
All GPU parts are estimated to fit 24 GB Ampere: A 9–11 GB; B G3T 11–15 GB and sequential SAM 3 5–7 GB; C DA3 13–17 GB. H is CPU only.
Estimate source: `sed -n '/## 24 GB cards/,$p' work/REVIEW_VERDICT_sb_ktrev2.md`. B/C assume fused attention; actual peaks require the first GPU capture.
Exclusions: code/exclusions.py:7 uses pinned R0 bdb5d402, withheld-80 634820b4, dev-S1 969cdb56, BENCH v2 3119aa4a and K1 held-out 4d4736cf.
code/test_kit.py:286 plants a row for each list; code/test_kit.py:299 proves excluded rows cannot flip a decision.
`bash scripts/cpu.sh code/exclusions.py` produced out/EXCLUSIONS.json: 1,012 decision rows, 1,037 report rows, 25 excluded rows in five priced captures; all six affected captures are excluded from pose decisions.
The excluded captures are scannet/scene0201_02, scene0478_00, scene0478_01, scene0614_02, scene0692_03 and scene0255_01; the last has no distance rows.
Freeze rule: code/process_guard.py:41 writes parts/<part>/BARS.json first and records its SHA256 in FREEZE.json; code/runner.py:81 precedes A/B/C preflight; scripts/run_H.sh:4 freezes H before its look.
Scoring guard: code/process_guard.py:31 rejects existing per-item files, missing bars/receipts, changed bars hashes and changed code; A/B/H and camera parity/scoring call it before output.
code/test_kit.py:330 through the altered-bars test exercise all four parts: 12 subprocess cases exit non-zero with byte-identical output trees.
`bash scripts/cpu.sh code/test_kit.py > out/tests_fix2.log 2>&1`: 42/42 PASS; freeze ordering, resume integrity, legacy scores and part isolation also pass.
`bash scripts/cpu.sh code/dryrun.py > out/dryrun_fix2.log 2>&1`: PASS; 296 captures, 9472 numbering hashes, 450 camera records.
`bash scripts/cpu.sh work/a0_rerun.py > out/a0_fix2.log 2>&1`: 1,037/1,037 A0 rows and 209/209 capture row sets match; the eligible subset matches 1,012/1,012 rows and 204/204 capture row sets.
A0 checks predictions, re-formatted responses, member frames and boxes; out/fix_validation/a0_rerun_summary.json records both populations and input hashes.
`bash scripts/cpu.sh scripts/finalize_v3.py > out/finalize_fix2.log 2>&1` binds the passing dry run and code in out/CODE_SHA256.json and GPU_NEED.json.
Code SHA256 for the GO: `39b253c268e69d3ad71621336928e6446871e5483ed4283453d5e8e9f1ea401e`.
`bash scripts/cpu.sh work/refresh_stage.py > out/stage_fix2.log 2>&1` verifies the saved stage_list.py inventory and updates changed kit bytes/hashes; external hashes and trace checks are reused.

| Part | Staged bytes | GB (decimal) | Smallest listed staging set |
|---|---:|---:|---|
| A | 22,244,325,728 | 22.244326 | A-tagged TSV rows: Python, G3T, K1 frames/caches/GT and kit |
| B | 26,019,184,648 | 26.019185 | B-tagged rows: Python, G3T, SAM 3, K1 frames/caches/GT and kit; A outputs also required |
| C | 21,175,476,440 | 21.175476 | C-tagged rows: Python, G3T, DA3, dev-S1 frames/records and kit |
| H | 824,834,632 | 0.824835 | H-tagged incremental rows; requires the A/B installation and outputs |
| union | 33,995,423,070 | 33.995423 | All unique TSV paths |

The parts column of out/STAGE_LIST.tsv defines each set; directory manifests bind its files. B needs A outputs for the joint gain; transfer them if parts use different nodes.
MISSING: /scratch/jjyeung/orch_n30/sb_kbox2/heldout_labels.json. No held-out look was consumed. Part C dense-input gaps remain named in out/BLOCKERS.json.
GPU launches require GPU_GO.json bound to this hash, SHARED_GPU_RESERVATION.json and, for C, DA3_GO.txt. Actual GPU performance remains unmeasured.
`bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh scripts/run_H.sh` passes.
`bash scripts/cpu.sh work/package_fix2.py` writes this report and out/sb_ktfix2.tar; `sha256sum -c out/sb_ktfix2.tar.sha256` verifies the archive.
`bash scripts/cpu.sh work/verify_fix2.py` verifies code/test/dry-run agreement, staging manifests, both A0 populations and every archive member.
Every result JSON records input hashes. The package verifies all archived members against out/FIX2_MEMBERS.json. Writing skills: no-archaeology and summary; no borderline history sentences retained.
