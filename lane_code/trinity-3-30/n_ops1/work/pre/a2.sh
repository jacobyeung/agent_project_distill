export TZ=UTC; date -u +%FT%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; K=/project/community/jjyeung/okh7/x_ee227714
cat $X/n/BUILD.json; echo; cat $X/n/job.sh; echo; cat $X/n/SHA256SUMS.txt | awk '{print $2}' | tr '\n' ' '; echo
ls -la $X/n/b $X/n/k | head -60
echo "==== l.py"; head -c 3000 $X/n/b/l.py
echo "==== x.py head"; head -c 4000 $X/n/b/x.py
echo "==== 172660 o"; ls -la $K/o | tail -30
echo "==== 172660.steps"; grep -v "_cgroup_procs_check\|unable to read" $K/o/172660.steps | cut -c1-300 | head -150
