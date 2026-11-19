#!/bin/bash
set +x; set -uo pipefail; export TZ=UTC
O=/project/community/jjyeung/okh7; KH=$O/x_ee227714; R=$KH/runs/6ed2c7aa; KA=$O/x_69d2930d; RA=$KA/runs/673bc60f
date -u +%FT%TZ
echo "== C' run"; ls -la --time-style=+%FT%T $R $R/inputs 2>&1 | tail -n +1
P=$(ls -d $R/inputs/prepare_* 2>/dev/null | head -1); echo "P=$P"; ls -la --time-style=+%FT%T $P 2>&1 | head -40
echo "== KH/o"; ls -la --time-style=+%FT%T $KH/o 2>&1 | tail -25
echo "== A run"; ls -la --time-style=+%FT%T $RA $RA/m200 $RA/inputs 2>&1 | head -40
echo "== A m200 artifact"; wc -c $RA/m200/artifact.json; sha256sum $RA/m200/artifact.json
