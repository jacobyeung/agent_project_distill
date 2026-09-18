# Remaining training pool by dataset (REQ-20260917-232)

Read-only census. Sources: union registry `REGISTRY_UNION_r1315_1789741908782481196.json` (299 scene receipts,
verified dataset+scene_name by opening each `scene_receipt.json`), training membership
`membership/v2/train50k_scene_reuse_answer_free.jsonl` (50,000 rows; sha256 matched `MEMBERSHIP_SHA` in
`collector/training_assets.py`), and candidate preparer packages under
`/home/jjyeung/agent_project/agent/rounds/candidates/`. No path containing `offline_labels` or `answer_bank`
was opened. `TRAIN50K_SCENE_REUSE_MANIFEST.json` is not named anywhere in `training_assets.py` or the union
registry, so it was not opened.

## 1. Per-dataset table

| dataset | total scenes | total questions | admitted scenes | admitted questions | remaining scenes | remaining questions |
|---|---|---|---|---|---|---|
| adt | 32 | 8,094 | 0 | 0 | 32 | 8,094 |
| arkitscenes | 571 | 7,330 | 0 | 0 | 571 | 7,330 |
| procthor | 110 | 1,735 | 0 | 0 | 110 | 1,735 |
| s3dis | 38 | 328 | 0 | 0 | 38 | 328 |
| scannet | 234 | 12,662 | 155 | 8,656 | 79 | 4,006 |
| scannetppv2 | 162 | 19,851 | 144 | 17,712 | 18 | 2,139 |
| **total** | **1,147** | **50,000** | **299** | **26,368** | **848** | **23,632** |

Admitted totals (299 scenes / 26,368 questions) match the census exactly. All 299 admitted scenes are
scannet or scannetppv2; adt, arkitscenes, procthor and s3dis are 0% admitted.

Remaining question-type histogram (from the membership rows whose scene is not in the admitted set):

| dataset | object_abs_distance | object_size_estimation | object_rel_direction_medium | object_rel_distance | object_counting | room_size_estimation | obj_appearance_order |
|---|---|---|---|---|---|---|---|
| adt | 1,593 | 860 | 3,984 | 1,593 | 64 | 0 | 0 |
| arkitscenes | 1,090 | 1,207 | 2,710 | 1,243 | 575 | 505 | 0 |
| procthor | 215 | 211 | 580 | 198 | 210 | 109 | 212 |
| s3dis | 48 | 66 | 86 | 24 | 69 | 35 | 0 |
| scannet | 487 | 259 | 2,029 | 922 | 141 | 72 | 96 |
| scannetppv2 | 299 | 101 | 863 | 549 | 64 | 17 | 246 |

## 2. Sealed preparer coverage per remaining dataset

Packages under `agent/rounds/candidates/` matching `r1313_vsi_distill_gt_training*`: `..._prep_v2`,
`..._scannet_v1`, `..._scannet_v2`.

| dataset (remaining scenes) | sealed preparer package | sealed? |
|---|---|---|
| scannet (79 remaining) | `r1313_vsi_distill_gt_training_scannet_v2` | Yes — `CONTRACT.json` carries a sha256 per source file and its own contract sha256 (`a1b6ce4c38862ac...`), used by REQ-232 to materialize the 155 already-admitted scannet scenes at 201.37 scenes/hour |
| scannetppv2 (18 remaining) | `r1313_vsi_distill_gt_training_prep_v2` | Yes — `PREP_CONTRACT.json` carries per-source-file sha256 and a `source_contract` sha256; `ready_prep_v2/REGISTRY_55.json` shows all 55 of its prepared receipts are dataset `scannetppv2` |
| adt (32 remaining) | none found | — |
| arkitscenes (571 remaining) | none found | — |
| procthor (110 remaining) | none found | — |
| s3dis (38 remaining) | none found | — |

`r1313_vsi_distill_gt_training_scannet_v1` has a `README.md` and `SCANNET_CONVENTION.md` but no
`CONTRACT.json` in its directory listing — not sealed. It is the same generation that the REQ-232 brief says
"the v2 re-verification refused every v1 materialization." Both `scannet_v2` and `prep_v2` are generic,
per-scene preparers (`prepare_gt_scene.py prepare --scene <id> ...`), so each could in principle also process
its dataset's *remaining* scenes, but nothing in the union registry shows that having happened yet.

## 3. Raw-source availability for the largest remaining dataset

By remaining question volume the largest remaining dataset is **adt** (8,094 remaining questions, 32 scenes,
0% admitted); by remaining scene count the largest is arkitscenes (571 scenes). Both were checked against the
only source-root convention named in the read inputs: training membership rows carry a `video` field of the
form `<dataset>/<scene>.mp4` (confirmed on an adt row: `adt/ADT_Apartment_release_multiuser_party_seq139_M1292_preview_rgb.mp4`),
and an admitted scannet scene's `frames_receipt.json` resolves that same pattern to an absolute root,
`/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/media/<dataset>/<scene>.mp4`.

A plain `ls` of `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/media/` lists only three
entries: `s3dis`, `scannet`, `scannetppv2`. There is no `adt` or `arkitscenes` entry, so the source root the
union registry lineage names does not exist yet for either dataset. Three sample remaining adt scene ids —
`ADT_Apartment_release_decoration_seq133_M1292_preview_rgb`, `..._seq135_...`, `..._seq138_...` — therefore
have no directory or file to check under that root; none of their raw assets are staged. No preparer package
or receipt names any other source root for adt or arkitscenes, so no further raw-source path was available to
check within the read-only scope of this task.

## 4. Observations

Every dataset in the 50,000-question membership pool still has an unadmitted remainder, and four of the six
datasets — adt, arkitscenes, procthor, s3dis — have zero admitted scenes at all. The two datasets that carry
admissions, scannet and scannetppv2, are also the only two with a sealed preparer package, and each preparer
was built and proven on exactly the scenes that ended up admitted (155 scannet scenes via `scannet_v2`, and a
scannetppv2 batch via `prep_v2`, per `ready_prep_v2/REGISTRY_55.json`). adt carries the largest remaining
question count of any dataset (8,094, driven mostly by `object_rel_direction_medium` questions) despite having
the fewest total scenes among the unadmitted datasets, while arkitscenes carries the most remaining scenes
(571) but a comparatively thin 7,330 total questions across them. The `media/<dataset>/` root that the
membership and admitted receipts point to has no entry for adt, arkitscenes, or procthor, matching their
complete lack of preparer packages and admissions. The union registry's 299 receipts trace to four
provenance groups by path — a single pilot scene, a five-scene `additional_top10_v1` batch, 138
`materialization_v2` receipts, and the 155-scene REQ-232 rematerialization — and the first three sum to
exactly 144, the admitted scannetppv2 count, while the REQ-232 batch alone equals the admitted scannet count
of 155; every one of those 299 receipts is scannet or scannetppv2, so nothing in the union registry's
history has ever touched adt, arkitscenes, procthor, or s3dis.
