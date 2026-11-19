The packaged deriver validates production-form evidence and reaches READY without a Slurm identity or persistent-run initialization. Config identity remains `782f303d81e300b1b24094863d6ce7d984690529f0e414474c3e693df87e19da`. All 31 packet tests pass.

Archive: `p_1130b378.tar`. SHA256: `f719b05fcbe934654499d786d1a56d413c0db71f6a1fd9a60b5097e788ebfad9`.

`tools/derive_deployment.py` uses inherited `g.read_pin`, `g.identity`, `g.digest` and `d.contract`. It checks the review verdict, reviewer, config/source identity, admission hash, contract and scope; staging status, config/source identity, missing inputs and write count; durable archive status, location, tree and archive hash; and mode-p authorization identity, source, contract and expiry. It does not call `g.check`, `persistent_launch` or `r8.main`. The inherited verifier has no complete evidence-only entry point, so the deriver composes its read-only helpers with these record predicates. The unchanged job path runs the full allocation-time verifier.

`tests/test_derivation_pre_submit.py` uses the read-only driver `evidence_body.py`, `fixture_h`, `fixture_b` and the construction in `test_local.py`. It exercises the packaged `d.py` with every Slurm environment variable removed. A call guard refuses allocation-time persistence, and an audit guard refuses writes outside the lane's test directory. The READY result retains `production_authorized=false` in the derivation receipt. Four wrong-identity records and fourteen malformed record/binding variants fail. Runtime files under `b/` and `job.sh` match the existing fixture derivation byte for byte.

The tests use observed H1 record schemas and raw native selection receipt/index bytes. Two absent data archives contain explicit local sentinels; review attestations are simulated. These fixtures prove control flow and evidence validation, not production data authenticity, independent approval or native preparation. `proof/PRE_SUBMISSION.json` and `logs/tests.log` record the scope and results. The operator archive rebuild is byte-deterministic, and two fixture derivations have identical manifest hashes. Existing four-rank OFF and first-batch results remain bound to the unchanged config and trainer tree.

`R1P_PACKET.md` sets `H=/project/community/jjyeung/okh7/x_3fdda0fb` and prints source manifest SHA256 `661ccd85b7a8f1afd25297869dc3a28539e64a3a0ab9a74ee928c0c5ab8a66c3`. The fixture manifest value remains confined to local evidence. The archive, `OPERATOR.json`, `REPORT.md`, `R1P_PACKET.md`, `proof/GATES.json`, review request and checksums are resealed together. Independent final-packet review, content certification and the production CPU proof remain pending; no Orchard, Slurm, SSH, GPU or Git command ran.

`FIX6.diff` compares `tools`, `tests`, `configs`, `out` and `work/tree` against `/scratch/jjyeung/orch_n30/r1_ops/work/snap_782f303d`. Config and trainer files are byte-identical. The diff excludes itself, this note and `SHA256SUMS` to avoid recursive checksum dependencies; the final checksum manifest authenticates both FIX6 files. Binary changes carry before/after SHA256 values. No inherited `b/` file was edited. No files were deleted or edited outside this lane.

The report and packet instructions apply the no-archaeology writing rule. The snapshot comparison is retained because the brief explicitly requests a reviewable delta.

Changed files covered by the diff:

- `tools/derive_deployment.py`
- `tools/finalize.py`
- `tools/run_local_checks.py`
- `tools/unit_binding.py`
- `tools/write_fix6.py`
- `tests/test_derivation_pre_submit.py`
- `tests/test_packet.py`
- `out/FIX5.diff`
- `out/FIX5.md`
- `out/OPERATOR.json`
- `out/R1P_PACKET.md`
- `out/REPORT.md`
- `out/REVIEW_REQUEST.json`
- `out/UNIT_PACKING.md`
- `out/logs/finalize.log`
- `out/logs/fix5.log`
- `out/logs/local_checks5_final.log`
- `out/logs/package.log`
- `out/logs/package_repeat.log`
- `out/logs/pre_submission.log`
- `out/logs/tests.log`
- `out/logs/unit_packing5.log`
- `out/operator/d.py`
- `out/operator/sums.txt`
- `out/operator/u.py`
- `out/p_1130b378.tar`
- `out/proof/DERIVATION.json`
- `out/proof/FIRST_BATCH.json`
- `out/proof/GATES.json`
- `out/proof/PRE_SUBMISSION.json`
- `out/proof/UNIT_CANDIDATE.json`
- `out/proof/UNIT_PACKING_CHECK.json`
