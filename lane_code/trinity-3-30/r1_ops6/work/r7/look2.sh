#!/bin/bash
set +x; set -uo pipefail; export TZ=UTC
O=/project/community/jjyeung/okh7; KH=$O/x_ee227714; R=$KH/runs/6ed2c7aa
date -u +%FT%TZ
ls -la --time-style=+%FT%T $R $R/inputs 2>&1 | grep -v "^total"
for f in $R/inputs/data_receipt.json $R/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json $R/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/prepared/s1_receipt.json; do [[ -f $f ]] && sha256sum $f || echo "ABSENT $f"; done
ls -la --time-style=+%FT%T $KH/o | grep -v "^total" | awk '{print $5,$6,$7}'
echo "== grep err/steps"
grep -n -i -E "c0|bridge|restor|donor|slot|0\.json|673bc60f|76bed248|c11b603f|a09ca55b|210b2534|store|resum|step 20[0-9]|data_receipt|binding|world" $KH/o/172660.err $KH/o/172660.steps $KH/o/172660.w.steps 2>/dev/null | grep -v cgroup | cut -c1-400 | tail -60
echo "== tail err (non-cgroup, non-NCCL warn)"
grep -n -v -E "cgroup|TORCH_NCCL_AVOID_RECORD_STREAMS" $KH/o/172660.err | tail -30 | cut -c1-400
