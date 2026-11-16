# Additive numeric tolerance tiers

Census stamp: `1789755795496244761`.
Tool git commit: `uncommitted; patch required`; base: `7a002694b1a14238a673ee59ed15506c31ba6ffa`.
Tool SHA256: `915d770f1214bbd059cae1c7413c2efb8e4c2e9841e05011b2642b18e71c6139`.
DECISIONS.json SHA256: `240cef5b6e20110640f72cea0d5589edf17be07111dc5eea5984f75219101413`.

Thresholds are cumulative. Additional traces must satisfy the recorded census completion and perception conditions; strict accepted decisions remain unchanged.
The census grades all rows without options numerically (collector/census.py:47-61), including exact integer counts (55-56). Observed membership types: object_abs_distance, object_counting, object_size_estimation, room_size_estimation.
Census line 47: `if row.get('options'):`; line 56: `return not suffix and pred.is_integer() and target.is_integer() and pred==target,'exact_integer'`; line 60: `correct=target>0 and abs(pred-target)/target <= .05+1e-12`.
The tool uses census.grade() parsing and unit checks. Missing, invalid, unit-incompatible, and zero-denominator answers have null relative error and false tier flags. Counting retains integer and suffix constraints.

| Question type | Finalized | Strict accepted | Additional ≤10% | Additional ≤15% | Additional ≤25% |
| --- | ---: | ---: | ---: | ---: | ---: |
| obj_appearance_order | 53 | 53 | 0 | 0 | 0 |
| object_abs_distance | 103 | 50 | 15 | 22 | 29 |
| object_counting | 26 | 22 | 0 | 0 | 1 |
| object_rel_direction_medium | 377 | 350 | 0 | 0 | 0 |
| object_rel_distance | 207 | 139 | 0 | 0 | 0 |
| object_size_estimation | 37 | 7 | 7 | 10 | 21 |
| room_size_estimation | 6 | 1 | 0 | 0 | 2 |

Strict blended acceptance: 622/809 (76.89%).
Blended acceptance at ≤10%: 644/809 (79.60%).
Blended acceptance at ≤15%: 654/809 (80.84%).
Blended acceptance at ≤25%: 675/809 (83.44%).
