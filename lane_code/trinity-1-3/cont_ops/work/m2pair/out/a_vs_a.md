B minus A; paired room bootstrap, 10,000 draws, seed 20261115, 95% interval.
Rates use fractions. Displacement uses metres; rotation uses degrees.

**camera_displacement** — A: 150 items/450 reads; B: 150 items/450 reads; 150 paired items.

| Mode / metric | A | B | B−A [95% CI] | Differs |
|---|---:|---:|---:|:---:|
| none / M1.call_rate | 1.0000 | 1.0000 | 0.0000 [0.0000, 0.0000] | no |
| none / M1.exact | 1.0000 | 1.0000 | 0.0000 [0.0000, 0.0000] | no |
| none / M1.answer_before_first_call | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | no |
| none / M2.absolute_error_m | 0.6049 | 0.6049 | 0.0000 [0.0000, 0.0000] | no |
| none / M2.task_accuracy | 0.4720 | 0.4720 | 0.0000 [0.0000, 0.0000] | no |
| scale_translation:0.5 / M3.follow | 1.0000 | 1.0000 | 0.0000 [0.0000, 0.0000] | no |
| scale_translation:0.5 / M3.stick | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | no |
| scale_translation:2 / M3.follow | 1.0000 | 1.0000 | 0.0000 [0.0000, 0.0000] | no |
| scale_translation:2 / M3.stick | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | no |

**camera_movement_direction** — A: 150 items/300 reads; B: 150 items/300 reads; 150 paired items.

| Mode / metric | A | B | B−A [95% CI] | Differs |
|---|---:|---:|---:|:---:|
| none / M1.call_rate | 1.0000 | 1.0000 | 0.0000 [0.0000, 0.0000] | no |
| none / M1.exact | 1.0000 | 1.0000 | 0.0000 [0.0000, 0.0000] | no |
| none / M1.answer_before_first_call | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | no |
| none / M2.correct | 0.7533 | 0.7533 | 0.0000 [0.0000, 0.0000] | no |
| none / M2.task_accuracy | 0.7533 | 0.7533 | 0.0000 [0.0000, 0.0000] | no |
| rotate_translation:180 / M3.follow | 1.0000 | 1.0000 | 0.0000 [0.0000, 0.0000] | no |
| rotate_translation:180 / M3.stick | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | no |

**camera_rotation** — A: 150 items/300 reads; B: 150 items/300 reads; 150 paired items.

| Mode / metric | A | B | B−A [95% CI] | Differs |
|---|---:|---:|---:|:---:|
| negate_turn / M3.follow | 1.0000 | 1.0000 | 0.0000 [0.0000, 0.0000] | no |
| negate_turn / M3.stick | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | no |
| none / M1.call_rate | 1.0000 | 1.0000 | 0.0000 [0.0000, 0.0000] | no |
| none / M1.exact | 1.0000 | 1.0000 | 0.0000 [0.0000, 0.0000] | no |
| none / M1.answer_before_first_call | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | no |
| none / M2.error_deg | 17.9000 | 17.9000 | 0.0000 [0.0000, 0.0000] | no |
| none / M2.task_accuracy | 0.4273 | 0.4273 | 0.0000 [0.0000, 0.0000] | no |

JSON includes per-side intervals, scoring denominators, and per-read measurements.
M2 averages scored calls within each item. M3 uses each side’s eligible reads.
An interval is unavailable if either mean is undefined on any room draw.
