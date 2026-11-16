# ReVSI development set and ReVSI contamination check (2026-11-08)

ReVSI joins VSI-500 as a development benchmark. Its scenes do not occur in any training source of the coming runs, and the new membership is a seeded subset of the official 999 questions at the 32-frame tier.

## Contamination: zero overlap in every source
I matched ReVSI's 381 scenes by native id, by rung-1 opaque token (`'v' + sha256('rung1 scene <native>/<scene>')[:12]`) and by ScanNet physical group (`sceneNNNN`). The scenes are ScanNet 92, ScanNet++ 48, ARKit 171, 3RScan 46 and MultiScan 24; 222 of them are also VSI-Bench scenes. Opaque tokens were resolved by enumeration: all ARKit tokens and 98-99% of ScanNet tokens resolved.

| Source | Scenes checked | ScanNet | ScanNet++ | ARKit |
|---|---|---:|---:|---:|
| C1 pose rows (A1 `e84d901c` rows `6f27ae81`, 321,152 rows) | plan 3,540 recordings + A0 1,187 + division `4c230a7e` (4,265; this is the pin in the AWS receipt) | 0 | 0 | 0 |
| C1-r dense clip plan (p10) | 3,540 recordings (the same A1 plan) | 0 | 0 | 0 |
| derivgen traces | row shards, the 120 extra scenes, every non-test file and shard | 0 | 0 | 0 |
| weak_data canonical-trace packs | 7 packs + 2 reserves, 2,632 scenes | 0 | 0 | 0 |
| mixdata streams | vqa_sel_v1-v3 and pointing_try1, 2,229 scenes (filtered to division `4c230a7e`) | 0 | 0 | 0 |

None of our sources contains 3RScan or MultiScan. A1 uses ARKit Training and ScanNet train recordings, while ReVSI uses the validation splits. Details: `/scratch/jjyeung/orch_cd/revsi_dev/CONTAMINATION_REVSI_20261108.json`.

## Gate fix (lanes apply it; no code was edited)
- Exclusion list: `REVSI_SCENE_EXCLUSIONS_v1.json` (sha256 `9a8e1211...`). It has `scenes` with 311 `d1|d2|d3/<native>` entries, `physical_groups`, `rung1_tokens` and `other_corpora` (3RScan, MultiScan). `REVSI_SCENES_v1.tsv` holds the same scenes as a two-column TSV in vsi288 style.
- A1/C1 builders (`repo_af` and its descendants, `student_pilot/recording_pose.py::load_authorities`): this is the only gate that lacks ReVSI. Add the list as a pinned `extra_benchmarks` entry, and add the same pin to the admission policy's `required_exclusion_lists`. The loader accepts the file as is (`listed_scenes` gives 714 keys). C1-r and the mixdata `build_stream` inherit the A1 division, so they need the same pin at their next division or plan rebuild.
- The P1c-b, weak_data and derivgen authority (`weak_data/inputs/EXCLUDED_GROUPS.json`, 606 groups) already covers all 311 ReVSI ScanNet, ScanNet++ and ARKit scenes, so those builders need no change.
- `mix_trainer_roots_x.py` (BENCHMARKS table) and every new mix's SCENE_CHECK should load the list too.

## Development subset
- Rule: use the official tiny ids present at the 32-frame tier (999). A category with at most 71 questions is taken whole; a larger one gets a seeded draw (seed 20261108) in proportion to `question_type`. No question comes from outside the 999.
- The 999 has only 37 room_size, 63 route and 68 rel_direction questions, so equal sizes of 71 are impossible. Primary membership `MEMBERSHIP_REVSI_DEV_cap71.json`: **452 questions** (71 each for counting, size, abs_distance and rel_distance; 68 rel_direction; 63 route; 37 room_size), 213 scenes, qid sha256 `a2180b92...`. Alternative `..._cap83.json`: 500 questions with a cap of 83.
- Visibility is a flag only (`visible_32`): every queried object is visible under ReVSI's `obj_visibility.json` `visibility_32`. Results: 350 true, 2 false (rel_distance), and 100 not applicable (route and room_size have no queried objects).
- Limits: the visibility flag is not a re-verification of the labels, and room_size has only 37 questions, which makes it noisy.
- Files are in `/scratch/jjyeung/orch_cd/revsi_dev/` and `/data2/jjyeung/agent_project_data/revsi_dev_20261108/`: MEMBERSHIP, META (counts and input sha256s), QIDS, `build_membership.py`.

