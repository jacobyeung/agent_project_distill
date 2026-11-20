Built and checksummed all deliverables in `boxdev`.

Run there when the dump arrives:

```bash
./run.py --depth ../r1/returned/0.gz --receipt ../r1/returned/4.json --out out/BOXDEV.json
```

Verified: six tests passed, including the full 150-item synthetic run and parity STOP gate; 142 real T1 stored-box checks passed; three changed K1 predictions and printed boxes matched exactly.

The frozen rule uses **10 cm voxels and three-frame support**. Real dev parity, scores, and verdict remain pending the dump.

[Build results and measured costs](/scratch/jjyeung/orch_n30/lever1_c/boxdev/BUILD_RESULTS.md) · [Report template and renderer findings](/scratch/jjyeung/orch_n30/lever1_c/boxdev/REPORT_TEMPLATE.md)