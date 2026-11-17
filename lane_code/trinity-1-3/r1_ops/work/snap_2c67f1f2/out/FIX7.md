The routing absolute-distance census reads `routing.canonical` first, then nested and top-level provenance fallbacks. It counts `scannetpp/`, `scannetppv2/`, `scannet/` and `arkitscenes/` separately. More than 1% unknown eligible distance rows makes the loader audit and its production check FAIL, with unknown and total counts. Exactly 1% passes.

All 34 packet tests pass. Fixtures run through the frozen `c1_row` converter and classify all four canonical prefixes without unknowns. Real SQLite loader checks cover 0/100, 1/100, 2/100, 1/99 and 4/4 unknown rows, including propagation through `loader_audit.main` to its admission report. The packaged submit gate rejects invalid GO under PYTHONOPTIMIZE=1 and 2; it runs with `-I` and PYTHONOPTIMIZE unset. `proof/ROUTING_PREFIX.json` and `logs/tests.log` record the evidence.

V7 retains its producer receipt, database, mix and source selections. The selection implementation fingerprint binds the changed loader code. Config identity: `d8b03fd14db01af4def4a0cfd9a49d16ec492d9a3c6b0c56977f7f22b79f705a`. Run key: `26cc98b7`. Archive: `p_c5f3847d.tar`. Archive SHA256: `888027436a99cfec360959c46f4271222e4c029f5d36eb9870fea4f669231029`.

Pre-submission fixtures verify the current packaged config identity before building simulated evidence, reject malformed records and compare inherited runtime bytes. The operator archive rebuild is byte-deterministic; two fixture deployments have identical manifests. Four-rank OFF identity and the final-config first batch pass. The packet, report, gate records and checksums bind this identity. Production routing, native preparation and independent review remain pending; these fixtures do not certify production data or grant launch authorization.

`FIX7.diff` compares tools, tests, configs, out and work/tree against `/scratch/jjyeung/orch_n30/r1_ops/work/snap_f719b05f` (fix-6 archive f719b05f). The diff excludes itself, this note and SHA256SUMS to avoid recursion. The checksum manifest authenticates both FIX7 files. Binary changes include before/after hashes. Only loader_audit.py changes in the trainer tree; no inherited b/ file changes. All writes stay in this lane; no SSH, Orchard, Git, GPU or deletion command ran.

The reports apply the no-archaeology writing rule. The frozen-snapshot comparison is retained because the brief explicitly requests a reviewable delta.

Changed files covered by the diff:

- `tools/finalize.py`
- `tools/package_operator.py`
- `tools/run_local_checks.py`
- `tools/write_fix7.py`
- `tests/test_derivation_pre_submit.py`
- `tests/test_packet.py`
- `configs/diff_against_deployed.json`
- `configs/diff_against_h1_1.json`
- `configs/r1p.json`
- `out/BINDING.json`
- `out/DEPLOYMENT_REVIEW.patch`
- `out/OPERATOR.json`
- `out/R1P_PACKET.md`
- `out/REPORT.md`
- `out/REVIEW_REQUEST.json`
- `out/SAMPLER_REVIEW.patch`
- `out/config.json`
- `out/logs/finalize.log`
- `out/logs/fix7_derivation.log`
- `out/logs/fix7_initial_tests.log`
- `out/logs/fix7_targeted.log`
- `out/logs/local_checks7.log`
- `out/logs/local_checks7_final.log`
- `out/logs/make_proof.log`
- `out/logs/package.log`
- `out/logs/package_repeat.log`
- `out/logs/rebind_fix7.log`
- `out/logs/tests.log`
- `out/operator/BINDING.json`
- `out/operator/c.json`
- `out/operator/config.json`
- `out/operator/d.json`
- `out/operator/e.txt`
- `out/operator/ids.json`
- `out/operator/j.json`
- `out/operator/jb.sh`
- `out/operator/p_26cc98b7.sh`
- `out/operator/proof/selection/q.json`
- `out/operator/proof/selection/r.json`
- `out/operator/records/c.json`
- `out/operator/records/d.json`
- `out/operator/records/j.json`
- `out/operator/records/v.json`
- `out/operator/s.json`
- `out/operator/s.sh`
- `out/operator/sums.txt`
- `out/operator/t.tar`
- `out/operator/v.json`
- `out/p_c5f3847d.tar`
- `out/proof/DERIVATION.json`
- `out/proof/FIRST_BATCH.json`
- `out/proof/GATES.json`
- `out/proof/OFF_IDENTITY.json`
- `out/proof/PRE_SUBMISSION.json`
- `out/proof/ROUTING_PREFIX.json`
- `out/proof/UNIT_CANDIDATE.json`
- `out/proof/UNIT_PACKING_CHECK.json`
- `out/proof/inputs.json`
- `out/proof/loader_audit.json`
- `out/proof/local_config.json`
- `out/proof/local_prepared.json`
- `out/proof/p_26cc98b7.sh`
- `out/proof/selection/q.json`
- `out/proof/selection/r.json`
- `out/r1p_code.tar`
- `out/records/c.json`
- `out/records/d.json`
- `out/records/j.json`
- `out/records/v.json`
- `work/tree/student_pilot/loader_audit.py`
