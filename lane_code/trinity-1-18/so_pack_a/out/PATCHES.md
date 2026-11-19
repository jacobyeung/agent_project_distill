# Patch application and verification

Apply both diffs with patch -p1 at a writable root corresponding to the input mirror. Patch 01 adds the pack command, probes, tests and operator documents. Patch 02 adds pack_token.py and its test beside the native r10 and D builders. Native sources and embedded scripts remain unchanged.

TOOL_SHA256.json defines canonical files. PATCH_VERIFIED.json records fresh application and equality with work/r4/src, the tested work/r4/applied_final tree and top-level delivery. out_round3 preserves the reviewed outputs. REPORT.md and TEST_RUNS.json retain exact commands/outputs; evidence manifests and REPORT are outside the patches.

Run test_pack.py, test_native.py and test_review.py through test_review4.py under CPU Python with -I -s -B and fresh output directories. Native RESULT.json feeds test_review.py. Both adapter suites and generated login code run under /usr/bin/python3 3.6.8; round-3 and round-4 suites also run there. Use nice -n 10, eight CPU threads/cores and CUDA_VISIBLE_DEVICES="". REPORT.md records commands and resource limits. Tests redirect or stub remote paths and transport.

Production requires --enable; token rewriting requires --enable-token; normalization and structural fill are explicit switches. Every remote action needs --yes and the exact built token. Record token/delivery SHA in the ledger before verify; place enforces reservation and checks the verify receipt before place.attempt. A valid success can be reused; completed stale or failed verification can be explicitly rehashed without consuming placement. Default-OFF D equality is measured by test_native.py; full r10 lacks inputs.
