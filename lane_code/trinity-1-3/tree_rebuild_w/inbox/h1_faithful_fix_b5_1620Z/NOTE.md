# From h1_headsft (2026-11-16 16:20Z): standalone S1 faithful-own-rows patch, current version
Supersedes h1_faithful_fix_1432Z (b2). This version (kit Build 4/5) adds the preparation identity gate: S1 refuses below
95% faithful identity on the bound routing receipt. Tolerance-based answer_differs (option change, >10% displacement,
>10 deg rotation) is the stop metric only; faithful rows keep the model's own answer (ORCH RULING 1535Z).
Applies on sealed b01ce449 alone (no dependency on the rest of H1); composition proofs in kit BUILD_REPORT.md Build 4.
sha256 cdc6c9f72fed4c0b9b107e8b2f105a2284a32b32075e650c99b8a8012ad47fbf
