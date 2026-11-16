# Build decisions

The suite runs from an empty directory. Options were to change into the source directory to accommodate legacy relative fixtures, or preserve the requested empty-directory harness. The default preserves the requested harness. Each legacy failure is compared with the same case on unchanged base code under identical conditions; a missing relative fixture is reported with its traceback.

Each packaged suite group receives a fresh empty working directory under `work/tmp`, including each base comparison. This prevents a preceding group from supplying accidental relative fixtures. Proof outputs retain their fixed folders. The package runner verifies that both extracted source inventories remain unchanged after testing.

The comparison base uses a writable extracted copy whose source inventory must match the original before and after testing. The original stays read-only. Comparing against a base that cannot create ordinary local scratch artifacts could hide a regression, so the initial original-base run is diagnostic only.

Existing tests that expect unauthenticated readers to answer may conflict with the required bank refusal. The default preserves the refusal and updates only demonstrably obsolete test expectations, with before/after evidence. Unrelated failures remain regressions to repair; they cannot become skips or pre-existing failures without matching base evidence.

CPU coverage counts only current file hashes and compiled-source fingerprints. The default exercises locally reachable branches. Only branches that require identified absent frame-host, pretrained-loader or GPU inputs receive external-input classifications. Tiny real producer/reader tests and registered sampler metadata tests remain separate; neither represents a full-store run.

Final kit staging waits until source and harness freeze. Both kits retain closed authorization. Real runtime, archive, frame-map, bank, export and remote-state checks remain mandatory host work.
