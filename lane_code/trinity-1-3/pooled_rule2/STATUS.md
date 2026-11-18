# STATUS lane pooled_rule2 (Devin Opus high, trinity-1-3), started 2026-11-18T03:08Z, finished 03:36Z; lane exits after the RESULT event
Task: apply the review's six binding fixes to the pooled harm rule. Done; v2 is ready to register.

## Deliverables (events/pooled_rule/)
- POOLED_RULE_REGISTRATION_v2.md (478e9836), pooled_harm_rule_v2.py (4b6e3280), build_manifest.py (699cacd7), ROOM_CROSSWALK.json (994902af) and build_crosswalk.py, SIZE_UNITS_DEV_S1.json (2a0d756b) and build_size_units.py, BASE_MANIFEST_dev-S1_544.json (e08a1d34), BASE_MANIFEST_R0-dev_544.json (86c8f993), PROVENANCE_SCHEMA.md, test_pooled_rule_v2.py + TEST_OUTPUT.txt (26 tests OK), sim_exec.py, sim_exec_merge.py, SIM_EXEC_AGREEMENT.{json,txt}, pooled_rule2_COMPLIANCE.md, pooled_rule2_evidence.tgz (9f368f805c6d67c54ab74f45464fab356570851c7ed6476d17ba54633d1a5f6b; lane copy out/).
- Record distill_design/POOLED_HARM_RULE_R1_20261118.md updated in place; INDEX.md line 233 rewritten.

## Results
- Crosswalk: 72 dev-S1 rooms (ScanNet 14, ScanNet++ 27, ARKit venues 31) and 98 R0-dev ScanNet++ rooms; labels and physical rooms are bijections, no shared room, no dev-S1 room on R0 list. Clustering and room order unchanged, so v2 reproduces v1 exactly on D0 m200, D0 m100, H1-1 m100 at both levels.
- Executable-path simulation: 4,000 null + 2 x 1,000 loss pseudo-reads agree with pr_sim.py within one combined MC se; no rejected draw.
- Tests run from work/ (they read work/manifests/ and cont_ops receipts on trinity-1-3): `cd work && python3 -W ignore -m unittest -v test_pooled_rule_v2`.

## Open, for the orchestrator
- Ruling points: the manifest's run block also holds the read job, token and plan hash (the kit's plan hashes the export); the type filter may differ (dev-S1 baseline unfiltered, R1 `direct`) through the rule population. Both are stated in the registration.
- No independent review of the v2 fixes yet.
- rm_guard queued one command of this lane in agent_project/agent/PENDING_USER_COMMANDS.md (a heredoc that wrote an older sim_exec.py, matched "(rm" in a variable name). It deletes nothing; do not run it, it would overwrite work/sim_exec.py.
- No IB mirror: every deliverable and the evidence archive are on /data2 (events/pooled_rule/); the baselines and receipts the tool reads stay in lane cont_ops's folder on trinity-1-3.
