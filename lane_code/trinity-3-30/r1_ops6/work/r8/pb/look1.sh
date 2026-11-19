export TZ=UTC; O=/project/community/jjyeung/okh7
ls -la $O/r/673bc60f/ $O/r/6ed2c7aa/ 2>&1 | head -30
for f in $O/r/673bc60f/A.json $O/r/673bc60f/B.json $O/r/6ed2c7aa/A.json $O/r/6ed2c7aa/B.json; do [ -f $f ] && { echo "== $f"; head -c 1500 $f; echo; }; done
ls $O | head -40
ls $O/x_*/o/ 2>/dev/null | grep -E 'gcs_673bc60f|gcs_6ed2c7aa' | head
for d in $O/x_*; do ls -d $d/runs/673bc60f 2>/dev/null; done
sinfo -h -p preempt -o '%P %a %l %D %c %m %G' 2>&1 | head -3; squeue -h -p preempt -t PD -o '%i' | wc -l
cat $O/r/6ed2c7aa/../../x_ee227714/o/172660.w.steps 2>/dev/null | tail -5
