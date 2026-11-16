# Runs on trinity-1-3: one tar pipe over IB of the staged lane tree to trinity-1-18 (same absolute path). Arg: list of paths relative to the lane folder.
set -o pipefail
cd /scratch/jjyeung/orch_n30/trin_read
echo "start $(date -u +%FT%TZ) $*"
tar cf - "$@" | timeout 3600 ssh -o ConnectTimeout=20 trinity-1-18.ib 'df -B1 --output=avail /scratch | tail -1; mkdir -p /scratch/jjyeung/orch_n30/trin_read && cd /scratch/jjyeung/orch_n30/trin_read && tar xf - && echo RECV_OK && df -B1 --output=avail /scratch | tail -1'
echo "rc=$? end $(date -u +%FT%TZ)"
