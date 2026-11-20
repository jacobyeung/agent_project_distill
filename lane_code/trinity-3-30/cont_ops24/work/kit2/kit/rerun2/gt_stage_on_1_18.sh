#!/bin/bash
set -euo pipefail
# Run once on trinity-1-18 after the transfer owner authorizes IO and confirms disk space.
# Put gt_available.txt on 1-18 by the lane's existing session. Do not relay from another host.
test "$(hostname -s)" = trinity-1-18
LIST=${1:?absolute path to gt_available.txt on trinity-1-18}
tar -cf - -C /scratch/jjyeung/orch_cd/dose_pool/out -T "$LIST" |
  ssh -o ConnectTimeout=20 trinity-2-28.ib \
    'mkdir -p /scratch/jjyeung/orch_n30/grd_funnel1/work/gt_stage && tar -xf - -C /scratch/jjyeung/orch_n30/grd_funnel1/work/gt_stage'
