# Patch layout and verification

Apply both unified diffs with patch -p1 at a writable root corresponding to the input mirror. Patch 01 adds the packaging command, probes, regression tests and operator documents. Patch 02 adds pack_token.py and test_pack_token.py beside the native r10 and D builders. Neither patch changes a native source file or embedded script.

TOOL_SHA256.json names the canonical files. PATCH_VERIFIED.json records a fresh application, exact file equality, input-source hashes and test-log hashes. REPORT.md and TEST_RUNS.json contain exact commands, outputs and results. out_round1 preserves the reviewed deliverables. The current tested copy is work/r2/applied; final patch replay uses work/r2/applied_final. Runtime sources in both copies and the top-level delivery must be byte-identical.

Run test_pack.py, test_native.py, test_review.py and test_review2.py under the specified CPU Python with -I -s -B. Pass the native RESULT.json to test_review.py as PACK_NATIVE_RESULT. The additive adapter tests and login probes use /usr/bin/python3 3.6.8. Tests use fresh output directories, CPU only, nice -n 10, eight thread/core limits and the dispatch environment; REPORT.md records the complete commands. Production paths in tests are redirected or stubbed; no SSH or Slurm call runs.

Production actions require --enable. The token adapter requires --enable-token; wrapper normalization requires normalize_wrapper=true; structural fill requires fill_mode=structural. All default OFF or retain the mirror path. Native D delivery equality is measured under fixed entropy; r10 source identity is checked but a full r10 build lacks inputs. The D scorer mismatch remains a source-release refusal.

check requires export_binding_pin for a delivered plan without part pins, dependency_reference in structural mode and native_dry for the unchanged resolver. These are explicit SHA-pinned inputs. place requires a token reservation in the Trinity ledger. INFO limitations and missing inputs remain documented; no production certification is implied by passing fixture tests.
