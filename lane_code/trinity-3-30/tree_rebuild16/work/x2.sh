J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l; R=/scratch/jjyeung/orch_n30/tr15_rev24l3; tail -c +2900 $R/VERDICT.md; echo; echo =====
cd $J/work/tree_r1; f=$(grep -rl "def validate_removals" --include=*.py . | head -3); echo $f; for x in $f; do n=$(grep -n "def validate_removals" $x | cut -d: -f1); sed -n "$((n-5)),$((n+45))p" $x; grep -n "REMOVAL_ORDER\s*=" -A16 $x | head -30; grep -n "NAMING_REMOVE\s*=" $x; done
grep -rn "validate_removals(" --include=*.py . | grep -v "def " | head
