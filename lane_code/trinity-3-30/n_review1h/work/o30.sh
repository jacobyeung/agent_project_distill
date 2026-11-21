X=/project/community/jjyeung/okh7/x_22c714e1; TZ=UTC date +%TZ; hostname -s; df -h /project/community < /dev/null | tail -1
ls -la $X < /dev/null | head -60
echo "== wrappers"; for f in $X/jn3.sh $X/jn2.sh $X/jn.sh $X/jd7.sh; do [ -f $f ] && sha256sum $f < /dev/null; done
echo "== kit seals on X"; for k in q n n_go qd qp_11386117; do [ -f $X/$k/SHA256SUMS.txt ] && echo "$k $(sha256sum < $X/$k/SHA256SUMS.txt | cut -c1-64)"; done
echo "== slurm.conf proctrack"; grep -i -h 'ProctrackType\|TaskPlugin\|KillWait\|UnkillableStep' /etc/slurm/slurm.conf /etc/slurm/cgroup.conf < /dev/null 2>&1 | head
echo "== 173964"; ls -la $X/o/173964 < /dev/null 2>&1 | head -30; ls -la $X/o/173964/live < /dev/null 2>&1 | head -40; ls -la $X/o/173964/j7 < /dev/null 2>&1 | head -40
tail -c 1500 $X/o/173964/live/j2.log < /dev/null 2>/dev/null
