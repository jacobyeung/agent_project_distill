# NF: banked step-544 dev-S1 read replayed with K5 A2 cameras

Every line: replay holds the model text fixed, so the difference is a lower bound.

## Reproduction of the banked read
- Camera calls re-served from the banked geometry: 450/450 byte-equal
- Camera items re-scored from recorded text: 450/450; answers re-derived by the copy/written rule: 450/450
- 834/842 is the R8 reconstruction (cont_ops24_c/gbuild/analyze_round8.py) of the held-out camera reads 173258/173412/173234 from distance-read cameras, not of this read; read 170056 exports its served geometry per capture, so its camera calls replay from the exported tensors directly (b04 token replay: 927/927 calls, tests/replay_170056.py).

## Substitution
- {"direct": 0, "relative": 52, "kept": 0, "camera_captures": 52, "captures_banked_cameras_equal_A1_cu_bitwise": 0}

## Per type (points; paired room bootstrap, 10000 draws, seed 20261120, 58 rooms)
| Type | Items | Banked % | Replay % | Replay - banked [95% CI] | Printed value changed | Rule read | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| camera_displacement | 150 | 82.333 | 82.333 | +0.000 [+0.000, +0.000] (lower bound) | 0 (0.0%) | yes | no option A needed |
| camera_rotation | 150 | 75.667 | 75.667 | +0.000 [+0.000, +0.000] (lower bound) | 0 (0.0%) | yes | no option A needed |
| camera_movement_direction | 150 | 94.667 | 94.667 | +0.000 [+0.000, +0.000] (lower bound) | 0 (0.0%) | yes | no option A needed |
| object_abs_distance | 150 | - | - | unmeasured | 0 items on 0 changed captures (0.0%, upper proxy) | yes | UNMEASURED by option B |
| room_size_estimation | 36 | - | - | unmeasured | 0 items on 0 changed captures (0.0%, upper proxy) | yes | UNMEASURED by option B |

- Movement direction with every answer held (strict text-fixed): +0.000 pts.

## Rule-read types (sources)
- camera_displacement: H3 (tower-arm camera harm rule) read at R1 steps 200 and 400; R1 stopped at step 400 on it (-0.73 pts)
- camera_rotation: H3 read at R1 steps 200 and 400
- camera_movement_direction: H3 read at R1 steps 200 and 400
- object_abs_distance: protected outcome "termination on the claimed arm" (capped distance reads <= 5/150) read at each R1 boundary
- room_size_estimation: R1 room gate registered (baseline: reader_r1 job 172456); a read of it is not evidenced in the records

Thresholds: |difference| >= 0.5 pts or changed share > 5% triggers option A on a rule-read type.
Runtime 3.3 s.
