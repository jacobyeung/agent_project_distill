# Grounding selector for whole-object masks: GRD-1 single choice and the set selector with 3D identity (build B1)

## Question
The fixed programs need whole-object masks of every instance of a named category on every sampled frame, with identity across frames. Can a selector learned on training rooms, which accepts SAM 3's linked candidates as a set and merges them by 3D identity, close the program loss of the deployed (native) selector? What do mask tightening and propagation by projection add? Where does the remaining gap sit?

## Answer
The routed default is type-aware. Unique-object types take the accept model's top candidate, with every mask cut to its interior depth range. Counting takes every candidate with P(accept) >= 0.15 and joins them into 3D instances with a learned pairwise merge. I chose tau and the merge on dev only.

Under gt_ceiling's fusion policy on G3T depth, the routed default beats direct on abs distance and trails it on size and counting (1,493 VSI-Bench ScanNet items, 76 scans; direct fallback; paired scene bootstrap; `out/accept2/parity/SUM.md`):

| type | route | GT masks | route - direct |
|---|---|---|---|
| abs distance | 66.5 | 79.3 | +9.2 [+3.8, +14.8] |
| size | 62.3 | 77.1 | -5.8 [-10.3, -1.3] |
| relative distance | 59.1 | 91.5 | -1.9 [-10.6, +6.7] |
| direction easy / medium / hard | 81.0 / 84.4 / 78.2 | 100 / 100 / 95.5 | within their CIs |
| counting | 54.4 | 98.1 | -16.7 [-23.9, -10.4] |

- **The accept step is the largest remaining loss.** The top candidate is the wrong object on 12 of 30 hand-read operands because it is a look-alike of another category, and on 9 because it is a real object the annotation does not label. The rest are parts (6), mixed linking (2) and background (1).
  - CPU features (centre agreement, extents, a size prior, phrase competition) move the accept step by at most 1 point.
  - A visual check pays only if it fixes half the wrong top candidates while breaking at most 5% of right ones. The student's PRES32 + V3 features reach about a quarter on dev.
- **Proposals bind weakly through the selector.** Each recall point is worth about 0.2 on abs, size and rel distance, against 7-12 points for all never-proposed objects with GT masks.
- **Counting is accept-bound.** Identity work is worth 6.2 with perfect accepts. With today's accepts it hurts, because the learned merge hides false accepts.

## Evidence (lane grd_selector, trinity-2-18; files under /scratch/jjyeung/orch_cd/grd_selector)

### Accept v2 under the new geometry (`work/accept2/`, `out/accept2/`)
- **Harness.** `price3.py` prices any arm under gt_ceiling's policy: best single view for absolute distance and voxel vote plus the largest view for the rest (`price_sel.RuleFused`, imported read-only), on G3T depth with the depth cut. It reproduces gt_ceiling's TG_MASKDECOMP predictions for route, GT and gt_prop on all 1,298 non-counting items. In `parity/SUM.md` and `item2_*/SUM.md`, the column `oracle` is the variant with a top-peak fallback. gt_ceiling's oracle_dc is in `oracle_vsi/SUM.md`: rel +13.9, pooled +7.9.
- **Wrong-object reading** (`item1/READING.md`, 30 of 51 distinct wrong operands, which drive 124 wrong rel and direction items):
  - look-alike of another category: 12 (37 of 85 items), including 2 vocabulary cases;
