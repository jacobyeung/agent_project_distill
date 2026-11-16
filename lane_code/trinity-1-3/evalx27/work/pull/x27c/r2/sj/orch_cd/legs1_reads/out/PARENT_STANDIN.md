no difference from the parent
INCOMPLETE: f17 dev-S1 comparison is missing
R3: INCOMPLETE: need f17 dev-S1 and paired dev-858 reads
Routed: INCOMPLETE: routed journals missing

| Type | LEG % | Parent % | Change (pp) | LEG caps/100 |
|---|---:|---:|---:|---:|
| object_abs_distance | 38.8667 | 38.8667 | +0.0000 | 0.00 |
| object_counting | 58.4000 | 58.4000 | +0.0000 | 0.00 |
| object_rel_direction_easy | 91.3333 | 91.3333 | +0.0000 | 0.00 |
| object_rel_direction_hard | 78.6667 | 78.6667 | +0.0000 | 0.00 |
| object_rel_direction_medium | 88.6667 | 88.6667 | +0.0000 | 0.00 |
| object_rel_distance | 72.0000 | 72.0000 | +0.0000 | 0.00 |
| object_size_estimation | 68.1333 | 68.1333 | +0.0000 | 0.00 |
| relative_count | 59.7122 | 59.7122 | +0.0000 | 0.00 |
| relative_size_object | 92.0000 | 92.0000 | +0.0000 | 0.00 |
| room_size_estimation | 55.5556 | 55.5556 | +0.0000 | 0.00 |
| route_planning | 33.3333 | 33.3333 | +0.0000 | 0.00 |

leg minus parent. Bootstrap over physical rooms; 10,000 draws, seed 17.

| Stratum / type | Items | Rooms | Difference (pp) | 95% interval (pp) |
|---|---:|---:|---:|---:|
| primary / overall | 1375 | 71 | +0.0000 | [+0.0000, +0.0000] |
| primary / object_abs_distance | 150 | 46 | +0.0000 | [+0.0000, +0.0000] |
| primary / object_counting | 150 | 49 | +0.0000 | [+0.0000, +0.0000] |
| primary / object_rel_direction_easy | 150 | 36 | +0.0000 | [+0.0000, +0.0000] |
| primary / object_rel_direction_hard | 150 | 38 | +0.0000 | [+0.0000, +0.0000] |
| primary / object_rel_direction_medium | 150 | 36 | +0.0000 | [+0.0000, +0.0000] |
| primary / object_rel_distance | 150 | 35 | +0.0000 | [+0.0000, +0.0000] |
| primary / object_size_estimation | 150 | 59 | +0.0000 | [+0.0000, +0.0000] |
| primary / relative_count | 139 | 24 | +0.0000 | [+0.0000, +0.0000] |
| primary / relative_size_object | 150 | 53 | +0.0000 | [+0.0000, +0.0000] |
| primary / room_size_estimation | 36 | 9 | +0.0000 | [+0.0000, +0.0000] |
| route_own_labels / overall | 150 | 40 | +0.0000 | [+0.0000, +0.0000] |
| route_own_labels / route_planning | 150 | 40 | +0.0000 | [+0.0000, +0.0000] |

Facing-away controls use own labels. Constant-answer rates map option letters back to meanings.

| Type | Away % | Forward % | Best away constant % | Best forward constant % |
|---|---:|---:|---:|---:|
| object_rel_direction_easy | 24.00 | 92.00 | 54.00 | 54.00 |

object_rel_direction_easy answer frequencies: {"away": {"left": 46.0, "right": 54.0}, "forward": {"left": 58.0, "right": 42.0}}
Paired outcomes: {"forward_0_away_0": 3, "forward_0_away_1": 1, "forward_1_away_0": 35, "forward_1_away_1": 11}
| object_rel_direction_hard | 6.00 | 86.00 | 36.00 | 36.00 |

object_rel_direction_hard answer frequencies: {"away": {"back-left": 2.0, "back-right": 14.0, "front-left": 44.0, "front-right": 40.0}, "forward": {"back-left": 16.0, "back-right": 14.0, "front-left": 34.0, "front-right": 36.0}}
Paired outcomes: {"forward_0_away_0": 6, "forward_0_away_1": 1, "forward_1_away_0": 41, "forward_1_away_1": 2}
| object_rel_direction_medium | 12.00 | 96.00 | 40.00 | 58.00 |

object_rel_direction_medium answer frequencies: {"away": {"left": 52.0, "right": 48.0}, "forward": {"back": 6.0, "left": 56.0, "right": 38.0}}
Paired outcomes: {"forward_0_away_0": 2, "forward_1_away_0": 42, "forward_1_away_1": 6}

The card parent 29.33% is ON16k. Primary decision protocol B2048 gives parent route 33.33%. Never mix these arms.
ON16k route scores: LEG 29.3333%, parent 29.3333%.
