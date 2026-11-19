"""Paired non-inferiority sizing for the K1 pointing test (assumed discordant-pair rate p_d).

Run: bash work/run.sh power
n = (z_0.95 + z_0.80)^2 * p_d / margin^2; paired SE of the accuracy difference = sqrt(p_d / n).
"""
import json
from math import sqrt
from statistics import NormalDist

z = NormalDist().inv_cdf
k = (z(0.95) + z(0.80)) ** 2
out = {}
for p_d in (0.05, 0.10, 0.15):
    out[p_d] = dict(n_for_margin_5pt=round(k * p_d / 0.05 ** 2), n_for_margin_3pt=round(k * p_d / 0.03 ** 2),
                    ci95_halfwidth_pts_at_320=round(100 * 1.96 * sqrt(p_d / 320), 2))
print(json.dumps(out, indent=1))
