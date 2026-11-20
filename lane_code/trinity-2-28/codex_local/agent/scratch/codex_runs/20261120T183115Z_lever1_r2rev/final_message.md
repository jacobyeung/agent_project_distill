**DEFECT — the GT-depth intervention confounds depth quality with missing raster coverage. Restore missing GT frames, or compare both depth arms on identical valid support and report coverage separately.**

Recomputed from [K1X.json](/scratch/jjyeung/orch_n30/lever1_c/r2/out/K1X.json), with contributions expressed over each full subgroup:

| Held-out group | Rows | Depth-swap Δ | New refusals | Refusal contribution | Remaining contribution |
|---|---:|---:|---:|---:|---:|
| ScanNet/++ | 114 | −0.26 | 0 | 0.00 | −0.26 |
| ARKit portrait | 54 | −6.30 | 6 | −6.85 | +0.56 |
| ARKit landscape | 48 | −17.50 | 11 | −15.63 | −1.88 |

**Missing frames explain the dominant loss.** All 17 new ARKit refusals select an entirely zero-depth frame. Across the eight affected captures, these frames have `valid=True` and `inst=-1` everywhere; none contains a mixture of zero and positive depth. Ten rows return `box unavailable` despite usable alternative selected frames; seven return `not seen` because their missing operand’s selected track contains only zero-depth frames.

The lift records a mask as visible before checking positive depth ([ladder_pricing.py:10](/scratch/jjyeung/orch_n30/lever1_c/r2/vendor/ladder_pricing.py:10)). The session then independently pins the largest **visible** mask and requires that frame to have lifted points ([box_v313.py:529](/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449/trace_format/box_v313.py:529)). This explains why the lift’s usable alternative frame does not rescue the answer.

A four-capture replay reproduced all 24 saved predictions/refusals. Excluding zero-depth frames from mask eligibility recovered all eight `box unavailable` rows in those captures; three `not seen` rows remained unsupported. For `42898541`, TV–refrigerator recovered to **3.56 m**, versus label **3.867 m**. This is a diagnostic intervention, not a corrected full-population score.

**Units and scale:** No evidence supports a millimetre/metre error. Checked positive depths are metre-sized and millimetre-quantized; `42898541` has median **1.939 m**. Oracle scale uses positive, high-confidence `GT/G3T` ratios ([e3_harness.py:225](/scratch/jjyeung/orch_n30/lever1_c/r2/vendor/e3_harness.py:225)); the swap applies `q=s/SO` once ([k1x.py:218](/scratch/jjyeung/orch_n30/lever1_c/r2/k1x.py:218)). Held-out ARKit q ranges are **0.948–1.121 portrait**, **0.882–1.224 landscape**. A uniform GT-depth multiplier cancels through SO in the depth-alone/own-scale cell.

**Holes and interpolation:** `sample_gt` retains zeros and checks only frame-level `valid` ([k1x.py:187](/scratch/jjyeung/orch_n30/lever1_c/r2/k1x.py:187)). Bilinear interpolation treats zero as a numeric depth; the lift drops nonpositive centre depths afterward ([geometry_profiles.py:154](/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:154), [ladder_pricing.py:16](/scratch/jjyeung/orch_n30/lever1_c/r2/vendor/ladder_pricing.py:16)). Partial holes could therefore create false positive depths, but the observed refusal mechanism is **whole-frame absence**.

**Resolution/alignment:** GT depth is floor-sampled onto 51×51 endpoints, then bilinearly queried: approximately **6.4×4.8 native raster pixels per grid interval**, reversed in portrait. The four checked captures have matching raster/PNG orientations and exactly 2× dimensions: 320×240→640×480 or 240×320→480×640. Served canvas transforms contain scaling without translation ([geometry.py:66](/scratch/jjyeung/orch_n30/sb_kbox4/reader_src/e2e_reader/geometry.py:66)). Median normalized focal ratios were **0.989–1.029**. These checks disfavor a gross crop, rotation, or scale mismatch; they do not independently verify the upstream 2.5× RGB conversion. K1X applies no additional 2.5× factor.

**Spread and mask bleed:** The 5×5 stencil measures relative depth spread, and the lift retains points below its median ([geometry_profiles.py:174](/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449/student_pilot/geometry_profiles.py:174)). Background contamination survives: `45662908` bed pixels outside the target instance increase from **47.1% to 56.4%** after filtering. Removing the spread cut recovered none of the four-capture refusals. Edge effects remain plausible contributors to residual errors, but do not explain the dominant loss.

**Joins and labels:** Capture keys derive from canonical identities; tower/GT anchor indices and GT hashes are checked ([k1x.py:130](/scratch/jjyeung/orch_n30/lever1_c/r2/k1x.py:130)). Corrected labels join by row ID, and deployed choices remain fixed across cells. I found no wrong-key or label-join explanation.

**C3 +2.69 and endpoint 79.07:** Neither has held-out GT-mask refusals. In the audited missing frames, `inst=-1` makes GT masks empty in **both** baseline and swapped cells ([k1x.py:183](/scratch/jjyeung/orch_n30/lever1_c/r2/k1x.py:183)); thus the deployed-mask refusal penalty does not transfer directly. Both figures remain conditional on GT-mask coverage and retain coarse sampling, spread filtering, and served intrinsics. **79.07 is therefore not an unrestricted GT-geometry ceiling.** The existing synthetic tests use positive depths and miss this coverage failure ([test_k1x.py:19](/scratch/jjyeung/orch_n30/lever1_c/r2/tests/test_k1x.py:19)).

Fix depth eligibility separately from pose validity: excluding a missing-depth reference frame through `geo.has()` can also break valid pose transforms. Add whole-frame-missing and partial-hole regression cases; restore rasters before interpreting a pure depth intervention.

`REVIEW_R2.md` could not be written because the session’s filesystem sandbox is read-only. No files were changed.