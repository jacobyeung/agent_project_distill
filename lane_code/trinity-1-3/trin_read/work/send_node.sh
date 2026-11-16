# usage: bash send_node.sh NODE PATH...  (from trinity-1-3; one IB tar pipe to the same absolute path on NODE)
set -o pipefail
N=$1; shift; cd /scratch/jjyeung/orch_n30/trin_read
echo "start $(date -u +%FT%TZ) $N $*"
tar cf - "$@" | timeout 3600 ssh -o ConnectTimeout=20 $N.ib 'df -B1 --output=avail /scratch | tail -1; mkdir -p /scratch/jjyeung/orch_n30/trin_read && cd /scratch/jjyeung/orch_n30/trin_read && tar xf - && echo RECV_OK && df -B1 --output=avail /scratch | tail -1'
echo "rc=$? end $(date -u +%FT%TZ)"
