predicted-mask paired route table

released labels; primary stratum; raw program; no-answer=0; direct fallback descriptive only.

Pairs: 1086 of 1086 eligible direct items; 0 missing program/GT rows. Room percentile bootstrap: 10,000 draws, seed 20261112.

| Dataset | Type | Items / rooms | Direct % | Program % | Difference pp [95% CI] | Rule verdict* |
|---|---|---:|---:|---:|---|---|
| All | object_abs_distance | 150 / 46 | 38.9 | 46.9 | +8.1 [+0.9, +16.9] | route |
| All | object_counting | 150 / 49 | 58.4 | 44.2 | -14.2 [-24.6, -4.9] | direct |
| All | object_rel_direction_easy | 150 / 36 | 91.3 | 70.7 | -20.7 [-34.7, -8.7] | direct |
| All | object_rel_direction_hard | 150 / 38 | 78.7 | 68.7 | -10.0 [-19.8, -1.4] | direct |
| All | object_rel_direction_medium | 150 / 36 | 88.7 | 61.3 | -27.3 [-41.9, -14.3] | direct |
| All | object_rel_distance | 150 / 35 | 72.0 | 44.0 | -28.0 [-40.3, -16.4] | direct |
| All | object_size_estimation | 150 / 59 | 68.1 | 60.5 | -7.6 [-14.5, -0.9] | direct |
| All | room_size_estimation | 36 / 9 | 55.6 | 62.2 | +6.7 [-14.4, +25.0] | undecided |
| arkitscenes | object_abs_distance | 47 / 19 | 34.7 | 52.8 | +18.1 [+6.6, +29.1] | route |
| arkitscenes | object_counting | 47 / 16 | 62.3 | 55.1 | -7.2 [-25.3, +8.4] | undecided |
| arkitscenes | object_rel_direction_easy | 41 / 14 | 95.1 | 87.8 | -7.3 [-20.0, +0.0] | undecided |
| arkitscenes | object_rel_direction_hard | 48 / 15 | 77.1 | 79.2 | +2.1 [-14.6, +14.3] | undecided |
| arkitscenes | object_rel_direction_medium | 40 / 13 | 90.0 | 85.0 | -5.0 [-21.2, +10.4] | undecided |
| arkitscenes | object_rel_distance | 18 / 6 | 66.7 | 44.4 | -22.2 [-60.0, +3.6] | undecided |
| arkitscenes | object_size_estimation | 76 / 28 | 75.4 | 63.2 | -12.2 [-21.5, -3.3] | direct |
| scannet | object_abs_distance | 30 / 8 | 43.7 | 48.7 | +5.0 [-3.4, +32.7] | undecided |
| scannet | object_counting | 53 / 13 | 57.0 | 45.7 | -11.3 [-30.8, +2.1] | undecided |
| scannet | object_rel_direction_easy | 37 / 7 | 86.5 | 75.7 | -10.8 [-42.1, +0.0] | undecided |
| scannet | object_rel_direction_hard | 28 / 6 | 85.7 | 75.0 | -10.7 [-25.0, -3.7] | direct |
| scannet | object_rel_direction_medium | 23 / 7 | 91.3 | 65.2 | -26.1 [-66.7, -8.3] | direct |
| scannet | object_rel_distance | 41 / 9 | 73.2 | 63.4 | -9.8 [-34.1, +11.9] | undecided |
| scannet | object_size_estimation | 32 / 11 | 55.9 | 60.0 | +4.1 [-8.1, +17.2] | undecided |
| scannet | room_size_estimation | 36 / 9 | 55.6 | 62.2 | +6.7 [-14.4, +25.0] | undecided |
| scannetppv2 | object_abs_distance | 73 / 19 | 39.6 | 42.5 | +2.9 [-8.1, +15.3] | undecided |
| scannetppv2 | object_counting | 50 / 20 | 56.2 | 32.4 | -23.8 [-39.8, -6.7] | direct |
| scannetppv2 | object_rel_direction_easy | 72 / 15 | 91.7 | 58.3 | -33.3 [-51.4, -12.3] | direct |
| scannetppv2 | object_rel_direction_hard | 74 / 17 | 77.0 | 59.5 | -17.6 [-33.3, -5.3] | direct |
| scannetppv2 | object_rel_direction_medium | 87 / 16 | 87.4 | 49.4 | -37.9 [-60.3, -18.2] | direct |
| scannetppv2 | object_rel_distance | 91 / 20 | 72.5 | 35.2 | -37.4 [-51.2, -23.7] | direct |
| scannetppv2 | object_size_estimation | 42 / 20 | 64.3 | 56.2 | -8.1 [-21.9, +5.6] | undecided |

*Route only when the interval is strictly above zero; direct only when strictly below; zero-inclusive intervals are undecided. Room counts disclose low-support and degenerate intervals.

Loss decomposition is unavailable for the GT stand-in. The source GT pricing aligned tower pose to GT by yaw/translation. The deployment kit uses raw exported coordinates; voxel bins and floor cells can change under this alignment (see REPLAY_PARITY.json).
