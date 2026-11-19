# Documentation fix: PASS
OPERATOR.md, GPU_NEED.json and ROOMKIT_REPORT.md require an approved provenance copy, its launch flag and its SHA256 in the GO note.
The original KERNEL_PROVENANCE.json and KERNEL_FROZEN.json remain byte-identical to the source.
ROOMKIT_REPORT.md discloses the K1 gain +0.73 [-1.40, +2.69], training-only interpretation, and legacy rule/label inheritance; authorized_by remains the orchestrator's decision.
`bash scripts/cpu.sh scripts/gpu_run.py --help` confirms --provenance.
`bash scripts/cpu.sh tests/test_roomkit.py`: 43/44 pass; one known relocated-S0-path KeyError (out/TESTS_RAW.log).
`bash scripts/cpu.sh out/docs_validation.py tests`: 44/44 pass; only S0 path keys are translated in memory, with every digest preserved.
`bash scripts/cpu.sh out/docs_validation.py probe`: approved copy passes 19,211 prerequisite hashes; pending authorization is rejected; no GPU execution.
`bash scripts/cpu.sh out/docs_digest_check.py`: all 63 original code files and all 29 TESTS/GO code entries match; GO template bytes and aggregate digest are unchanged.
`bash scripts/cpu.sh scripts/package.py`: packages and verifies every ledger member; `cp out/sb_rkfix2.tar out/sb_rkdocs.tar` supplies the requested name.
`sha256sum out/sb_rkdocs.tar > out/sb_rkdocs.tar.sha256` records the archive checksum; see out/ROOMKIT_REPORT.md and out/GPU_NEED.json.
Approval and per-run GO remain MISSING. No original code, frozen evidence or source workspace file changed; all work used CPU and local disk.
The required inheritance disclosure is retained because it informs the orchestrator's authorization decision.
