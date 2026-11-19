# Mask carry: DRY RUN ON STUB TRACKERS (not a result)

Bars read on S_PHR (S_PHR: PRESENT); frame set cross-fit by room fold. Decision: **OBJECT_ARMS_CLOSED**. carry_precision fails: the object arms (size, appearance order, counting) stay closed.

| Seed set | Frame set | C_best1 | C_fused | C_fused - A0 [95%] | Precision on-target | Size - A0 [95%] | First-seen | Frame recall |
|---|---|---|---|---|---|---|---|---|
| S_A0 | STUBSEED | 56.77 | 56.77 | +0.00 [+0.00, +0.00] | n/a (0/0) | +0.00 [+0.00, +0.00] | 61.7% | 13.4% |
| S_GT | STUBRASTER | 73.97 | 78.62 | +21.85 [+17.82, +26.00] | 100.0% (4682/4682) | +19.22 [+16.35, +22.11] | 85.5% | 100.0% |
| S_PHR | STUBSEED | 60.50 | 60.50 | +3.73 [+2.05, +5.48] | n/a (0/0) | +0.71 [+0.22, +1.26] | 62.8% | 14.0% |
| S_PHR | cross-fit | | 60.50 | +3.73 [+2.05, +5.48] PASS | n/a FAIL | +0.71 FAIL | 62.8% FAIL | |

A0_deployed 56.77 (36 refusals scored 0); A2_gt_masks 73.97; fused_cf 78.62. Deployed frame recall 57.9%, best pool candidate 74.8%, false presence 976 operand-frames, first-seen pairs 76.56%, size MRA 52.36 on 770 objects.
Frame-set choice per fold: 0: STUBSEED, 1: STUBSEED, 2: STUBSEED, 3: STUBSEED, 4: STUBSEED.

- S_A0/STUBSEED: all-seed precision n/a (0/0), seed-majority n/a; false presence 279 operand-frames; refusals 36.
- S_GT/STUBRASTER: all-seed precision 100.0% (4682/4682), seed-majority 100.0%; false presence 0 operand-frames; refusals 0.
- S_PHR/STUBSEED: all-seed precision n/a (0/0), seed-majority n/a; false presence 235 operand-frames; refusals 22.
- carry_ceiling (diagnostic): S_GT C_fused 78.62 against fused_cf 78.62.

Held-out captures, R0-dev, dev-S1 and official items were not opened; every number is on the 1,037 K1 training rows.
