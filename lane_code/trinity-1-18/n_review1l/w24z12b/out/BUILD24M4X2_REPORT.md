24m4x2 passes local validation; full production SQL/runtime replay remains unavailable. GO=false except kit_n_go.
F1 restores both intake expressions; F2 emits the compose counter only with a list; F3 gates every row carrying r1_source. Tree 9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b.
TREE_CHANGE_24M4X.patch changes only extent_receipt.py, carrier_c1_run.py and the conditional r1_routing.py key versus C″; fuzz-free check and apply_24m4x.py replay on verified 24m4u seals pass.
Fail-before: work/build24m4x2/FAIL_BEFORE.log records nd.py:318 ValueError: E96:tree on 7a8022ad; 173796/nd.json /reason has the same traceback. The supplied job.log has zero exact E96:tree hits.
nd.py TREE and ch.py TREE pin the new seal as constants, independently authenticating kit tree bytes; f.json tree_sha256 and nd.py FIELDS are refreshed. native_rules passes with all 13 removal files.
PIN_AUDIT.json covers 193 helper/kit files: 7,677 C″ file-pin occurrences remain valid because those bytes are unchanged; no old whole-tree pin remains there. Local scanner seals and their arming entrypoint are refreshed.
chain.json publishes $.refused_rows, $.extent_exempted_rows and $.extent_still_checked_rows (173796 used $.streams.routing). Exact no-list refusal comparison and extra/missing-exemption tests yield publisher exits 0/1/1.
Kit q df93cfba9769ca82f48ac3bfdbb117ffc2d06b6f694ed1694c23d815fa97e2a9; n 797255ae1421d27f6c65bb9fc0038da1f345f446e1e1d41c90ba1bdf8f2338f7.
Kit n_go aa2d1267065d920db23dc3e6aa5f41c87b87d57b2cf27f12af82255a786c97ea; qd 8ae781f4cd655a53108b8b0966ecb3a41a5679b19e70d4ddadb472a88bae2784. RCJ_FILES_24M4X2.sha256 seals every helper.
All 39 rcj/kit/scan/naming/resolver/guard/arming/qd/planner/publication suite groups pass (138 unittest cases); 18 targeted tests, 3 real-row controls and the 80-row chain pass: 14 exempted, 66 checked, 0 refused.
Q2: four no-list compose/intake byte comparisons pass. Q5: 17 files, 157 cases per tree; both have 140 passes, 7 skips and the same 10 missing-fixture/import errors. FAILURES.json retains every setup failure and test output.
Offline nd.publish uses exact published SQL samples (10 P/7 N) with a test-only P-hash substitution; native_rules/publish_types run unchanged. Only seal fields differ from C″; full type-table replay and 3,924,609-byte real-artifact publication pass.
UPLOADS_24M4X2.json/.list replay exactly against reviewed q e7ac0727, n a7809da0, qd 221d1782 and all 8 helper pins: 38 files, 10531875 bytes; 11 optional GO files are separate. c072905b stays 12,061,474 bytes.
The package preserves inherited workspace members, includes the evidence and failures, verifies every archived byte/mode/link, and writes its checksum last.
