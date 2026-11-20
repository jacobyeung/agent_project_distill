W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/w24c
awk '/^--- a\/tests|^--- \/dev\/null/{exit} {print}' $W/work/x24l4c_back/out/HOST24L4.patch
echo ====; cat $C/out/BUILD24M4C_REPORT.md
