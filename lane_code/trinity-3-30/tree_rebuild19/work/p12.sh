W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; cd $W/w24j; ls; ls work | head -30; T=$(ls -d work/*/tree_r1 work/tree_r1 2>/dev/null | head -3); echo "T=$T"
for t in $T; do nice -n 10 grep -rn --include=*.py "processor_resolution_pin_missing\|def processor_for_receipt\|def layout" $t | head -10; done
nice -n 10 grep -n "model_pin\|def regenerate" -A6 out/kit_qd/b/rg.py | head -50
