VSI-Bench × direct: NOT READY for production; ReVSI × direct: NOT READY for production.

The whole R suite passes 49 tests with one cross-kit skip. The reviewer F1/F2/F3 gate passes all three cases across R and N; test_prodroot passes all three cases. Reviewer files remain byte-equal. Four direct CPU rehearsals and one full production-root rehearsal pass. The latter stays below 20 MB.

Accepted report reproduction is exact: 68.77 [66.5, 71.0] and 64.94 [61.3, 68.4], with every group and all three budgets checked. Accepted reader, scorer, parity and item bytes remain identical.

Packets use deterministic salts derived from member pins and the Trinity-only secret. All unsalted dictionary checks find zero keys; public salts still permit guesses that include the salt. In-job contents are exempt from the naming rule. Source paths, child arguments and environment retain their naming checks.

Production still requires owner selection/export inputs, live native-library and namespace validation and transport-only rehearsals. CPU models, mounts and transport remain stand-ins. Nothing was submitted or uploaded.

vsi: SHA256 `9af222653edcdd3cdabc28e198150081ca5e54f7b607b2a6d9aa021608e777ce` (1572052 bytes).
revsi: SHA256 `3a639231fa224462c98fd61cec836ce950377cb019f30fa66eb70c1ac2cc4715` (1719061 bytes).

R5_VALIDATION.json, R5_REVIEW_GATE.json, R5_PRODROOT.json, R5_SALT_CHECK.json, R5_ARCHIVE_CHECK.json, R5_STORAGE.json, PACKAGE_PINS.json and SHIP_SHA256SUMS bind the release.
