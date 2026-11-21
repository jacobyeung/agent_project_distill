# K5 score

## Answers
```
{
 "q1_deterministic_orders_bit_equal": "yes",
 "default_orders": "orders agree",
 "q2_cost_ratio_of_means": 1.1538883156577047,
 "q2_cost_ratio_of_medians": 1.170822405970063,
 "deterministic_warn_only": {
  "D1": false,
  "D2": false
 },
 "strict_refusals": {}
}
```

## A1_vs_A2 (complete)
| dataset | compared | bit-equal | tower bit-equal | max t m | max rot deg | max K | max scale rel |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ScanNet | 29/29 | 29 | 29 | 0 | 2.41e-06 | 0 | 0 |
| ScanNet++ | 25/25 | 25 | 25 | 0 | 2.41e-06 | 0 | 0 |
| ARKit | 30/30 | 30 | 30 | 0 | 1.71e-06 | 0 | 0 |
| all | 84/84 | 84 | 84 | 0 | 2.41e-06 | 0 | 0 |

## D1_vs_D2 (complete)
| dataset | compared | bit-equal | tower bit-equal | max t m | max rot deg | max K | max scale rel |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ScanNet | 29/29 | 29 | 29 | 0 | 2.41e-06 | 0 | 0 |
| ScanNet++ | 25/25 | 25 | 25 | 0 | 2.09e-06 | 0 | 0 |
| ARKit | 30/30 | 30 | 30 | 0 | 2.09e-06 | 0 | 0 |
| all | 84/84 | 84 | 84 | 0 | 2.41e-06 | 0 | 0 |

## A1_vs_D1 (complete)
| dataset | compared | bit-equal | tower bit-equal | max t m | max rot deg | max K | max scale rel |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ScanNet | 29/29 | 0 | 0 | 1.23 | 27.3 | 1.91 | 0.00156 |
| ScanNet++ | 25/25 | 0 | 0 | 0.301 | 4.56 | 1.79 | 0.00264 |
| ARKit | 30/30 | 0 | 0 | 1.14 | 78.8 | 2.71 | 0.00915 |
| all | 84/84 | 0 | 0 | 1.23 | 78.8 | 2.71 | 0.00915 |

## A2_vs_D2 (complete)
| dataset | compared | bit-equal | tower bit-equal | max t m | max rot deg | max K | max scale rel |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ScanNet | 29/29 | 0 | 0 | 1.23 | 27.3 | 1.91 | 0.00156 |
| ScanNet++ | 25/25 | 0 | 0 | 0.301 | 4.56 | 1.79 | 0.00264 |
| ARKit | 30/30 | 0 | 0 | 1.14 | 78.8 | 2.71 | 0.00915 |
| all | 84/84 | 0 | 0 | 1.23 | 78.8 | 2.71 | 0.00915 |

