S=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/sel24; wc -c $S/SELECTION_TABLE.md $S/PROVENANCE.md $S/orchard/*; grep -n -i -B2 -A8 "UNATTRIBUTED" $S/SELECTION_TABLE.md | cut -c1-600 | head -90
