cd /scratch/jjyeung/orch_n30/fb_pack/donor3 && ls
grep -E 'student_pilot/(point_depth_head|decoupled_v|carrier_c1|carrier_c1_decode)\.py' out/TREE_FILES.sha256
for d in tree src base work; do [ -d $d ] && ls $d | head; done
