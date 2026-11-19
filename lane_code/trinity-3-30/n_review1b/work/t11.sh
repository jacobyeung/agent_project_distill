X=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24l3_back/out
head -c 600 $X/HOST24LN3.patch; echo; grep -n "^+++\|^---\|^Index\|^diff" $X/HOST24LN3.patch | head; grep -n "^+++\|^---\|^diff" $X/HOST24L3.patch | head
