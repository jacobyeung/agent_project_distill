The pinned discovery kit is `X/qp_11386117`, with seal `1138611744d623dce116a7a104a5682ae7a6e889e3155059a92d20adc364ba83` (PIN_24M4Z8.md: `ee8c749b72ed21d3f1e20b8592cb14d9a171b3280b907b2220b0aea96407a608`). Its Python files are byte-identical to reviewed `kit_qd`, seal `8ae781f4cd655a53108b8b0966ecb3a41a5679b19e70d4ddadb472a88bae2784`. The helper copies source bytes directly and enforces the exact allowed difference; it has no token-escaping operation or token-absence assertion.

The full-file comparison differs in exactly `BUILD.json`, `SHA256SUMS.txt`, `k/a.json`, `k/h.json`, `k/p.json`, and `k/r.json`. It has no added or removed files and no mode changes. `work/build24m4z8b/FULL_FILE_DIFF.json` lists both hashes for every member. `work/build24m4z8b/AUDIT.json` verifies 2099 protected files and the unchanged arming helper `1a4b900b7153e540e3674d1ccb98c2c8bd75be3b2ac61ccd1edb17a0ad1a6a13`. `GO=false` remains sealed.

Both delivered shells select `qp_11386117`; `j7.py` reads the seal from the kit at runtime and retains its bytes. `UPLOADS_24M4Z8B.json/.list` lists exactly 51 files totaling 5,851,681 bytes, each below 5 MB (`work/build24m4z8b/UPLOAD_AUDIT.json`). `UPLOADS_24M4Z8.json/.list` mirrors the new manifest for existing consumers.

All checks below ran on the new bytes. Paths are relative to this workspace.

| Check | Result and evidence |
|---|---|
| Pin reproducibility and three authentication negatives | OK; `work/build24m4z8b/PIN_TESTS.json` |
| Full-file and protected-file hash audit | OK; `work/build24m4z8b/FULL_FILE_DIFF.json`, `work/build24m4z8b/AUDIT.json` |
| Real unpinned planner | Expected `R1_ROUTING_SELECTION_PIN_MISSING`; `work/build24m4z8b/qd_plan.log` |
| Real pinned planner | Selection authenticates; stops at `E10:/project/community/jjyeung/okh7/h_6ed2c7aa/m400/s.tar`, unavailable offline; `work/build24m4z8b/qdp_plan.log` |
| Training refusal | Expected `E03`; `work/build24m4z8b/training_refused.log` |
| Discovery shell | OK; `work/build24m4z8b/JD_SHELL.json`, `work/build24m4z8b/JD_SHELL.log` |
| CPU planner shell | OK; `work/build24m4z8b/PP_SHELL.json`, `work/build24m4z8b/PP_SHELL.log` |
| Wrapper checks | OK; `work/build24m4z8b/WRAPPER_TESTS.json` |
| `qd_tests` | OK; `work/build24m4z8b/qd_tests_1795218845017402970.log` |
| `planner_tests` | OK; `work/build24m4z8b/planner_tests_1795218848502985351.log` |
| `scans` | OK; `work/build24m4z8b/scans_1795218850361012058.log` |
| `naming_tests` | OK; `work/build24m4z8b/naming_tests_1795218883117308177.log` |
| `guard_q_new` | OK; `work/build24m4z8b/guard_q_new_1795219106940702394.log` |
| `guard_q_legacy` | OK; `work/build24m4z8b/guard_q_legacy_1795219107061392757.log` |
| `guard_n_new` | OK; `work/build24m4z8b/guard_n_new_1795219107157932985.log` |
| `guard_n_legacy` | OK; `work/build24m4z8b/guard_n_legacy_1795219107275613732.log` |
| `arm_tests` | OK; `work/build24m4z8b/arm_tests_1795218927468975359.log` |
| `arm_missing_test` | OK; `work/build24m4z8b/arm_missing_test_1795218953919243708.log` |
| `native_arm_tests` | OK; `work/build24m4z8b/native_arm_tests_1795219107372737946.log` |
| `review_tests` | OK; `work/build24m4z8b/review_tests_1795218984142116054.log` |
| `coverage_tests` | OK; `work/build24m4z8b/coverage_tests_1795218984448012437.log` |
| `arm_negatives` | OK; `work/build24m4z8b/arm_negatives_1795219057752006583.log` |

The shell tests retain the scoped fixtures described in their JSON reports; they do not establish a production run. `work/build24m4z8b/VALIDATION.json` records all 14 suite groups and six focused checks. `FAILURES.json` retains setup shell-quoting and evidence-path errors, four missing guard-report-directory errors, one missing seal-index error, and a filesystem audit invoked under test virtualization with their full output; the corrected guard, native arming, and direct filesystem audit reruns succeed. Synthetic review verdicts stay in memory, with base64 backing state; the actual unchanged helper still refuses the authorization message at its independent verdict gate. No launch verdict was produced. The package audit found inherited `work/build24m4y2/before/timings.json` matched the verdict gate. Its bytes are preserved losslessly as `.json.gz` and in `attic/`, with the raw file absent (`work/build24m4z8b/VERDICT_SURFACE.json`). The failure output is in `work/build24m4z8b/FAILURES.json`.

For n_review1g: verify `SHA256SUMS.txt` hashes to `1138611744d623dce116a7a104a5682ae7a6e889e3155059a92d20adc364ba83` and authenticate every listed member. Compare the entire kit against reviewed qd and require exactly the six differences above, including byte-identical Python. Decode and authenticate `k/a.json`; `discovery_pin` must contain selection `a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73`, compact receipt digest `522a3be39b90d6fd8ec4dd599d89e1d5762c3a1a150e198c0c0bbb70f931ba39`, and database `5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df`, plus base `4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84`, selection receipt `74640a29f939ce2aac8ce13683574078a09f3d02e89bbbe07653dda70ef49576`, and authorization `f9bdaf0ba8b84606d007cbfb5113cf470718fe2ce89a554af42c5ed8b8a50f6f`. Decode `k/h.json` and `k/r.json`; both must point to `u/a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73`. Hash that object, authenticate its native receipt, recompute its compact digest, and confirm its database pin. Require the second job's `j7.json.kit_sha256` to equal `1138611744d623dce116a7a104a5682ae7a6e889e3155059a92d20adc364ba83`; inspect its host digest, prepared receipts, population, reader filters, and first-batch files before judging (d) or P1. The independent launch verdict gate remains required.
