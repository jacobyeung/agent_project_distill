# Scorer check: surviving score_and_aggregate_orchard.py (0bb536ca) vs the benchmark authority

Authority: /home/jjyeung/agent_project/AGENTS.md section 3 defines NA scoring as MRA through the compatibility scorer
agent/agentic_information_5.0/evaluate_benchmark_v4.py (4ec4da5f, identical to the root copy), which imports
mean_relative_accuracy, to_float and the aggregation from agent/evaluation/scoring.py (f67703ea; contract
"na": "mean_relative_accuracy_0.50_0.95_0.05", aggregation "decimal_mean_round_half_even_15_places").
Surviving file: /scratch/jjyeung/orch_cd/k1_build/work/kit_k1a/native_kit/vendor_sam/vendor/score_and_aggregate_orchard.py
(0bb536ca...ef2a1). The kit pins exactly this copy in kit_k1a/out/DEPENDENCIES.json line 48; it pins no o3_cache copy.

## official_mra vs mean_relative_accuracy, line by line
| step | authority (scoring.py 141-153) | surviving (243-258) | same? |
|---|---|---|---|
| None input | 0.0 | 0.0 | yes |
| non-finite input | no guard; NaN/inf comparisons fall out to 0.0 for positive targets | explicit guard, 0.0 | yes, except inf pred with negative target (see below) |
| target 0 | 0.0 always | 1.0 if pred == 0 else 0.0 | NO: (0, 0) scores 0.0 vs 1.0 |
| relative error | abs(pred-target)/target (signed denominator) | abs(pred-target)/abs(target) | NO for target < 0: authority error <= 0, scores 1.0 for every pred; surviving scores the true relative error |
| point count | int((0.95-0.5)/0.05+2) = int(10.999999999999998) = 10 | same expression, 10 | yes |
| thresholds | np.linspace(0.5, 0.95, 10) | 0.5 + i*(0.95-0.5)/9 | NO at i=7: 0.85 vs 0.8499999999999999, so 1-c = 0.15000000000000002 vs 0.15000000000000013 |
| hit test, mean | err <= 1-c, mean of 10 | same | yes |

## Grid evaluation (compare.py sha 256f4d6e, COMPARE.json)
- 13,952 (pred, target) pairs: targets {0, -0, -1, -2.5, 1e-9, 0.3, 1, 2.5, 3, 7, 100, 1e6, +-inf, nan, None}; preds the same
  plus every boundary t(1+-0.05k), t+-|t|0.05k and their float neighbours. 1,737 differ: 6 at target 0 (pred +-0),
  1,725 at negative targets, 6 at positive finite targets (all on the 0.85 boundary, e.g. pred 1.15 target 1.0:
  authority 0.7, surviving 0.8; pred 2.55 target 3.0: 0.7 vs 0.8). No difference for None, NaN or inf with target >= 0.
- 200,000 random positive-target pairs with many exact ties: 1,054 differ (0.53%), all by 0.1.
- K1 baseline constants (k1_report.constant picks an interval endpoint g*t or g*(2-t)), scored against the same g:
  2,487 of 120,000 differ (2.1%). Held-out rows differ only when the train-fitted constant lands exactly on 0.85 x a test GT.

## Parse layer (k1_report passes float(pred), float(gt))
authority to_float takes the last number in free text ('3.5 m' -> 3.5, '-2' -> 2.0, '1e3' -> 3.0); surviving
official_to_float is float() with finite check; k1_report's own float() raises on text and passes 'nan'/'inf' through
(official_mra then returns 0.0). For numeric K1 rows the three agree except the sign case.

## Aggregation (score_official_vsibench, not imported by k1_report)
Surviving: float means; collapses rel_direction only when all three sub-tasks exist; VSI 6 MCA + 4 NA types only;
MCA fuzzy match = first space-separated token. Authority: Decimal mean rounded half-even at 1e-15; collapses whichever
direction sub-tasks exist; includes VSTI types and any type containing "direction"; MCA via fuzzy_matching_mca regex.
Synthetic 370-record VSI set: overall differs by 3.3e-16 with all three directions, by 0.00267 with 'hard' missing.

## Verdict
- The surviving official_mra is NOT identical to the authority's MRA. It equals it on every finite positive target
  except the ulp-level 0.85 boundary; it differs at target 0 (pred 0) and on all negative targets.
- k1_report.py may import the surviving file unchanged as the kit's pinned scorer (DEPENDENCIES.json pins 0bb536ca);
  its K1 decision will then differ from authority MRA on exact 0.85-boundary rows and on zero targets.
  If K1 must equal the authority bit for bit, it must import mean_relative_accuracy from agent/evaluation/scoring.py.
- Import lines that must change in kit_k1a/work/k1_report.py (I changed nothing):
  line 6 `sys.path.insert(0,str(gate.ROOT/'o3_cache/work/kit/vendor_sam/vendor'))` points at the lost folder; it must
  name `k1_build/work/kit_k1a/native_kit/vendor_sam/vendor`. Line 7 `from score_and_aggregate_orchard import official_mra`
  stays (or becomes `from evaluation.scoring import mean_relative_accuracy` with line 6 naming /home/jjyeung/agent_project/agent,
  plus line 17's call renamed, if authority equality is required).
- Same lost path elsewhere: kit_k1a/work/parity_live.py line 10 (imports sam_backend from o3_cache/.../vendor).
