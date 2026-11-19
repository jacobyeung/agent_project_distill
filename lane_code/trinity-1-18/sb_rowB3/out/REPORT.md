The kit delivers 8,186 truthful frame-k rows across all six VSTI families, from 6,827 unique store-v7 sources.
CHECKS.json, INDEPENDENT_CHECK.json, KIT_CHECK.json, and the thirty-row review pass. The build is CPU-only; no training ran.

| Family | Source census | Eligible sources | Delivered | All out of view | Per joint cell by stratum |
|---|---:|---:|---:|---:|---|
| camera_obj_rel_dist_v1 | 1951 | 814 | 1200 | 529 | tied:38, untied:37 |
| camera_obj_rel_dist_v2 | 1983 | 1142 | 1494 | 787 | tied:59, untied:107 |
| camera_obj_rel_dist_v3 | 1998 | 763 | 836 | 507 | tied:40, untied:169 |
| obj_obj_relative_pos_lr | 1998 | 1388 | 1428 | 562 | earlier:138, later:139, tied:80 |
| obj_obj_relative_pos_nf | 2000 | 1397 | 1636 | 958 | earlier:161, later:169, tied:79 |
| obj_obj_relative_pos_ud | 1996 | 1323 | 1592 | 991 | earlier:159, later:162, tied:77 |
Cell counts apply to every rank/semantic-answer × option-position combination within the named first-seen stratum.

Each queried object has exactly one in-view or out-of-view statement, then a relation to the frame-k camera, then the answer.
The visibility threshold is the source visibility_floor, 0.002. The first frame mention says “of 32”; all frame indices are in 1..32.
For an out-of-view object, use the latest qualifying recorded instance frame strictly before k; otherwise use the nearest recorded frame, preferring the earlier frame on a tie.
The trace labels this as a recorded-sighting reference and explicitly identifies references later in the clip. Source instances record first sightings, not a complete visibility history.
Relations come from geometry_values and are independently checked against pinned GT arrays. Camera distance is to the closest OBB point; left/right compares camera bearings; up/down compares gravity-aligned heights.
Camera geometry_values are sorted distances: the source trace supplies their label order, and independent GT confirms that association. No image region, mask, depth, or pose at k is invented.

| Family | Source option histogram before | Eligible-source histogram before | Delivered histogram after |
|---|---|---|---|
| camera_obj_rel_dist_v1 | A:491, B:484, C:489, D:487 | A:214, B:195, C:190, D:215 | A:300, B:300, C:300, D:300 |
| camera_obj_rel_dist_v2 | A:664, B:657, C:662 | A:388, B:379, C:375 | A:498, B:498, C:498 |
| camera_obj_rel_dist_v3 | A:999, B:999 | A:384, B:379 | A:418, B:418 |
| obj_obj_relative_pos_lr | A:998, B:1000 | A:689, B:699 | A:714, B:714 |
| obj_obj_relative_pos_nf | A:1000, B:1000 | A:695, B:702 | A:818, B:818 |
| obj_obj_relative_pos_ud | A:998, B:998 | A:647, B:676 | A:796, B:796 |

| Camera family | Source rank before | Eligible rank before | Delivered rank after |
|---|---|---|---|
| camera_obj_rel_dist_v1 | 1:665, 2:492, 3:391, 4:403 | 1:297, 2:199, 3:153, 4:165 | 1:300, 2:300, 3:300, 4:300 |
| camera_obj_rel_dist_v2 | 1:843, 2:582, 3:558 | 1:497, 2:324, 3:321 | 1:498, 2:498, 3:498 |
| camera_obj_rel_dist_v3 | 1:1111, 2:887 | 1:418, 2:345 | 1:418, 2:418 |
First-seen ranks sort by (first_seen, numeric instance id). Tied and untied rows are balanced separately; ties do not imply temporal precedence.
For untied camera rows, the earliest object wins exactly 1/4, 1/3, and 1/2 of the four-, three-, and two-object families. HISTOGRAMS.json also reports earliest-with-ties counts.
Each camera rank has equal A/B/C/D, A/B/C, or A/B counts within its tie stratum. Pair families balance both semantic directions and A/B within earlier/later/tied subject sightings.

