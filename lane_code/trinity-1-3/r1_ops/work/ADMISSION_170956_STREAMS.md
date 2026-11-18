# Admission of 170956 (config fac07052; log f170956.proof.log sha 911729ca), stream counts after scene exclusion
| Stream | seen | removed | retained | card expectation |
|---|---|---|---|---|
| VQA | 203,812 (after 7 REMOVE lists; n.json matched 601) | 0 | 203,812 | 203,812 admitted (FIX10) |
| routing | 47,898 | 0 | 47,898 | 14,020 + 12,260 + 9,143 + 11,728 = 47,151 routing + 747 unit rows = 47,898 |
| pointing | 20,239 | 0 | 20,239 | (auxiliary) |
| pose/0 | 27,604 | 5,977 (dev 1,097, bench 4,880) | 21,627 | (S2 pose source 0) |
| pose/1 | 202,320 (1,200 benchmark rows dropped before) | 28,960 (dev 6,800, bench 22,160) | 173,360 | (S2 pose source 1) |
Admission ended `exit rc=0` at 2026-11-18T00:27:16Z.
