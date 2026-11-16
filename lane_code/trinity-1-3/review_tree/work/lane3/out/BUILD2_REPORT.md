# Build 2 report

The tree implements the shared grammar adapter, component and bank policy, shared-room withholding, metadata-first repeat checks, native type sampling and connector configurations. The bounded kits stage and verify, but they are inspection kits: the job entry stops after verification. Deployable-kit integration remains incomplete.

The combined suite ran 83 tests with 0 failures, 0 errors and 0 skips (`out/B2_FINAL_TEST_RESULTS.json`). The focused closing suite ran 3 tests with 0 failures and 0 errors (`out/B2_CLOSING_TEST_RESULTS.json`). The portable integration suite ran 11 tests with 0 failures and 0 errors (`out/B2_INTEGRATION_TEST_RESULTS.json`). The final native-config and kit-staging suite ran 3 tests with 0 failures and 0 errors (`out/B2_CONFIG_TEST_RESULTS.json`). The final fallback proof ran 1 test with 0 failures and 0 errors (`out/B2_FALLBACK_TEST_RESULTS.json`).

| Delivered behavior | Evidence |
|---|---|
| The shared grammar retains the supplied bytes; the native wrapper preserves masking and additional refusals. | `work/tree_r1/student_pilot/r2_grammar.py`; `out/GRAMMAR_RULES.json`; `out/GRAMMAR_DIVERGENCE.md` |
| Evidence is required by component and phase. Training skips evaluation-only choices; missing training records refuse. | `out/COMPONENT_POLICY.md`; `out/COMPONENT_SLOTS.json`; `out/RECORDS_TO_REGENERATE.md`; `work/tree_r1/tests/test_r2_policy.py` |
| The builder transports regenerated evidence, filtered counts and final-reader indices with all nested pins. The real portable producer and reader pass the synthetic proof. | `work/tree_r1/launch_r2/closure.py`; `work/tree_r1/tests/test_r2_portable.py`; `out/B2_INTEGRATION_TEST_RESULTS.json` |
| The bank gateway reads actual items, binds their content and reader hash, ignores caller labels, restricts lineage claims and requires both venue scores. The deployed selector refuses the fitted-on banks and training responses. | `work/tree_r1/student_pilot/r2_policy.py`; `work/tree_r1/student_pilot/r2_grammar.py` |
| The intake and native reader reject withheld room names and capture aliases, including exclusion-list tokens. Intake reports withheld rows per family. | `work/tree_r1/student_pilot/r2_intake.py`; `work/tree_r1/student_pilot/r2_contract.py`; `work/tree_r1/tests/test_r2_policy.py` |
| Repeat checks reconcile complete filtered metadata receipts before materialization. The native sampler enforces the per-type table and keeps facing twins together. | `out/MIX_A0.json`; `out/MIX_A0.md`; `out/B2_SAMPLER_PROOF.json`; `work/tree_r1/student_pilot/r2_mix.py` |
| Native fusion omits the camera connector. The adapter-only stage freezes the language model; the full stage preserves native optimizer groups. | `work/tree_r1/student_pilot/carrier_c1.py`; `out/B2_MODEL_PROOF.json` |

The native trainer validator accepts the configured arms, fusion stages and fallback quotas. Configurations omit the MDG key, derive explicit stream budgets, trim milestones to each stage and regenerate the recipe and checkpoint budget. The kit also binds the changed route table rather than retaining the parent route pin (`work/tree_r1/student_pilot/r2_config.py`; `work/tree_r1/tests/test_r2_native_config.py`).

The shared-room file SHA256 is `634820b44927b1a50c18db9b90246b4b99f8954b0d7f5f2893e547f1c92879ed`. Its sorted-room digest is `e4b0de9663e853faf9de23bc980bd42e1592e5f9cd8365b836aa48ac9fb5fb68`, which differs from the lost digest `bf737b729a8f9414f400a639d33e997242f1788353ccab5e0c4e1f0fdb12e09f`. This mismatch is reported without changing the draw (`out/WITHHELD_BINDING.json`; `work/shared/WITHHELD_ROOMS_80.json`).

The mix table follows the plan and the D0 ruling. Route planning enters VQA; routing carries programs and simulated misses. The stream quotas, registered duration and fallback are in `out/MIX_A0.json` and `out/MIX_FALLBACK.json`. The printed table in `out/MIX_A0.md` uses plan populations and labels its repeat arithmetic provisional. Real post-filter counts remain unavailable. Both sealed pose sources are pinned from the parent staging list; the named Orchard inventory confirms the second source and frame-store presence (`out/POSE_SOURCE_BINDINGS.json`). No store was opened here.

The CPU producer proof runs native intake, materialization, membership reads, RGB loading and encoders. It uses synthetic RGB, a lossless tiny tokenizer/processor and randomly initialized tiny native model weights at the unavailable pretrained/GPU boundary (`out/CPU_PATH_PROOF.json`; `out/FAMILY_ENCODER_PROOF.json`). The connector proof runs the real CarrierC1 and GF-1 code with tiny native language/vision models and a tiny native frozen tower. Its parity fixture disables the depth branch; the retained build-one proof exercises native depth. It checks exact parent logits, reload equality, finite loss and stage trainable sets (`out/B2_MODEL_PROOF.json`). No pretrained export, GPU behavior or real visual labels were checked.

