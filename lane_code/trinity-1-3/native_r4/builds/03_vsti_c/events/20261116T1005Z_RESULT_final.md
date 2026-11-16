RESULT: V1c built and CPU-verified; no job submitted. Evidence: out/FINAL_RESULT.json.
V1b archive and family hashes remain unchanged: out/REFRESH.json; work/finalize_c.py.
F1: strict parser/official metrics; kit matches all 900 rows, primaries 66.95/68.71: out/SCORER_CHECK.json; tests/test_v1c.py.
F1 forms: 146/148 distance and 34/36 room tagged answers checked; zero mismatches: out/HISTORICAL_FORMS.json.
F2: shared project packet, /dev/null batch output, no foreign /tmp in a.sh; test_f2_shared_packet: out/TESTS.json.
F3: staged bwrap; explicit host fallback only for Trinity; test_f3_s1_staged_namespace: out/TESTS.json.
S1: allocation CUDA value passes through; test_f3_s1_staged_namespace: out/TESTS.json.
S2: proof exceptions become failed receipts and read continues; test_s2_proof_failure_continues: out/TESTS.json.
S3: refused parity positions excluded with reasons; test_s3_parity_refusal_exclusion: out/PARITY_POLICY_CPU.json.
S4: dependent camera items auto-zero; others decode with all calls refused; test_s4_geometry_scope: out/GEOMETRY_SCOPE_CPU.json.
S5: incomplete rows have no score/interval; test_s5_complete_and_incomplete_types: out/TESTS.json.
S6: headline names refused subtasks/counts and proof status; test_s4_geometry_scope: out/GEOMETRY_SCOPE_CPU.json.
S7: distinct item cutoff/kill, 600-second reserve and earlier cap handling; test_s7_distinct_deadlines: out/TESTS.json.
S8: full frame-count assertion and index comparison tests pass: out/TESTS.json; code/pixels.py; code/indices.py.
S8 pending: own selected-frame list absent; 311-scene command: out/FRAME_CHECKS.md; out/INDEX_CHECK.json.
Release pixels: full counts pass; 0/160 selected frames byte-identical: out/RELEASE_CHECK.json.
Refusal wording is the runtime's recoverable error format (trace 3.13): out/LEGALITY.md; REPORT.md.
Tests: 53 kit + 30 inherited pass; unexecuted inherited tests have reasons: out/TESTS.json.
CPU job path: 9 sample items, 2 scenes, synthetic tower/heads/logits; passed: work/cli_sealed/RESULT.json.
Full adaptation: 311 scenes, 9,952 PNG SHA checks, 450 items and fixed canary; passed: out/FULL_ADAPT.json.
Namespace denied by sandbox; operator command: out/rehearsal/RUNBOOK.md; out/rehearsal/NAMESPACE.json.
Unexplained authored reachable lines: 0; inherited: 318: out/UNEXECUTED.json.
Unexecuted classes: {"GPU decode": 209, "UNEXPLAINED": 318, "error branch (with condition)": 402, "venue staging (Trinity or Orchard)": 579}: out/UNEXECUTED.json.
Code SHA256 dc40cf60212a34c2789a9821bb558e0592074c4d81b0bb1239e55c238f093eaa: out/c.tar; out/PACKAGE_VERIFY.json.
Reference SHA256 9a1de8608ea0e75e2f2436259b81f0e991b2007002a59de11d85062e8384d08f: out/d.tar; out/PACKAGE_VERIFY.json.
Family SHA256 3cf68794ee715bdad6936486ce64edc72c40b08165f9e0763c126aaa685eecf6: out/FAMILY.json; out/PACKAGE.json.
Diff V1b +189/-61; C8r +1824/-18: out/DIFF_STATS.json.
Options/defaults and operator commands: out/DECISIONS.md; out/RUN_ORCHARD.md; out/RUN_TRINITY.md; out/SIZING.md.
GPU proof/decoding, actual Orchard namespace, transfers and return timing were not checked: out/FINAL_RESULT.json.
No network, SSH, Git, GPU, agent delegation, external write or submission ran.
