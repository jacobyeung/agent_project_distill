# Repeat comparison

run1 `kit/r1/returned/0.gz`  
run2 `kit/r1/returned/0.gz`  
T1 `/scratch/jjyeung/orch_n30/cont_ops24_c/cap/t1.gz`


## run2 vs run1 (max / median over captures)

| dataset | n | translation m | rotation deg | K abs | scale abs | depth m |
|---|---|---|---|---|---|---|
| scannet | 11 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| scannetppv2 | 19 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| arkitscenes | 30 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| all | 60 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

Worst captures: scannet translation: scannet/scene0166_00 (0), scannet/scene0166_02 (0); scannet rotation: scannet/scene0166_00 (0), scannet/scene0166_02 (0); scannetppv2 translation: scannetppv2/0c7962bd64 (0), scannetppv2/17c5e6a336 (0); scannetppv2 rotation: scannetppv2/0c7962bd64 (0), scannetppv2/17c5e6a336 (0); arkitscenes translation: arkitscenes/41069053 (0), arkitscenes/41069054 (0); arkitscenes rotation: arkitscenes/41069053 (0), arkitscenes/41069054 (0)

## run1 vs T1

| dataset | n | translation m | rotation deg | K abs | scale abs |
|---|---|---|---|---|---|
| scannet | 11 | 0.00749 / 0.00117 | 0.0882 / 0.0399 | 0.137 / 0.109 | 9.16e-05 / 2.26e-05 |
| scannetppv2 | 19 | 0.0102 / 0.00277 | 0.0937 / 0.0598 | 0.198 / 0.13 | 1.24e-04 / 5.05e-05 |
| arkitscenes | 30 | 0.141 / 0.00709 | 1.44 / 0.12 | 0.322 / 0.164 | 2.27e-04 / 8.34e-05 |
| all | 60 | 0.141 / 0.00351 | 1.44 / 0.0636 | 0.322 / 0.137 | 2.27e-04 / 5.81e-05 |

Worst captures: scannet translation: scannet/scene0320_01 (0.00749), scannet/scene0515_00 (0.00216); scannet rotation: scannet/scene0320_01 (0.0882), scannet/scene0261_02 (0.0563); scannetppv2 translation: scannetppv2/7e7cd69a59 (0.0102), scannetppv2/99a2503d63 (0.00529); scannetppv2 rotation: scannetppv2/ad562ce09b (0.0937), scannetppv2/e35232b92f (0.0811); arkitscenes translation: arkitscenes/41126645 (0.141), arkitscenes/41069053 (0.0769); arkitscenes rotation: arkitscenes/41126645 (1.44), arkitscenes/41291639 (1.12)

## run2 vs T1

| dataset | n | translation m | rotation deg | K abs | scale abs |
|---|---|---|---|---|---|
| scannet | 11 | 0.00749 / 0.00117 | 0.0882 / 0.0399 | 0.137 / 0.109 | 9.16e-05 / 2.26e-05 |
| scannetppv2 | 19 | 0.0102 / 0.00277 | 0.0937 / 0.0598 | 0.198 / 0.13 | 1.24e-04 / 5.05e-05 |
| arkitscenes | 30 | 0.141 / 0.00709 | 1.44 / 0.12 | 0.322 / 0.164 | 2.27e-04 / 8.34e-05 |
| all | 60 | 0.141 / 0.00351 | 1.44 / 0.0636 | 0.322 / 0.137 | 2.27e-04 / 5.81e-05 |

Worst captures: scannet translation: scannet/scene0320_01 (0.00749), scannet/scene0515_00 (0.00216); scannet rotation: scannet/scene0320_01 (0.0882), scannet/scene0261_02 (0.0563); scannetppv2 translation: scannetppv2/7e7cd69a59 (0.0102), scannetppv2/99a2503d63 (0.00529); scannetppv2 rotation: scannetppv2/ad562ce09b (0.0937), scannetppv2/e35232b92f (0.0811); arkitscenes translation: arkitscenes/41126645 (0.141), arkitscenes/41069053 (0.0769); arkitscenes rotation: arkitscenes/41126645 (1.44), arkitscenes/41291639 (1.12)

## run2 vs run1 within T1 bounds (twice max T1 repeat deviation): **True**

| field | bound | run2-run1 max | worst capture | captures over bound |
|---|---|---|---|---|
| K | 0.158 | 0 | arkitscenes/41069053 | 0 |
| camera_to_world_metric | 0.00372 | 0 | arkitscenes/41069053 | 0 |
| camera_to_world_unscaled | 0.00136 | 0 | arkitscenes/41069053 | 0 |
| canvas_to_source | 0 | 0 | arkitscenes/41069053 | 0 |
| scale | 4.29e-05 | 0 | arkitscenes/41069053 | 0 |

Checks: captures_aligned=60, t1_items_with_geometry=149, run1_vs_t1_equals_embedded_row_parity=True, run1_vs_t1_equals_parity_receipt_items=True, run1_vs_t1_equals_parity_receipt_maxima=True, run1_parity_bounds_equal_t1_repeat_bounds=True, run2_vs_t1_equals_embedded_row_parity=True, run2_vs_t1_equals_parity_receipt_items=True, run2_vs_t1_equals_parity_receipt_maxima=True, run2_parity_bounds_equal_t1_repeat_bounds=True
