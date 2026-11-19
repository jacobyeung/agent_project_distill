export TZ=UTC; P=/project/community/jjyeung/okh7/x_ee227714
ls $P | head -30 | tr '\n' ' '; echo
for d in $P/j $P/logs $P/o; do ls -t $d 2>/dev/null | head -3 | sed "s#^#$d/#"; done
f=$(ls -t $P/j/*.out 2>/dev/null | tail -n +1 | head -1); echo F=$f; test -n "$f" && grep -m3 -i "H100\|NVIDIA\|total_memory\|GiB" $f | cut -c1-200
grep -m3 -ih "NVIDIA H100\|H100 80GB HBM3\|NVIDIA A100" $P/j/*.out 2>/dev/null | cut -c1-200
