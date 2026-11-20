cd /scratch/jjyeung/orch_n30/fb_pack/donor3 || exit 1
for d in base apply_base; do for f in point_depth_head.py decoupled_v.py; do p=$d/student_pilot/$f; [ -f $p ] && sha256sum $p; done; done
echo ==PDH; cat base/student_pilot/point_depth_head.py 2>/dev/null || cat apply_base/student_pilot/point_depth_head.py
echo ==DV; cat base/student_pilot/decoupled_v.py 2>/dev/null || cat apply_base/student_pilot/decoupled_v.py
