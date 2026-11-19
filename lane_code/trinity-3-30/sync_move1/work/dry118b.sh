set -u
cd /scratch/jjyeung/orch_n30 || exit 5
df -h /scratch | tail -1
for v in new2; do
  echo "== $v"; LCS_ROBUST_SYNC=1 timeout 600 nice -n 10 python3 -I -s -B /dev/stdin trinity-1-18 < /tmp/sm1/filter_$v.py 2>&1 >/dev/null | cut -c1-400
done
