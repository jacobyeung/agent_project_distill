#!/bin/bash
set +x; set -uo pipefail; export TZ=UTC
O=/project/community/jjyeung/okh7
echo "== A err fast path"; grep -n -c "fast path is not available" $O/x_69d2930d/o/171377.err; grep -n "fast path is not available" $O/x_69d2930d/o/171377.err | head -2 | cut -c1-120
echo "== A err first non-warning lines after NCCL"; grep -n -v -E "cgroup|TORCH_NCCL_AVOID" $O/x_69d2930d/o/171377.err | head -40 | cut -c1-300
echo "== C err"; grep -n -v -E "cgroup|TORCH_NCCL_AVOID" $O/x_ee227714/o/172660.err | tail -20 | cut -c1-300
TZ=UTC scontrol show job 172660 | grep -E "StdOut|StdErr|WorkDir"
