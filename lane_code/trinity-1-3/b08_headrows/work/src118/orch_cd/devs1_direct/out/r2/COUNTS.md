Each cell contains 1,525 items from the unchanged 2,136-item list. The cells exclude 600 unsupported items and 11 rooms without either label.

| Type | In each cell | Primary | Disagreement | Missing released | Released text unavailable |
|---|---:|---:|---:|---:|---:|
| object_abs_distance | 150 | 150 | 0 | 0 | 0 |
| object_counting | 150 | 150 | 0 | 0 | 0 |
| object_rel_direction_easy | 150 | 150 | 0 | 0 | 0 |
| object_rel_direction_hard | 150 | 150 | 0 | 0 | 0 |
| object_rel_direction_medium | 150 | 150 | 0 | 0 | 0 |
| object_rel_distance | 150 | 150 | 0 | 0 | 0 |
| object_size_estimation | 150 | 150 | 0 | 0 | 0 |
| relative_count | 139 | 139 | 0 | 0 | 0 |
| relative_size_object | 150 | 150 | 0 | 0 | 0 |
| room_size_estimation | 36 | 36 | 0 | 0 | 0 |
| route_planning | 150 | 0 | 0 | 150 | 0 |

Total: 1,375 primary; 0 disagreement; 150 missing released; 0 released text unavailable; 611 excluded. The retained cells cover 142 captures and 73 physical rooms.

All 889 ordinary MC items have released option text and agree by content. The 150 generated route items have canonical labels but no established released-dataset provenance. They remain in the unavailable report view. `EXCLUDED_MISSING_ROOM.jsonl` lists the 11 rooms without either label. `STRATA.jsonl` records all 2,136 fixed items.

The adapter preserves original `released_answer` and `released_options`, maps released content to `released_answer_in_options`, and uses that mapped letter for scoring. Unavailable rows use their canonical label for the kit score and return null released-label metrics. Numeric agreement uses the released-denominator 10% rule.