| Relation family | Source semantic answers before | Eligible semantic answers before | Delivered semantic answers after |
|---|---|---|---|
| obj_obj_relative_pos_lr | Left:996, Right:1002 | Left:708, Right:680 | Left:714, Right:714 |
| obj_obj_relative_pos_nf | Far:1002, Near:998 | Far:692, Near:705 | Far:818, Near:818 |
| obj_obj_relative_pos_ud | Down:986, Up:1010 | Down:655, Up:668 | Down:796, Up:796 |
All 6,827 eligible sources are retained, including every eligible all-out-of-view source. The maximum source use is 3; use histogram: 1:5474, 2:1347, 3:6.
Repeated sources use distinct answer positions. PLAN.json fixes every first-seen/semantic/position cell; the generator and independent checker fail on a short cell.

N’s sealed W19 kit is used: 8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa. Loaded modules match TREE_SEAL.json.
Native direct pack and validators pass on all 11,926 sources and all 8,186 new rows. Independent GT checks cover 706 raster files and every emitted row.
Checks cover unique qids/candidate_ids, N’s candidate-id formula, room exclusions, source-use bounds, complete mapping, and field differences.
Permitted changes: qid, candidate_id, answer, target, student_input.question/options, and provenance.sb_rowB3. All media and remaining source fields stay identical.
The room rule excludes K1 held-out, R0, withheld-80, dev-S1, and BENCH v2 using their pinned authorities in INPUTS.json.
The wording filter checks 4,849 unique exclusion-only wordings from 1,219 pinned local inputs; it refuses 679 sources.
It rejects normalized Levenshtein distance ≤0.05 after NFKC, casefold, and whitespace normalization, divided by maximum codepoint length. All deterministic option permutations are checked.
The distance implementation passes 3,844 independent dynamic-program comparisons. No held-out wording supplies a template.
QID_MAP.jsonl maps original store qids and sb_rowB2 qids to every new qid. This kit replaces the sb_rowB2 kit; do not concatenate their rows.
REMOVE.json covers all 11,926 original store-v7 qids in N’s five-key JSONL n.json format. REMOVE.provenance.json carries its hashes without changing that schema.

Next-read gate: on the fixed 59 dev camera-item pairs from one room with different k whose true winner changes, the model’s top shared object must change on more than the step-200 baseline of 18 pairs.
Also report answer correctness and the evaluated denominator so random answer changes cannot count as improvement. This build does not measure the next-read gate.

Commands producing the reported counts (from this workspace; CUDA hidden, bytecode disabled, BLAS/OpenMP threads set to 1):
`/scratch/jjyeung/envs/p1cpu/bin/python build_rows.py` produces the census, filters, exact cells, both histograms, rows, mapping, and removal list.
`/scratch/jjyeung/envs/p1cpu/bin/python verify_rows.py` independently checks all geometry, visibility, sighting references, transformations, and identities.
`/scratch/jjyeung/envs/p1cpu/bin/python select_samples.py` selects thirty distinct sources for READ30.md; READ30_REVIEW.json records the agent’s review.
`/scratch/jjyeung/envs/p1cpu/bin/python check_wording_filter.py` produces the edit-distance comparison count.
`/scratch/jjyeung/envs/p1cpu/bin/python finish_delivery.py` asserts checks, writes this report, seals out/sb_rowB3.tar, verifies every archive member, and writes SHA256SUMS.

Not done: 4,420 source rows lack 307 exact pinned GT rasters. REFUSALS.json marks them MISSING and lists original paths, expected mirror paths, and hashes.
Full GT rasters and the sealed trainer tree remain external read-only inputs; their paths and hashes are recorded. No GT mapping, scene list, or proof was guessed.
The requested before/after histograms describe the build distributions, not model performance. No revision-history prose is retained.
