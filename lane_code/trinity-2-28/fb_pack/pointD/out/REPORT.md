The Locate overlay is implemented and tested against base+PATCH_A. Full real-mask rebuilding remains MISSING because the required mask and RGB assets are not staged locally.

`PATCH_POINT.patch` changes 5 files and applies with zero fuzz; all 942 replayed source files match. `FILES_TOUCHED.json` lists before/after hashes.
The sealed base is `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7`; base+PATCH_A is `290e2119232da4eb3d55df805e069b4a2d9f5e167368db30d2ef2e013ee6e0f9`.
The sole protected-file overlap is `student_pilot/carrier_c1_run.py` (donor). Prior2 and camform have no overlap. Merge the runner's narrow config/receipt/weighting hunks with donor changes.

Set this top-level config field in tree_rebuild14:
`"pointing_locate": {"rule_id": "pointing-locate-v1", "sha256": "5cf88c67b7fce075cfba754e5bad6e895dca6621c251f10d2f2d7aaf098d2c20"}`
The SHA256 binds the canonical rule specification in `student_pilot/pointing_locate.py`; the specification also pins fbp_point's reference transform SHA256.
Keep final-mode `pointing_weights={"decision":5,"row_mean":2}`. Absent `pointing_locate` preserves base store bytes. Unknown rule pins and explicit null config values fail validation.
After `mask_target`, visible targets contain exactly `Locate the <label> in frame k.`; null targets contain exactly `Locate the <label> in frame k: it is not visible in that frame.`
Each target wraps that one line in `<think>\n...\n</think>\n\n` and appends the unchanged JSON answer. Exact labels, including their digits, remain intact; the trace adds no coordinates.
Native stream receipts record the rule id and SHA256. Preparation authenticates the database and checks every target against the rule. Prepared/config rule mismatches fail closed.
The weighted decision is the token containing the period or colon immediately after the frame index, including merged frame/punctuation tokens. The parser accepts the native training boundary with the opening think token masked in the prompt. Supervised weights retain mean 2 and decision/ordinary ratio 5.

`bash code/run.sh setup` verifies all 939 base files and applies PATCH_A.
`bash code/run.sh compare` checks all 25,020 real stored rows: 16,262 visible and 8,758 null targets match fbp_point's delivered store exactly; all 25,020 answer byte strings are unchanged.
That command also checks every real row's decision position with a character tokenizer. `COMPARE.json` records the selected visible/null tokens and normalized weights.
`bash code/run.sh boundary_probe` passes four cases through native `training_text`: visible/null targets with the opening think token either supervised or masked in the prompt. The weighted tokens are `.` and `:` in both cases; the chat template and tokenizer are synthetic fixtures.
`bash code/run.sh compare` also runs native `build_stream` on four synthetic fixture rows, or three after shape filtering. Base/new SQLite SHA256s match with the field absent, including a `source_receipt=True` rebuild. Enabled fixture targets match the reference transform and preserve mask answers.
`bash code/run.sh admission_probe` exercises N's actual `admit(prepare_only=True)` prepare closure through the native pointing build, retaining three fixture rows with target filtering and scene exclusions.
The probe stubs unrelated source/model admission authorities and stops after the pointing build. It does not claim full N launch admission.
`bash code/run.sh run_tests final focused_final tests.test_pointing_locate tests.test_carrier_c1_data tests.test_s1_admission tests.test_s1_target_filter tests.test_carrier_c1_t0.PointingDecisionWeight` passes 23 tests.
Those tests include actual `carrier_c1_run.prepare` receipt gates and `Rows.get` shifted loss weights. Dropping either the target-filter receipt or Locate pin is rejected.
`bash code/run.sh run_tests base full_base full`: 1941 tests, 18 failures, 473 errors, 145 skips.
`bash code/run.sh run_tests final full_final full`: 1951 tests, 18 failures, 473 errors, 145 skips.
The new run adds no failing test or subtest. Both use the same restricted CPU harness. `BASE_FAILURES.json` retains every failure and traceback; these are not clean full-suite passes.
The comparison normalizes only randomized production-import fixture paths, retaining the separate `empty` and `kit` subtests and verifying their identical blocked-subprocess exceptions.
`bash code/run.sh package` produces the patch, verifies every replayed file, compares suite outcomes and packages the delivery. All evidence JSONs bind their input hashes.

MISSING: a full or real-row sample through `build_stream`; the first GT-mask input is `/data2/p5x9/d1/v002f7d9ced14/f18.npz` (SHA256 `8dd7035cd867e7ec6a0107d39d01e7d1e1bbb3be13ae9657b89b06c2778fe499`).
MISSING: its source's first RGB input, `/data2/k6tk/f2/f25faedce4622416aed654d13ed347ed2a3b1ea0928a5674a80169324c6888cc.png`. No matching local basename was found in the named K1 frames/ext copies; no mapping was invented and NFS was not read.
The pinned division was found locally and hash-verified. Real-store comparisons reuse stored mask answers; they do not re-prove masks, filtering or scene admission.
MISSING: a production tokenizer path. Decision tests use character, separate-punctuation and merged-token fixtures; no production-tokenizer encoding is claimed.
The prompt's `point/out/code/pointing_locate.py` is MISSING; the supplied implementation is `point/code/pointing_locate.py`, SHA256 `20e6bac0646697300e79322653fe1cf0291e10f0498105bc89cb388463412b27`.

Tree_rebuild14 must apply PATCH_A, merge this overlay with donor changes, set the rule field before admission, stage genuine masks/RGB, and rebuild pointing with the existing removal, shape and scene filters.
Pin the resulting stream receipt and database; do not assume the target-only derivative's `d5362229...` database hash for a newly filtered native rebuild. Preserve the 32-pointing-rows-per-step quota.
Refresh `r1_training.store_hashes.pointing` via the native handover binding, plus changed content membership and scene-source pins; rebuild the `r2_sampling` population and set `r1_training.row_plan_sha256=digest(cfg['r2_sampling'])`.
`launch_r1/entry.py:85-88` requires that sampler and row-plan binding. The new field and rebuilt pins change `carrier_c1_run.identity(cfg)`.
`launch_r1/entry.py:89-94` requires a fresh PASS host receipt whose `config_identity` matches and whose `loader_audit.complete` is true, with all required assertions.
`launch_r1/entry.py:90,103-104` requires a fresh independent PASS review bound to the same final config identity. Neither gate is satisfied by this CPU delivery.
Rebind continuation/handover identities where used, regenerate preparation/admission receipts, refresh the source closure and tree seal, and reseal the launch/staging inventory after merging all lanes.
Open decision (review MUST 2): `evalpath/pointing_markers.py:164-166` still pre-fills an empty think block. The orchestrator must decide whether evaluation should generate Locate or use an explicit answer-only protocol. Evaluation is unchanged.

The archive is `out/fbp_pointD.tar`; `out/fbp_pointD.tar.sha256` binds its bytes. It contains patch, reports, logs and reproducibility scripts, not the real databases or test fixtures.
No Git, network, SSH, GPUs, process termination, tmux operation, deletion, or other-lane writes were used. No revision-history prose required an exception.
