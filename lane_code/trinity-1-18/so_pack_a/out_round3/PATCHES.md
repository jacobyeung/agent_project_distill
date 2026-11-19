# Patch application and verification

Apply both unified diffs with `patch -p1` at a writable root corresponding to the input mirror. Patch 01 adds pack.py, pack_verify.py, probes, tests and operator documents. Patch 02 adds pack_token.py and its test beside native r10 and D builders. Native sources and embedded scripts remain unchanged.

TOOL_SHA256.json defines the canonical files. PATCH_VERIFIED.json records fresh application and byte equality with work/r3/src, work/r3/applied and the top-level delivery. out_round2 preserves the reviewed outputs. REPORT.md, TEST_RUNS.json and BEFORE_RUNS.json retain exact commands and outputs; generated evidence manifests are outside the patches.

Run test_pack.py, test_native.py, test_review.py, test_review2.py and test_review3.py under CPU Python with -I -s -B and fresh output directories. The native RESULT.json feeds test_review.py. Login snippets, both adapter tests and the round-3 verification tests also run under /usr/bin/python3 3.6.8. Use nice -n 10, eight thread/core limits and CUDA_VISIBLE_DEVICES=""; exact commands are in REPORT.md. Tests redirect or stub production paths and transport.

Production requires --enable; token rewriting requires --enable-token; normalization and structural fill are explicit switches. Every remote action needs --yes and the exact built token. Verify needs no ledger reservation and creates no place.attempt. Place requires the ledger reservation and a fresh receipt matching the sealed part SHA256s before consuming its attempt. Default-OFF D delivery equality is measured; r10 source equality is checked, while its full build lacks inputs.
