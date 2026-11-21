X=/project/community/jjyeung/okh7/x_22c714e1; TZ=UTC date +%TZ; cd $X/o/174134 < /dev/null
grep -n -i "target_filter\|target-filter\|division\|streams\|vqa\|pointing" q.log < /dev/null | cut -c1-260 | tail -25
echo == steps; tail -15 q.steps < /dev/null | cut -c1-200