| Configuration | Staged bytes | Temporary bytes before / after | Kit SHA256 | Source |
|---|---:|---:|---|---|
| none | 19949707 | 191994146 / 191994146 | `cabab438f900af64eff11006771e67887ae61c19d84b3d394fa722b13945cedf` | `out/B2_KITS.json`; `work/build2/kits/b0b0b0b0` |
| gf1 | 19951768 | 191994146 / 191994146 | `ab66794e405d7f7459b3233df76d7408cde3dcda696858811d36837cdf662787` | `out/B2_KITS.json`; `work/build2/kits/b2b2b2b2` |

The final kit measurement counts all files after staging. The per-test harness guards temporary size and retains fixtures (`work/build1/run_tests.py`). The combined test run ended with 159044885 temporary bytes and 257720346 lane bytes (`out/B2_FINAL_TEST_RESULTS.json`). The final staging suite ended with 191994146 temporary bytes and 370769640 lane bytes (`out/B2_CONFIG_TEST_RESULTS.json`). No individual write reached the large-write threshold in the user brief. No full store, GPU work, network access, Git operation, subagent or file deletion ran.

The kit builder reuses `launch_s1.build.tree_files` and the actual `launch_s1/b/a.py` verifier with its dependencies. The source base and launch machinery remain unchanged. The parent anonymity certificate explicitly waived naming rules on Orchard; this build applies the stricter requested rules (`work/kit07ca49df_meta/m/ANON_OK.json`; `out/FORBIDDEN_STRINGS.json`).

Differences from the parent kit:

- Bound metadata uses opaque content names. Original provenance bytes live in base64 capsules; operational references use relative opaque paths.
- Source members use opaque content files and a source registry instead of the parent native source archive. The host adapter needed to execute that representation is not implemented.
- The new closure includes policy slots, the shared room file, pre-registration, exclusion records, parent removal records, the mix and run identity.
- Optional evidence and sampling bindings travel with their dependencies; the closure records the original and transported hashes. Missing real inputs remain explicit.
- The init identity changes to the accepted export; exact parent resume refuses. The source and mix identities change with it.
- The route table makes room size and route planning direct. The sampler adds the bound per-type allocation.
- The connector field selects the control or fusion arm. The fusion staging proof carries a synthetic dense manifest, clearly labelled in `out/B2_KITS.json`.
- The site binding retains the parent Orchard allocation. The job name follows the requested opaque prefix. The job entry verifies bytes and exits; authorization modes are empty.

Changed-statement coverage is 2939/2944; production coverage is 1700/1705 (`out/B2_COVERAGE_CLASSIFIED.json`). Unexecuted production statements by class: CPU-only=0, model-loader=2, frame-host=3, GPU=0 (`out/B2_COVERAGE_CLASSIFIED.json`). Every remaining statement is listed with its source line. The standard-library tracer measures source statements intersecting the diff against the sealed base. Coverage from prior tests is retained only for unchanged lines mapped from authenticated source snapshots; focused tests cover the changed integration (`work/build1/run_tests.py`; `work/build2/merge_all.py`; `work/build2/merge_same.py`; `out/B2_COVERAGE_REMAP.json`). No CPU-reachable changed statement remains unexecuted.

Open decisions and defaults:

- Evidence schema: use the documented slots and refuse missing records. Some historical component filenames were not recovered; their reconstructed names are labelled GUESS in the policy table.
- Qualification rooms: follow the orchestrator default; they do not add an exclusion. Later probe reads must be labelled seen-in-training. The shared draw itself remains unchanged.
- Fusion duration: use the base adapter warm-up and the remaining registered budget for full fine-tuning. The derived schedule is 400 + 600 steps (`work/tree_r1/student_pilot/r2_config.py`; base `configs/gf1_stage1.json`; registered total in `out/MIX_A0.json`). This is a build default, not an experimental finding.
- Missing dense data: permit only a labelled CPU staging fixture. Real fusion admission must receive the actual dense manifest; the missing-manifest mutation refuses.
- Missing real counts: retain the plan table for review and refuse admission. The fallback requires a frame-host absence record; local absence cannot select it.

Unfinished integration and checks:

- The opaque source representation needs a native execution adapter and a production job entry. The builder supports evidence and sampling bindings, but the supplied kits contain missing evidence slots because the real records are unavailable.
- The JSON bank gateway is tested directly. Native inference and grounding-runtime entrypoints now refuse recognized restricted-lineage reads before loading weights; their legacy bank formats still need authenticated adapters. All evaluation/export entrypoints have not been audited.
- Real type indices, population receipts and dense manifests remain unavailable. The portable synthetic proof exercises their binding, but the supplied kits carry no synthetic population admission.
- The full model loader, real export identity bytes, actual dense manifests, real exclusion counts, full repository suite and Orchard staging were not exercised. The frame-host job and card belong to the next build.
- CPU-only coverage gaps, if listed above, remain build work; they are not represented as hardware-dependent.

The final tree seal is `cd82c5c40b30b9512b6ea9285ea682b6b7b08c9ebe24d922693c439408868254` (`out/TREE_SEAL.json`). The sealed base is unchanged. The unified changes and file hashes are `out/TREE.diff` and `out/TREE_FILES.sha256`.