## Capture-0 recompute
```
{
 "A1": {
  "status": "complete",
  "bit": true,
  "tower_bit": true,
  "translation_m": 0.0,
  "translation_unscaled": 0.0,
  "rotation_deg": 0.0,
  "K": 0.0,
  "scale": 0.0,
  "scale_rel": 0.0
 },
 "A2": {
  "status": "complete",
  "bit": true,
  "tower_bit": true,
  "translation_m": 0.0,
  "translation_unscaled": 0.0,
  "rotation_deg": 0.0,
  "K": 0.0,
  "scale": 0.0,
  "scale_rel": 0.0
 },
 "D1": {
  "status": "complete",
  "bit": true,
  "tower_bit": true,
  "translation_m": 0.0,
  "translation_unscaled": 0.0,
  "rotation_deg": 0.0,
  "K": 0.0,
  "scale": 0.0,
  "scale_rel": 0.0
 },
 "D2": {
  "status": "complete",
  "bit": true,
  "tower_bit": true,
  "translation_m": 0.0,
  "translation_unscaled": 0.0,
  "rotation_deg": 0.0,
  "K": 0.0,
  "scale": 0.0,
  "scale_rel": 0.0
 }
}
```
## A1 vs rank 1 dump
```
{
 "ScanNet": {
  "compared": 11,
  "K_bit": 11,
  "served_plane_bit": 11,
  "unscaled_bit": 4,
  "metric_fixed_bit": 4,
  "max_K": 0.0,
  "max_unscaled_translation": 2.225860458774576e-16,
  "max_unscaled_rotation_deg": 1.7075472925031877e-06,
  "max_metric_fixed_translation_m": 8.89045358334726e-16,
  "max_scale_vs_served_rel": 1.272897441519735e-05
 },
 "ScanNet++": {
  "compared": 19,
  "K_bit": 19,
  "served_plane_bit": 19,
  "unscaled_bit": 8,
  "metric_fixed_bit": 8,
  "max_K": 0.0,
  "max_unscaled_translation": 3.273110650186759e-16,
  "max_unscaled_rotation_deg": 2.4148365394514667e-06,
  "max_metric_fixed_translation_m": 2.560433633529891e-15,
  "max_scale_vs_served_rel": 3.07471041012014e-05
 },
 "ARKit": {
  "compared": 30,
  "K_bit": 30,
  "served_plane_bit": 30,
  "unscaled_bit": 8,
  "metric_fixed_bit": 8,
  "max_K": 0.0,
  "max_unscaled_translation": 4.558679027077474e-15,
  "max_unscaled_rotation_deg": 1.7075472925031877e-06,
  "max_metric_fixed_translation_m": 1.6461279444302545e-14,
  "max_scale_vs_served_rel": 3.650254899411344e-05
 },
 "all": {
  "compared": 60,
  "K_bit": 60,
  "served_plane_bit": 60,
  "unscaled_bit": 20,
  "metric_fixed_bit": 20,
  "max_K": 0.0,
  "max_unscaled_translation": 4.558679027077474e-15,
  "max_unscaled_rotation_deg": 2.4148365394514667e-06,
  "max_metric_fixed_translation_m": 1.6461279444302545e-14,
  "max_scale_vs_served_rel": 3.650254899411344e-05
 }
}
```
## Cost
```
{
 "ScanNet": {
  "A": {
   "n": 52,
   "mean": 7.320400156442282,
   "median": 7.41401654452784,
   "max": 8.202443944988772
  },
  "D": {
   "n": 52,
   "mean": 8.554272307981872,
   "median": 8.713747375528328,
   "max": 9.626749459013809
  },
  "ratio_of_means": 1.1685525552115792,
  "ratio_of_medians": 1.1753072471843615
 },
 "ScanNet++": {
  "A": {
   "n": 48,
   "mean": 7.321609238268138,
   "median": 7.177299943024991,
   "max": 9.18435568595305
  },
  "D": {
   "n": 48,
   "mean": 8.53942131392129,
   "median": 8.389744855492609,
   "max": 10.452071362000424
  },
  "ratio_of_means": 1.1663312034310662,
  "ratio_of_medians": 1.1689277196288683
 },
 "ARKit": {
  "A": {
   "n": 54,
   "mean": 4.283491873389317,
   "median": 4.273771750507876,
   "max": 4.7475544429617
  },
  "D": {
   "n": 54,
   "mean": 4.75831945516445,
   "median": 4.738748970004963,
   "max": 5.325630943989381
  },
  "ratio_of_means": 1.1108505854125563,
  "ratio_of_medians": 1.1087978597457457
 },
 "all": {
  "A": {
   "n": 154,
   "mean": 6.2558870956811194,
   "median": 6.98950713899103,
   "max": 9.18435568595305
  },
  "D": {
   "n": 154,
   "mean": 7.2185950237802565,
   "median": 8.183471565018408,
   "max": 10.452071362000424
  },
  "ratio_of_means": 1.1538883156577047,
  "ratio_of_medians": 1.170822405970063
 },
 "arm_wall_seconds": {
  "A1": 651.435884475708,
  "A2": 650.4084753990173,
  "D1": 740.6864717006683,
  "D2": 727.5625977516174
 },
 "rebuild_seconds": {
  "A1": [
   21.626153627003077,
   15.814474151993636,
   20.3403515110258,
   14.647552334005013,
   18.564561259001493,
   14.594956537010148,
   18.686752443027217
  ],
  "A2": [
   21.441654865979217,
   15.425843396980781,
   17.71937099500792,
   15.513812927005347,
   20.09025131200906,
   15.42568972700974,
   18.31612000701716
  ],
  "D1": [
   22.997480279009324,
   15.861870573018678,
   21.68700448796153,
   15.670973090047482,
   20.13590184302302,
   15.246515149017796,
   20.333649992011487
  ],
  "D2": [
   21.76924626500113,
   15.000010603049304,
   18.77594370103907,
   15.679854282992892,
   20.994542611995712,
   15.604492846003268,
   19.08984531200258
  ]
 },
 "peak_bytes": {
  "A1": 17110709760,
  "A2": 17110709760,
  "D1": 23007253504,
  "D2": 23007253504
 }
}
```
