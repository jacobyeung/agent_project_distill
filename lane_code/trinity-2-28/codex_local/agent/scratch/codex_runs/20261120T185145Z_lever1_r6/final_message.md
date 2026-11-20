Built and validated. **Route retention remains unresolved:** same-item gate scores are unavailable. **Centimetre twins trigger the <−3 diagnostic threshold; the diagnostic was not run.** The ≥2 gate trigger remains unidentified; only twin-substitution estimates are available.

Dataset splits remain hypotheses. Scores are MRA points:

| Dataset | T1 | T2 points | Dense64 |
|---|---:|---:|---:|
| ARKit | 60.0 | 59.6 | 59.4 |
| ScanNet | 62.3 | 58.3 | 48.0 |
| ScanNet++ | 56.2 | 68.2 | 58.4 |
| ScanNet combined | 58.0 | 65.3 | 55.3 |
| All 150 | **58.6** | **63.5** | **56.6** |

| Constant baseline | Score [95% CI] | Served advantage |
|---|---:|---:|
| Class median, leave-one-room-out | 31.5 [25.8, 37.3] | +27.1 |
| Global median, leave-one-room-out | 27.0 [20.9, 33.2] | +31.6 |
| Pooled median, descriptive | 27.6 [21.5, 33.8] | +31.0 |

The class baseline uses the global fallback on **109/150 items**.

Observed routed-minus-direct twin differences:

| Direct twin’s unit | Step 200 [95% CI] | Step 400 [95% CI] |
|---|---:|---:|
| Metres | +8.3 [−11.9, 29.5] | +16.0 [−8.8, 40.0] |
| Feet | +42.8 [31.5, 54.9] | +37.7 [24.9, 51.7] |
| Metres + feet | +32.4 [21.8, 42.8] | +31.7 [20.2, 43.8] |
| All units | +13.9 [6.8, 21.0] | +12.0 [4.0, 19.8] |
| Centimetres | −7.2 [−20.2, 6.7] | **−3.2 [−16.1, 10.2]** |

Twin wording and units differ. Box/“not seen” gate proxies change pooled scores by −3.2/−2.0 at steps 200/400; centimetre proxies improve by +4.6/+5.2.

**Deviations:** both named direct reads contain zero distance items. D580 yields **198/161** route/direct pairs, not 82; 82 counts step-400 template “not seen” responses.

Tests reproduce all 450 capture scores and all eight INDEX arm means. Hash checks pass. Full intervals, funnel stages, gates, and provenance are in the 67-line report and JSON:

[Report](out/REPORT_R6.md) · [Ledger](out/LEDGER.json) · [CLI](ledger.py) · [Tests](test_ledger.py) · [SHA256SUMS](out/SHA256SUMS)