X=/project/community/jjyeung/okh7/x_22c714e1; J=173496
wc -l $X/j/a15_cot_ap24d9b8e2_$J.err $X/j/a15_cot_ap24d9b8e2_$J.log
grep -v "_cgroup_procs_check\|unable to read\|archive members verified\|staged$\| joined \|verified [0-9]" $X/j/a15_cot_ap24d9b8e2_$J.err | head -60 | cut -c1-300
echo ==== LOGHEAD; grep -v "archive members verified\|staged$\| joined " $X/j/a15_cot_ap24d9b8e2_$J.log | head -40 | cut -c1-300
