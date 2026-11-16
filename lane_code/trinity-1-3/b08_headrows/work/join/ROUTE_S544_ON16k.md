predicted-mask paired route table

released labels; primary stratum; raw program; no-answer=0; direct fallback descriptive only.

Pairs: 1086 of 1086 eligible direct items; 0 missing program/GT rows. Room percentile bootstrap: 10,000 draws, seed 20261112.

| Dataset | Type | Items / rooms | Direct % | Program % | Difference pp [95% CI] | Rule verdict* |
|---|---|---:|---:|---:|---|---|
| All | object_abs_distance | 150 / 46 | 4.1 | 46.9 | +42.8 [+34.4, +50.8] | route |
| All | object_counting | 150 / 49 | 62.8 | 44.2 | -18.6 [-29.7, -8.9] | direct |
| All | object_rel_direction_easy | 150 / 36 | 91.3 | 70.7 | -20.7 [-31.2, -11.7] | direct |
| All | object_rel_direction_hard | 150 / 38 | 84.0 | 68.7 | -15.3 [-26.5, -4.9] | direct |
| All | object_rel_direction_medium | 150 / 36 | 89.3 | 61.3 | -28.0 [-41.7, -15.6] | direct |
| All | object_rel_distance | 150 / 35 | 70.7 | 44.0 | -26.7 [-40.0, -14.0] | direct |
| All | object_size_estimation | 150 / 59 | 68.7 | 60.5 | -8.2 [-15.1, -1.3] | direct |
| All | room_size_estimation | 36 / 9 | 8.9 | 62.2 | +53.3 [+30.0, +73.2] | route |
| arkitscenes | object_abs_distance | 47 / 19 | 4.3 | 52.8 | +48.5 [+34.9, +61.0] | route |
| arkitscenes | object_counting | 47 / 16 | 69.6 | 55.1 | -14.5 [-33.3, +0.0] | undecided |
| arkitscenes | object_rel_direction_easy | 41 / 14 | 95.1 | 87.8 | -7.3 [-16.2, +0.0] | undecided |
| arkitscenes | object_rel_direction_hard | 48 / 15 | 81.2 | 79.2 | -2.1 [-21.4, +13.2] | undecided |
| arkitscenes | object_rel_direction_medium | 40 / 13 | 90.0 | 85.0 | -5.0 [-15.4, +6.9] | undecided |
| arkitscenes | object_rel_distance | 18 / 6 | 50.0 | 44.4 | -5.6 [-44.4, +18.8] | undecided |
| arkitscenes | object_size_estimation | 76 / 28 | 76.6 | 63.2 | -13.4 [-23.0, -3.7] | direct |
| scannet | object_abs_distance | 30 / 8 | 2.0 | 48.7 | +46.7 [+23.8, +66.7] | route |
| scannet | object_counting | 53 / 13 | 58.7 | 45.7 | -13.0 [-36.9, +1.8] | undecided |
| scannet | object_rel_direction_easy | 37 / 7 | 94.6 | 75.7 | -18.9 [-42.1, -9.1] | direct |
| scannet | object_rel_direction_hard | 28 / 6 | 89.3 | 75.0 | -14.3 [-27.3, +0.0] | undecided |
| scannet | object_rel_direction_medium | 23 / 7 | 91.3 | 65.2 | -26.1 [-66.7, -8.3] | direct |
| scannet | object_rel_distance | 41 / 9 | 63.4 | 63.4 | +0.0 [-12.7, +16.7] | undecided |
| scannet | object_size_estimation | 32 / 11 | 54.4 | 60.0 | +5.6 [-3.5, +20.9] | undecided |
| scannet | room_size_estimation | 36 / 9 | 8.9 | 62.2 | +53.3 [+30.0, +73.2] | route |
| scannetppv2 | object_abs_distance | 73 / 19 | 4.9 | 42.5 | +37.5 [+25.9, +49.6] | route |
| scannetppv2 | object_counting | 50 / 20 | 60.8 | 32.4 | -28.4 [-42.4, -13.3] | direct |
| scannetppv2 | object_rel_direction_easy | 72 / 15 | 87.5 | 58.3 | -29.2 [-44.9, -12.7] | direct |
| scannetppv2 | object_rel_direction_hard | 74 / 17 | 83.8 | 59.5 | -24.3 [-42.3, -9.1] | direct |
| scannetppv2 | object_rel_direction_medium | 87 / 16 | 88.5 | 49.4 | -39.1 [-60.0, -20.0] | direct |
| scannetppv2 | object_rel_distance | 91 / 20 | 78.0 | 35.2 | -42.9 [-58.6, -27.9] | direct |
| scannetppv2 | object_size_estimation | 42 / 20 | 65.5 | 56.2 | -9.3 [-23.1, +4.9] | undecided |

*Route only when the interval is strictly above zero; direct only when strictly below; zero-inclusive intervals are undecided. Room counts disclose low-support and degenerate intervals.

Loss decomposition is unavailable for the GT stand-in. The source GT pricing aligned tower pose to GT by yaw/translation. The deployment kit uses raw exported coordinates; voxel bins and floor cells can change under this alignment (see REPLAY_PARITY.json).
