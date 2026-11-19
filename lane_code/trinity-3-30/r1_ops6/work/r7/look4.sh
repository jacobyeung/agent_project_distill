#!/bin/bash
set +x; set -uo pipefail; export TZ=UTC
O=/project/community/jjyeung/okh7; KH=$O/x_ee227714; R=$KH/runs/6ed2c7aa
cat -n $KH/job.sh
echo "== d"; ls -la --time-style=+%FT%T $R/d $R/d/* 2>&1 | head -40
for f in $R/d/0.json $R/d/c.json; do echo "== $f"; sha256sum $f; head -c 1500 $f; echo; done
du -sb $R/d 2>&1 | tail -1
