ReVSI × harness: NOT READY; ReVSI × e2e: NOT READY; VSI-Bench × harness: NOT READY; VSI-Bench × e2e: NOT READY.

The whole N suite has 122 passes, two cross-kit skips and one incompatible original reviewer case. The original R4 test appends OFFNATIVE_PACKET_SHA256 itself; its current-API sibling passes. The reviewer F1/F2/F3 gate passes all three cases, and test_prodroot passes all three production-root cases. Reviewer files remain byte-equal.

Four whole-worker CPU fixtures and one full CPU rehearsal under a production-style /tmp root pass. The rehearsal root remains below 20 MB; large fixture assets and traces stay in RAM. Mounts, transport and models remain CPU stand-ins.

All four opacity adapters are identical. Each packet derives a deterministic salt from its member pins and the Trinity-only secret; token and alias lookups use the salt. Unsalted dictionary checks find zero keys. The public salt still allows dictionary guesses that include it. In-job contents are exempt from the naming rule.

Production still requires complete owner artifacts, live timing and native-library validation, proof inputs and transport-only rehearsals. ReVSI clip hashes and pixel correspondence remain pending. The 17 whole-scene shards fit their planning estimates; live timing remains unmeasured. Nothing was submitted or uploaded.

code.tar SHA256 `66d1a0a759a3bf9b7f3ca62cd15d13fc50cf66fd3b7e01e7873f0e0a9083baaa` (8983667 bytes). N7_VALIDATION.json, N7_REVIEW_GATE.json, N7_PRODROOT.json, N7_SALT_CHECK.json, N7_ARCHIVE_CHECK.json, N7_STORAGE.json, CODE_PINS.json, DEPENDENCY_PINS.json and SHIP_SHA256SUMS bind the release.
