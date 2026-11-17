D=/project/community/jjyeung/okh7/x_f5c353f7/runs/359fcc3c/inputs
for d in $D $D/*/ $D/*/*/; do echo "== $d"; ls -la $d | head -20; done 2>&1 | head -80
for f in $D/*/*.json $D/*/*/*.json; do test -f $f && echo "$f $(stat -c %s $f) $(sha256sum < $f | cut -c1-16) v314=$(grep -o v314_execution_disagreement $f | wc -l) ord=$(grep -o object_rel_direction_hard $f | wc -l)"; done 2>/dev/null
