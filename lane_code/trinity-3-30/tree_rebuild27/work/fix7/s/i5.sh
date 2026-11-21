W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
ls $W/w28jn7 | head; f=$(ls $W/w28jn7/*.sh $W/w28jn7/*/jn7.sh 2>/dev/null | head -3); echo "$f"; for x in $f; do echo "== $x"; grep -n "9e809db4\|22c714e1\|seal\|kit_sha\|X/n\|sess" $x | head -20; done
