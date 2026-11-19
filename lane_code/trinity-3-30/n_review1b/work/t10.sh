X=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24l3_back/out
filt(){ awk -v want="$2" '/^diff --git/{keep=index($0,want)>0} keep' "$1"; }
echo "##### HOST24LN3 files"; grep "^diff --git" $X/HOST24LN3.patch
echo "##### r1_handover"; filt $X/HOST24LN3.patch student_pilot/r1_handover.py
echo "##### HOST24L3 files"; grep "^diff --git" $X/HOST24L3.patch
echo "##### entry (24l3)"; filt $X/HOST24L3.patch launch_r1/entry.py
echo "##### production_proof (24ln)"; filt $X/HOST24LN3.patch launch_r1/production_proof.py
