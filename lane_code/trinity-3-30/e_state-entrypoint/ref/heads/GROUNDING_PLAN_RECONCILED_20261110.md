# Grounding from name to 3D: reconciled plan (d_fable + d_astra)

2026-11-10 ~09:10Z, trinity-2-18, judge lane (Claude Opus), read-only except this record, the Astra copy and five briefs.
Inputs: d_fable `GROUNDING_OBJECT_FIRST_SVP_20261110.md` (= `/scratch/jjyeung/orch_cd/design_g3d/d_fable/out/DESIGN.md`, BUILD_TASKS B1-B14); d_astra `GROUNDING_NAME_TO_3D_ASTRA_20261110.md` (= `/scratch/jjyeung/orch_cd/design_g3d/d_astra/out/DESIGN.md`, BUILD_TASKS T01-T18). Gains are routed+fallback minus T0 m800 direct on dev 858, in the order direction medium / hard / relative distance / absolute distance. The "80.1 / 58.7 / 73.0" figure has no source file and is not used.

## Question
How should the student turn an object's name into a 3D position and extent inside its own generate pass, with and without SAM 3 as a frozen tower, and what do we build and run first?

## 1. Agreement and differences

**Both designs agree on these points.**
- The geometry chain works, and the gate is identity. With GT masks the gains are +24.1 / +23.9 / +27.3 / +39.6, and an oracle choice among SAM 3's instances gives +22.8 / +26.1 / +24.9 / +38.1 (`mdg_next/events/20261110T0236Z_RESULT_nogo_card_S3I.md`).
- The unit is the (clip, name) object, held in a lazy per-clip memory that later questions reuse. Neither design builds a full scene table up front.
- The model resolves each name on a few selected views at full detail, never on all 32 frames, and it verifies the object before it propagates it with pose and depth.
- Agreement across frames cannot correct a look-alike that persists across views.
- Masks supply extent for now, and `<gap>` keeps its exact surface-to-surface minimum. Keypoint calls wait for an oracle ceiling.
- A question routes only when all its operands are reliable. The direct path stays as the fallback.
- Branch N (no SAM 3) is built and reported as the ablation that prices the tower.
- No bespoke kernel is warranted now. The batched routed decode is the throughput lever, and profiling comes before any kernel.
- Stop adding low-resolution in-video pointing rows, stop treating geometry-only selectors as identity fixes, and stop using the 0.035 accept threshold.

**Where they differ, and which side this plan adopts.**
| # | Point | d_fable | d_astra | Adopted, and why (evidence) |
|---|---|---|---|---|
| D1 | Baseline to beat | official gate, or the most confident detection | native gate >0.5 plus the 0.5 m ball selector | **d_astra.** Native gate plus selector is the strongest measured rule: +4.91 / -3.48 / +6.67 / +22.76, significant on 2 of 4 types (`hrp_infer/events/20261110T0840Z_RESULT_dev_oracle.md`). **This contradicts d_fable's claim** that geometric selectors win "1 of 4 at best". Every new selector is compared with this one at matched coverage, and ofs_e1 already carries the arm. |
| D2 | Disambiguation | the same LM answers yes/no on a 448 px crop of each candidate, plus a numbered sheet, fused by logistic | a click on a high-resolution re-read, checked against the masks | **d_fable as primary, d_astra's click as a feature.** A verify score exists for every candidate, needs one forward and no parse, and avoids the absent-frame failure, since base points at 33% of absent objects (`pt_fail/out/BLIND_SCORES.md`, absent 67.35% correct). Click or box agreement on the best four views enters the fusion as one feature (V3). |
| D3 | Resolution | does not bind at the object level: 70% of objects have a view over 5% of the frame | a GPU screen of base and T0 at three resolutions | **d_fable for budgeting.** Base scores 79.9% on views over 5% and 20.6% on views under 1% (BLIND_SCORES, 861 items). The screen is already queued as evalx pt_grid A/B' on base and costs no new allocation, so the T0 factorial is dropped. |
| D4 | Gates | object-level: on target >= 88%, accepted precision >= 93%, coverage >= 85% | identity >= 85% at >= 50% coverage, matched against the native gate | **Merged.** The deploy gate is >= 3 of 4 types with CI lower bound > 0 on the 53 non-tuning scenes, which both designs require. The object-level numbers are diagnostics, read as risk-coverage curves against D1. The frame-level 84/90 pointing gate goes, because it is label-limited: Astra scores 70.3 against base 69.6, and a 10 px dilation lifts base to 78 (`pt_fail/out/STATS.md`). |
| D5 | No-SAM branch | the LM's native boxes on the 4 frames ranked first by presence, with depth supplying the extent | a re-read click prompting MDG with dense V-C/G3T features (T08) | **d_fable first.** It needs no training, and X4 arm (b) prices it. T08 waits, because MDG plateaued at 0.72 in-mask and 0.81 null against bars of 0.84 and 0.90 (`mdg_build/STATUS.md`). |
| D6 | Geometry contract | not raised | V-C depth versus scaled G3T depth; one-view propagation; visible-surface centre graded apart from the OBB centre | **d_astra, as an addendum to X4.** GT 2D centroids land within 0.5 m of the OBB centre for only 65% of objects (hrp_infer 0840Z), so the centroid metric mixes surface error with amodal-centre error. |
