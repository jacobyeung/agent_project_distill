Cause: H1 changes milestones to [100,200] but retained D0’s nine-export disk plan; native admission requires three exports.
Changes: tools/derive_kit_h1.py:445,643 and payload/d.py:445,643 recompute the pinned checkpoint_space.plan with the old reserve; tools/make_deriver.py:14,18 generates it.
Validation: tools/build_packet.py:67,81 and tools/rebuild_fix6.py:16 run native validation in p1cpu; tests/test_admission_config.py:32 reproduces the exact old error and tests the derived config. Login derivation stays stdlib-only.
Fresh targets: x_3fdda0fb and r/39504485 avoid the old KH and the failed job’s persistent claim; native tests reproduce cold-restart refusal on an already claimed root.
| Audit check | Run | Result |
|---|---|---|
| Native validate, H1/faithful, layout, recipe, route policy/table, exclusions/removals | yes | PASS |
| b/w tree, authorize(p), input shapes, contract, source authentication | yes | PASS; identical local pinned bytes |
| capped_steps / wall / stop / full states / session names | yes | 29 only for pose-only; 86400 required; 13h allocation + USR1; stop 200; 14+2 states; 44 names PASS |
| admit(prepare_only) | partial | Config/authentication/request pass; missing production pose receipt blocks parent preparation |
| Routing selection implementation | yes | BLOCKED: native “Routing selection belongs to another implementation”; seven D0 closure entries differ |
| milestone_gate / full data preparation / effective / GPU pre-step | no | gate_stop=false and stop<400; production data/model/GPU unavailable |
Blocker: do not relabel the selection hashes. Regenerate or verify selection with H1 and real inputs; changed accepted rows would change training semantics. REPORT.md lists all seven entries and exact coverage.
Tests: 16 regression scripts PASS; admission assertions PASS (including both reproduced refusals); deterministic package/fixture/stdlib planner and guarded patch PASS. Four-rank harness syntax only; runner and chain_r1 unchanged.
Identity: 40d8d70da5f9de29a722a6146612475c224ce735370a2fea1868b351688880a4; PENDING-review config key: 4aa7c6fc. Final review changes the filename; resolving selection changes identity again.
Contract: 9a5270923627a9fae982acf90ac20ee4b695ac1932b98ae13038b63710a03ff9 (unchanged); run_key 17c4ffa4 unchanged.
Deriver SHA256: edb4af2c398b7b3af93ff7638565c55d561c60742f2c6c9658bc631284320a7a; all 12 changed member hashes: evidence/fix6_patch_manifest.json and DIFF.md.
sums.txt SHA256: 0fe8910ad45caa6223cbecb12beb630264e9758934ec6e9fd2bc7355ccbe1aa7.
Upload SHA256: 7106ad9463ebaa0904cdddd2a53f4ceba278d803b4fee16c8792d8ff4aee8eaf; orch_h1.sh SHA256: a0c487512e53e2c96f3dd3e9b0c1505b4dda3d84fec8c34dd822c202ce878def.
Patch: build/c_patch.sh (137584 bytes), SHA256 edb60e51d96c794ad912ce1ff3c199a31dc8f18c251918652a995a33ef9a858f; retains all old bytes/evidence in v_6; old KH untouched.
Orchard: STOP until selection is verified and bindings rebuilt; then patch → o.sh prepare/reproduction/stage → g.sh → fresh review.json → z.sh derive → anon scan + z.sh certify → fresh go.json → s.sh.
EXPORT_OBJECTS.txt is unchanged; unused create-only sessions still match all names and may be copied privately to new KH (verify expiry/unused status). No full trainer re-upload is needed.
Exact audit/results: REPORT.md and evidence/fix6_admission/results.json. No Orchard/SSH/network/GPU/Git/deletion; all changes stayed in this workspace.
