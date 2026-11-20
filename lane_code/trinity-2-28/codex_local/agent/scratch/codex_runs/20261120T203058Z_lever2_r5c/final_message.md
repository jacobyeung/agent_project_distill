ARKit reproduction **PASS**: all 12 arrays and NPZ bytes match; tolerance unchanged. **21/22 captures pass; 22/22 built.** The original 15 NPZ hashes remain unchanged. All 26 tests pass.

41254810 passes geometry but fails binding: both same-frame IoU medians are zero.

Files under [out/gt/arkit_gt/gt/](/scratch/jjyeung/orch_n30/lever1_c/nogt/out/gt/arkit_gt/gt):

| File | Result | SHA256 |
|---|---|---|
| 41126645.npz | PASS | `574d8d99da58f0c8bf04630fa75d7387b0427bcf4527f7ad62a3ff1d4a42cd54` |
| 41159771.npz | PASS | `9716ccc08f618e33c19389b7bb6999d4ef3bc389084cce13b357268f1f429b9f` |
| 41159772.npz | PASS | `7c6bdfcb058bbc4d4fd702b8999da0910b272c3ac95a2529f8d7be2ebed844c6` |
| 41254810.npz | FAIL | `c2e4a881d1541d30a5c7f2f23e3cb1c55a8f66387edf6d6bbc720f6726c8e8ba` |
| 42446097.npz | PASS | `278e8ab34d66e6d568ec113118074d32ecfd83f65ff255898165b1935f596494` |
| 42899829.npz | PASS | `fd7def74e0b0ef7c7d9788b43c8170f27f30e6eff5e4f4c654f0ed1bd987715a` |
| 47331002.npz | PASS | `6558c79afc422436d8be66fd55ab2734e2bce601a81342384d759ac0295a7e4b` |

Updated [report](/scratch/jjyeung/orch_n30/lever1_c/nogt/out/NOGT_REPORT.md:56), CAPTURE_CHECKS.json, REPRODUCTION.json, and SHA256SUMS. Old report text and checksum lines are preserved; repeated checksum paths use the last entry.