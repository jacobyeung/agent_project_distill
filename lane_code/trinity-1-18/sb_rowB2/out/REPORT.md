The build delivers 6,827 GT-recomputed replacements and removes all 11,926 source VSTI rows.
It refuses 5,099 sources; every refusal has a reason in REFUSALS.json. CHECKS.json and INDEPENDENT_CHECK.json pass.

| Family | Source rows | Any object outside k | No object at k | Replacements | Missing GT |
|---|---:|---:|---:|---:|---:|
| camera_obj_rel_dist_v1 | 1951 | 1950 | 1722 | 814 | 1136 |
| camera_obj_rel_dist_v2 | 1983 | 1980 | 1805 | 1142 | 807 |
| camera_obj_rel_dist_v3 | 1998 | 1983 | 1844 | 763 | 619 |
| obj_obj_relative_pos_lr | 1998 | 1980 | 1789 | 1388 | 599 |
| obj_obj_relative_pos_nf | 2000 | 1985 | 1846 | 1397 | 589 |
| obj_obj_relative_pos_ud | 1996 | 1986 | 1873 | 1323 | 670 |

The audit prints ten source question/options/trace examples per family in EXAMPLES60.md.
Each replacement fixes its camera and every object comparison to the queried slot k. The first frame mention says “of 32”.
The trace uses N’s qualitative Step grammar. GT_FACTS.jsonl records numeric distances, bearings, heights, poses, and independent computations.
Distance means camera centre to the closest GT OBB point. Left/right uses camera bearing; up/down uses the camera’s gravity-aligned level horizon.
A location relative to the camera does not assert that an object is visible in that frame. Frame-k visibility shares remain in the facts.

| Family | Entire source before | Admitted sources before | After |
|---|---|---|---|
| camera_obj_rel_dist_v1 | A:491, B:484, C:489, D:487 | A:214, B:195, C:190, D:215 | A:203, B:204, C:204, D:203 |
| camera_obj_rel_dist_v2 | A:664, B:657, C:662 | A:388, B:379, C:375 | A:381, B:380, C:381 |
| camera_obj_rel_dist_v3 | A:999, B:999 | A:384, B:379 | A:381, B:382 |
| obj_obj_relative_pos_lr | A:998, B:1000 | A:689, B:699 | A:694, B:694 |
| obj_obj_relative_pos_nf | A:1000, B:1000 | A:695, B:702 | A:698, B:699 |
| obj_obj_relative_pos_ud | A:998, B:998 | A:647, B:676 | A:661, B:662 |

The option seed is 20261119. Every admitted source appears once. Counts differ by at most one where divisibility prevents exact equality.
PLAN.json fixes every family/position cell before rendering; the generator asserts every cell exactly and fails on a short cell.
Only qid, candidate_id, answer, target, question/options, and the provenance.sb_rowB2 addition may change. Media pins and other metadata are preserved.
QID_MAP.jsonl maps each emitted replacement. REMOVE.json is JSON Lines with exactly N’s five keys: pool, question_type, reason, row_key, scene.
REMOVE.provenance.json supplies hashes without changing N’s removal schema. INPUTS.json binds the source, kit, GT, and exclusion inputs.

N’s native direct pack and validators pass on all 11,926 sources and all 6,827 replacements.
The build uses the sealed W19 tree (seal 8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa). Ground-route packing does not apply to this direct-row schema.
The separate checker recomputes all 6,827 delivered answers from pinned rasters and checks each distance ordering.
GT recomputation changes 0 source semantic answers; option letters change when options move.
The room rule excludes K1 held-out, R0, withheld-80, dev-S1, and BENCH v2 rooms using their pinned authorities.
Unique qids/candidate_ids, one-use source limits, allowed field changes, removal coverage, and all frame-k citations pass.
The wording filter checks 4,849 unique held-out wordings from 1,219 local files/archive members.
It excludes normalized Levenshtein distance ≤0.05 (NFKC, casefold, whitespace; divide by maximum codepoint length).
It refuses 679 source rows before balancing, checking every deterministic option position. No held-out wording supplies a template.
The bounded edit-distance implementation passes 3,844 comparisons against an independent dynamic program.
READ30.md contains thirty complete rows, five per family. READ30_REVIEW.json records their review.

Counts and evidence are produced by these commands (CPU only, OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=1, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE=1):
`/scratch/jjyeung/envs/p1cpu/bin/python stage_inputs.py` resolves hash-identical GT and lists missing inputs.
`g++ -O3 -shared -fPIC wording_filter.cpp -o inputs/wording_filter.so` builds the exact bounded edit-distance checker.
`/scratch/jjyeung/envs/p1cpu/bin/python collect_wordings.py` records the exclusion-only wording corpus.
`/scratch/jjyeung/envs/p1cpu/bin/python build_rows.py` produces the audit, GT facts, row counts, position cells, replacements, mapping, and removal list.
`/scratch/jjyeung/envs/p1cpu/bin/python verify_rows.py` independently checks delivered geometry and transformations.
`/scratch/jjyeung/envs/p1cpu/bin/python check_wording_filter.py` produces the edit-distance test count.
`/scratch/jjyeung/envs/p1cpu/bin/python finish_delivery.py` writes this report and seals the archive; SHA256SUMS records its digest.

Not done: 4,420 rows lack 307 exact source-pinned rasters in the local mirror and have no replacement.
GT_REFUSALS.json lists every missing raster’s original path, expected mirror path, and expected SHA256. No GT, scene mapping, or answer was guessed.
This is a row-build delivery, not a training run or production-readiness claim. The kit’s seal does not authorize production.
No borderline revision-history prose is retained.
